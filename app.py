from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash, g
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from pathlib import Path
import sqlite3, os, secrets, re
from datetime import timedelta

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / 'data' / 'bugatti_demo.sqlite3'
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('BUGATTI_SECRET_KEY', 'replace-this-development-key-before-deployment')
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = os.environ.get('FLASK_HTTPS', '0') == '1'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=30)

PRODUCTS = [
 {'id':1,'name':'Bugatti Heritage Cap','category':'Clothing','price':85,'description':'A refined cap inspired by the marque’s motorsport heritage.','image':'https://images.unsplash.com/photo-1588850561407-ed78c282e89b?auto=format&fit=crop&w=900&q=85'},
 {'id':2,'name':'Tourbillon Model Car','category':'Model Cars','price':145,'description':'A collectible scale model for automotive enthusiasts.','image':'https://media.lider.media/files/441129-bugatti-tourbillon.jpg'},
 {'id':3,'name':'Signature Jacket','category':'Clothing','price':320,'description':'A premium motorsport-inspired outer layer.','image':'https://images.unsplash.com/photo-1551028719-00167b16eac5?auto=format&fit=crop&w=900&q=85'},
 {'id':4,'name':'Carbon Keyring','category':'Accessories','price':45,'description':'A compact accessory with a technical finish.','image':'https://images.unsplash.com/photo-1612817288484-6f916006741a?auto=format&fit=crop&w=900&q=85'},
 {'id':5,'name':'Grand Tour Travel Bag','category':'Exclusive Lifestyle','price':480,'description':'A travel essential designed for refined journeys.','image':'https://images.unsplash.com/photo-1553062407-98eeb64c6a62?auto=format&fit=crop&w=900&q=85'},
 {'id':6,'name':'Technical Wireless Headphones','category':'Tech','price':210,'description':'A fictional demonstration product for the store prototype.','image':'https://images.unsplash.com/photo-1505740420928-5e560c06d30e?auto=format&fit=crop&w=900&q=85'},
 {'id':7,'name':'Classic Roadster Model','category':'Model Cars','price':125,'description':'A miniature tribute to classic automotive design.','image':'https://hips.hearstapps.com/hmg-prod/amv-prod-cad-assets/images/05q4/267357/2006-bugatti-veyron-164-road-test-review-car-and-driver-photo-9031-s-original.jpg'},
 {'id':8,'name':'Leather Card Holder','category':'Accessories','price':95,'description':'Minimal everyday carry in a timeless silhouette.','image':'https://images.unsplash.com/photo-1627123424574-724758594e93?auto=format&fit=crop&w=900&q=85'},
]
MODELS = [
 {'slug':'tourbillon','name':'Tourbillon','eyebrow':'THE NEXT CHAPTER','desc':'A new era of performance, craftsmanship and timeless mechanical design.','image':'https://media.lider.media/files/441129-bugatti-tourbillon.jpg','type':'Current model','collection':'current contemporary','year':'2024','story':'The Tourbillon introduces a new chapter for Bugatti, combining a naturally aspirated V16 engine with electrified power and a cabin inspired by fine watchmaking. Its design draws on the marque’s historic centreline and horseshoe grille.'},
 {'slug':'w16-mistral','name':'W16 Mistral','eyebrow':'THE ROADSTER','desc':'The open-air celebration of Bugatti’s W16 era.','image':'https://bugatti-newsroom.imgix.net/fe86ea75-1b82-44d8-abcd-734c8d5743f7/13%20BUGATTI_W16-Mistral_UAE-launch?auto=format%2Ccompress&cs=srgb&w=1600','type':'Current model','collection':'current contemporary','year':'2022','story':'The W16 Mistral is an open-top roadster created as a farewell to Bugatti’s celebrated W16 powertrain. Its design blends an open cockpit with carefully managed airflow and the marque’s signature styling.'},
 {'slug':'bolide','name':'Bolide','eyebrow':'TRACK FOCUSED','desc':'A radical track-only expression of lightweight engineering.','image':'https://www.motorlegend.com/modules/breve/photos/src/bugatti-bolide-22210-1-P.jpg','type':'Track hypercar','collection':'current contemporary','year':'2020 concept / production programme','story':'The Bolide is a track-focused machine developed around extreme aerodynamic ambition, low weight and the Bugatti W16. It is not intended as a conventional road car.'},
 {'slug':'chiron','name':'Chiron','eyebrow':'A MODERN ICON','desc':'A landmark in the story of high-performance grand touring.','image':'https://bugatti-newsroom.imgix.net/d822dada-b040-4d03-9df9-b77e7abc71ce/01_gims-2017_chiron?auto=format%2Ccompress&cs=srgb&w=1600','type':'Contemporary icon','collection':'contemporary','year':'2016','story':'Presented in 2016, the Chiron advanced Bugatti’s modern hyper sports car philosophy with a quad-turbocharged 8.0-litre W16 and a body shaped around both speed and elegance. Production concluded with a final, individually specified example in 2024.'},
 {'slug':'divo','name':'Divo','eyebrow':'AGILITY REDEFINED','desc':'A limited-series Bugatti shaped around agility and individuality.','image':'https://bugatti-newsroom.imgix.net/8b32a1e9ad0f4a29b7e088aa6df38bf3/07_bugatti-divo_side_web.jpg?auto=format%2Ccompress&cs=srgb&w=1600','type':'Limited series','collection':'contemporary','year':'2018','story':'The Divo revisited the Chiron’s foundations with a focus on lateral performance and a more assertive aerodynamic character. Its limited production made it a highly individual expression of Bugatti coachbuilding.'},
 {'slug':'centodieci','name':'Centodieci','eyebrow':'A TRIBUTE','desc':'A modern homage to the iconic EB110.','image':'https://bugatti-newsroom.imgix.net/99970f77-d8e6-4d42-b1f2-bfc2b7cb7466/01%20BUGATTI_Last-CENTODIECI?auto=format%2Ccompress&cs=srgb&w=1600','type':'Limited series','collection':'contemporary','year':'2019','story':'The Centodieci takes inspiration from the EB110 and reinterprets its visual themes through a modern limited-series hyper sports car. Its name means “110” in Italian, acknowledging the heritage behind the project.'},
 {'slug':'veyron','name':'Veyron 16.4','eyebrow':'A NEW BENCHMARK','desc':'The car that redefined the modern hyper sports car.','image':'https://hips.hearstapps.com/hmg-prod/amv-prod-cad-assets/images/05q4/267357/2006-bugatti-veyron-164-road-test-review-car-and-driver-photo-9031-s-original.jpg','type':'Classic icon','collection':'classic','year':'2005','story':'The Veyron brought together extraordinary speed, refinement and all-weather usability in a production car. Its 1,001 PS output and quad-turbocharged W16 became defining milestones in modern automotive engineering.'},
 {'slug':'eb110','name':'EB110','eyebrow':'THE REVIVAL','desc':'A landmark supercar from Bugatti’s early-1990s revival.','image':'https://bugatti-newsroom.imgix.net/68b8152d6e65c2af93b45dba/01-2509-bugatti-eb110-certification.jpg?auto=format%2Ccompress&cs=srgb&w=1600','type':'Classic icon','collection':'classic','year':'1991','story':'Unveiled in 1991, the EB110 marked a dramatic revival of the Bugatti name. Its carbon-fibre chassis, four turbochargers and all-wheel drive made it technically ambitious for its era.'},
]

SCHEMA = '''
CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, email TEXT UNIQUE NOT NULL, password_hash TEXT NOT NULL, is_admin INTEGER NOT NULL DEFAULT 0, created_at TEXT DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS orders(id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, order_number TEXT UNIQUE NOT NULL, customer_name TEXT NOT NULL, email TEXT NOT NULL, address TEXT NOT NULL, items_json TEXT NOT NULL, total REAL NOT NULL, status TEXT NOT NULL DEFAULT 'Demo order', created_at TEXT DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY(user_id) REFERENCES users(id));
CREATE TABLE IF NOT EXISTS form_submissions(id INTEGER PRIMARY KEY AUTOINCREMENT, kind TEXT NOT NULL, name TEXT, email TEXT, subject TEXT, message TEXT, details_json TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS configurations(id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, name TEXT NOT NULL, colour TEXT NOT NULL, interior TEXT NOT NULL, wheels TEXT NOT NULL, finish TEXT NOT NULL, created_at TEXT DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY(user_id) REFERENCES users(id));
CREATE TABLE IF NOT EXISTS wishlist(user_id INTEGER NOT NULL, model_slug TEXT NOT NULL, created_at TEXT DEFAULT CURRENT_TIMESTAMP, PRIMARY KEY(user_id, model_slug), FOREIGN KEY(user_id) REFERENCES users(id));
CREATE TABLE IF NOT EXISTS cart_items(user_id INTEGER NOT NULL, product_id INTEGER NOT NULL, quantity INTEGER NOT NULL DEFAULT 1, updated_at TEXT DEFAULT CURRENT_TIMESTAMP, PRIMARY KEY(user_id, product_id), FOREIGN KEY(user_id) REFERENCES users(id));
'''

def get_db():
    if 'db' not in g:
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
        g.db.execute('PRAGMA foreign_keys=ON')
    return g.db

@app.teardown_appcontext
def close_db(_=None):
    db = g.pop('db', None)
    if db is not None: db.close()

def init_db():
    with sqlite3.connect(DB_PATH) as db:
        db.executescript(SCHEMA)
        # Optional seeded admin account: set ADMIN_EMAIL and ADMIN_PASSWORD before first run.
        admin_email = os.environ.get('ADMIN_EMAIL', '').strip().lower()
        admin_password = os.environ.get('ADMIN_PASSWORD', '')
        if admin_email and admin_password and not db.execute('SELECT id FROM users WHERE email=?', (admin_email,)).fetchone():
            db.execute('INSERT INTO users(name,email,password_hash,is_admin) VALUES(?,?,?,1)', ('Project Admin', admin_email, generate_password_hash(admin_password)))

with app.app_context(): init_db()

def login_required(fn):
    @wraps(fn)
    def wrapped(*args, **kwargs):
        if not session.get('user_id'):
            flash('Please log in to use that feature.', 'notice')
            return redirect(url_for('login', next=request.path))
        return fn(*args, **kwargs)
    return wrapped

def admin_required(fn):
    @wraps(fn)
    def wrapped(*args, **kwargs):
        if not session.get('is_admin'):
            flash('Admin access is required.', 'notice')
            return redirect(url_for('home'))
        return fn(*args, **kwargs)
    return wrapped

@app.context_processor
def inject_globals():
    count = sum(int(v) for v in session.get('cart', {}).values())
    if session.get('user_id'):
        try:
            row = get_db().execute('SELECT COALESCE(SUM(quantity),0) AS n FROM cart_items WHERE user_id=?', (session['user_id'],)).fetchone()
            count = int(row['n'])
        except sqlite3.Error:
            pass
    return {'current_user': session.get('user_name'), 'is_admin': session.get('is_admin', False), 'cart_count': count}

@app.get('/')
def home(): return render_template('home.html', models=MODELS)
@app.get('/models')
def models():
    collection = request.args.get('collection', 'all').lower()
    if collection == 'current':
        visible = [m for m in MODELS if 'current' in m['collection']]
        title, subtitle = 'Current models', 'The latest expression of Bugatti engineering.'
    elif collection == 'contemporary':
        visible = [m for m in MODELS if m['collection'] == 'contemporary' or 'contemporary' in m['collection']]
        title, subtitle = 'Contemporary icons', 'Modern creations that have shaped a new era.'
    elif collection == 'classic':
        visible = [m for m in MODELS if m['collection'] == 'classic']
        title, subtitle = 'Classic icons', 'Landmark cars from Bugatti’s modern heritage.'
    else:
        visible = MODELS
        title, subtitle = 'Every model. A world of its own.', 'Discover icons defined by their own character.'
    return render_template('models.html', models=visible, collection=collection, collection_title=title, collection_subtitle=subtitle)
@app.get('/models/<slug>')
def model_detail(slug):
    model = next((m for m in MODELS if m['slug']==slug), None)
    if not model: return render_template('404.html'), 404
    return render_template('model_detail.html', model=model, saved=bool(session.get('user_id') and get_db().execute('SELECT 1 FROM wishlist WHERE user_id=? AND model_slug=?',(session['user_id'],slug)).fetchone()))
@app.get('/history')
def history():
    sections = [
      ('1909 · A vision begins','Ettore Bugatti founded his automobile company in Molsheim, then in the German Empire and now in France’s Alsace region. From the beginning, the marque brought together engineering, artistic proportion and meticulous workmanship.'),
      ('1920s · Racing and innovation','Bugatti cars became celebrated on circuits and road courses. The Type 35 helped establish the marque’s motorsport reputation, while light construction and carefully developed engineering supported its success.'),
      ('1930s · Jean Bugatti and the Atlantic','Ettore’s son Jean brought a distinctive design sensibility to the company. The Type 57 family and the sculptural Type 57 SC Atlantic remain enduring examples of coachbuilt automotive artistry.'),
      ('1947 · A chapter closes','Ettore Bugatti died in 1947. The original company faced changing circumstances after the war, but the designs and ideas created in Molsheim continued to influence automotive history.'),
      ('1991 · The EB110 era','The Bugatti name returned to the supercar world with the EB110, a technically ambitious car featuring a carbon-fibre chassis, four turbochargers and all-wheel drive.'),
      ('2005 · The Veyron changes expectations','The Veyron brought together immense power and high-speed capability with a level of comfort and finish expected of a grand touring car. It helped define the modern hyper sports car.'),
      ('2016 · The Chiron generation','The Chiron carried the modern Bugatti story forward with a quad-turbocharged W16 and a carefully balanced combination of performance, design and craftsmanship.'),
      ('2024 onward · A new era','The Tourbillon signals a new technical chapter, pairing a naturally aspirated V16 with electrification and a mechanical instrument cluster inspired by haute horlogerie.'),
      ('The Bugatti approach','Across eras, the marque has pursued a balance of technical ambition and beauty. Proportion, materials, hand-finished details and a recognisable design language are central to its identity.'),
      ('Molsheim · Craftsmanship today','The Atelier remains central to the marque’s story. Each car combines advanced engineering with specialist assembly and individual specification, with personalisation offered through the Sur Mesure programme.')
    ]
    return render_template('editorial.html', page_title='La Maison Bugatti · History', eyebrow='SINCE 1909 · MOLSHEIM', hero_title='A history shaped by ambition.', intro='More than a century of engineering, competition, design and individual craftsmanship.', image='https://bugatti-newsroom.imgix.net/d822dada-b040-4d03-9df9-b77e7abc71ce/01_gims-2017_chiron?auto=format%2Ccompress&cs=srgb&w=1800', sections=sections)
@app.get('/sur-mesure')
def sur_mesure(): return render_template('editorial.html', page_title='Bugatti Sur Mesure', eyebrow='PERSONAL EXPRESSION', hero_title='A world of your own', intro='A bespoke journey where materials, colours and details express individual vision.', image='https://bugatti-newsroom.imgix.net/fe86ea75-1b82-44d8-abcd-734c8d5743f7/13%20BUGATTI_W16-Mistral_UAE-launch?auto=format%2Ccompress&cs=srgb&w=1600', sections=[('Colour and material','Explore combinations that make every detail personal.'),('Craftsmanship','A considered approach to finish, texture and form.'),('Begin your configuration','Create a demonstration configuration for this project.')])
@app.get('/live')
def live(): return render_template('live.html')
@app.get('/careers')
def careers(): return render_template('form_page.html', page_title='Careers', eyebrow='JOIN THE JOURNEY', intro='Submit a demonstration careers enquiry. Do not upload sensitive personal documents.', kind='careers', fields=[('name','Full name','text',True),('email','Email address','email',True),('role','Area of interest','text',True),('message','Short introduction','textarea',True)])
@app.get('/store')
def store():
    categories = sorted(set(p['category'] for p in PRODUCTS))
    return render_template('store.html', products=PRODUCTS, categories=categories)
@app.get('/configurator')
def configurator(): return render_template('configurator.html', models=MODELS)
@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        name=request.form.get('name','').strip(); email=request.form.get('email','').strip().lower(); password=request.form.get('password',''); confirm=request.form.get('confirm_password','')
        if len(name)<2 or not re.match(r'^[^@\s]+@[^@\s]+\.[^@\s]+$',email): flash('Enter a valid name and email address.', 'error')
        elif len(password)<10 or not re.search(r'[A-Za-z]',password) or not re.search(r'\d',password): flash('Use at least 10 characters including a letter and a number.', 'error')
        elif password != confirm: flash('Passwords do not match.', 'error')
        else:
            try:
                cur=get_db().execute('INSERT INTO users(name,email,password_hash) VALUES(?,?,?)',(name,email,generate_password_hash(password)))
                get_db().commit(); session.permanent=True; session.update(user_id=cur.lastrowid,user_name=name,is_admin=False); flash('Account created successfully.', 'success'); return redirect(url_for('dashboard'))
            except sqlite3.IntegrityError: flash('An account with that email already exists.', 'error')
    return render_template('auth.html', mode='register')
@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        email=request.form.get('email','').strip().lower(); password=request.form.get('password','')
        user=get_db().execute('SELECT * FROM users WHERE email=?',(email,)).fetchone()
        if user and check_password_hash(user['password_hash'],password):
            anonymous_cart = session.get('cart', {}).copy()
            session.clear(); session.permanent = True; session.update(user_id=user['id'],user_name=user['name'],is_admin=bool(user['is_admin']))
            for pid, qty in anonymous_cart.items():
                get_db().execute('INSERT INTO cart_items(user_id,product_id,quantity) VALUES(?,?,?) ON CONFLICT(user_id,product_id) DO UPDATE SET quantity=MIN(20,quantity+excluded.quantity), updated_at=CURRENT_TIMESTAMP', (user['id'], int(pid), min(20, int(qty))))
            get_db().commit()
            flash('Welcome back.', 'success'); target=request.args.get('next','')
            return redirect(target if target.startswith('/') and not target.startswith('//') else url_for('dashboard'))
        flash('Email or password was not recognised.', 'error')
    return render_template('auth.html', mode='login')
@app.get('/logout')
def logout(): session.clear(); flash('You have been logged out.', 'notice'); return redirect(url_for('home'))
@app.get('/dashboard')
@login_required
def dashboard():
    db=get_db(); orders=db.execute('SELECT * FROM orders WHERE user_id=? ORDER BY id DESC',(session['user_id'],)).fetchall(); configs=db.execute('SELECT * FROM configurations WHERE user_id=? ORDER BY id DESC',(session['user_id'],)).fetchall(); wishes=db.execute('SELECT model_slug FROM wishlist WHERE user_id=?',(session['user_id'],)).fetchall()
    return render_template('dashboard.html',orders=orders,configs=configs,wishes=[w['model_slug'] for w in wishes])
@app.route('/contact', methods=['GET','POST'])
def contact():
    if request.method=='POST':
        name=request.form.get('name','').strip(); email=request.form.get('email','').strip(); subject=request.form.get('subject','').strip(); message=request.form.get('message','').strip()
        if not name or not email or not message: flash('Please complete all required fields.', 'error')
        else:
            get_db().execute('INSERT INTO form_submissions(kind,name,email,subject,message) VALUES(?,?,?,?,?)',('contact',name,email,subject,message)); get_db().commit(); flash('Your demonstration enquiry has been saved.', 'success'); return redirect(url_for('contact'))
    return render_template('form_page.html',page_title='Contact & Enquiries',eyebrow='WE ARE HERE TO HELP',intro='Send a demonstration enquiry to the project website.',kind='contact',fields=[('name','Full name','text',True),('email','Email address','email',True),('subject','Subject','text',False),('message','Message','textarea',True)])
@app.route('/dealer-finder', methods=['GET','POST'])
def dealer_finder():
    if request.method=='POST':
        save_submission('dealer',request.form); flash('Your dealer enquiry has been saved as a demonstration submission.', 'success'); return redirect(url_for('dealer_finder'))
    return render_template('form_page.html',page_title='Dealer Finder',eyebrow='FIND A POINT OF CONTACT',intro='This academic demo collects a preferred region and contact request; it does not locate or contact real dealers.',kind='dealer',fields=[('name','Full name','text',True),('email','Email address','email',True),('region','Preferred city or region','text',True),('message','What would you like to know?','textarea',False)])
@app.route('/service', methods=['GET','POST'])
def service():
    if request.method=='POST':
        save_submission('service',request.form); flash('Your customer-service request has been saved for the demonstration.', 'success'); return redirect(url_for('service'))
    return render_template('form_page.html',page_title='Customer Service',eyebrow='OWNERSHIP SUPPORT',intro='Send a general demonstration support request. Do not include passwords or financial information.',kind='service',fields=[('name','Full name','text',True),('email','Email address','email',True),('topic','Request type','text',True),('message','Message','textarea',True)])
@app.route('/newsletter', methods=['POST'])
def newsletter():
    email=request.form.get('email','').strip().lower()
    if not re.match(r'^[^@\s]+@[^@\s]+\.[^@\s]+$',email): flash('Enter a valid email address.', 'error')
    else:
        save_submission('newsletter',{'email':email,'name':'','message':'Newsletter subscription request'}); flash('Newsletter preference saved for this demonstration.', 'success')
    return redirect(request.referrer if request.referrer and request.referrer.startswith('/') else url_for('home'))
@app.route('/forgot-password', methods=['GET','POST'])
def forgot_password():
    if request.method=='POST':
        email=request.form.get('email','').strip().lower()
        # Deliberately do not reveal whether the account exists or send real email.
        save_submission('forgot-password',{'email':email,'message':'Password reset requested (demo; no email sent)'})
        flash('If this were a live service, reset instructions would be sent if the account exists. This demo does not send email.', 'notice'); return redirect(url_for('login'))
    return render_template('auth.html',mode='forgot')

def save_submission(kind, form):
    name=form.get('name','').strip(); email=form.get('email','').strip().lower(); subject=form.get('subject') or form.get('topic') or form.get('role') or form.get('region') or ''; message=form.get('message','').strip()
    get_db().execute('INSERT INTO form_submissions(kind,name,email,subject,message,details_json) VALUES(?,?,?,?,?,?)',(kind,name,email,subject,message, '{}')); get_db().commit()

@app.get('/api/products')
def api_products():
    q=request.args.get('q','').strip().lower(); cat=request.args.get('category','').strip()
    found=[p for p in PRODUCTS if (not q or q in (p['name']+' '+p['category']+' '+p['description']).lower()) and (not cat or cat=='All' or p['category']==cat)]
    return jsonify({'products':found,'categories':['All']+sorted(set(p['category'] for p in PRODUCTS))})
@app.get('/api/search')
def api_search():
    q=request.args.get('q','').strip().lower()
    results=[]
    if q:
        for m in MODELS:
            if q in (m['name']+' '+m['desc']+' '+m['type']).lower(): results.append({'title':m['name'],'type':'Car model','url':url_for('model_detail',slug=m['slug'])})
        for p in PRODUCTS:
            if q in (p['name']+' '+p['category']+' '+p['description']).lower(): results.append({'title':p['name'],'type':'Store product','url':url_for('store')+'?q='+p['name']})
        for title, path, keywords in [('La Maison Bugatti','/history','history company heritage maison careers'),('Bugatti Sur Mesure','/sur-mesure','sur mesure customization bespoke'),('Bugatti Live','/live','live gallery media video'),('Careers','/careers','careers jobs work')]:
            if q in (title+' '+keywords).lower(): results.append({'title':title,'type':'Page','url':path})
    return jsonify({'results':results[:15]})
@app.route('/api/cart', methods=['GET','POST','DELETE'])
def api_cart():
    db=get_db(); uid=session.get('user_id')
    if uid:
        cart={str(r['product_id']):int(r['quantity']) for r in db.execute('SELECT product_id,quantity FROM cart_items WHERE user_id=?',(uid,)).fetchall()}
    else:
        cart=session.get('cart',{})
    if request.method=='POST':
        data=request.get_json(silent=True) or {}; pid=str(data.get('product_id',''))
        try: qty=int(data.get('quantity',1))
        except (ValueError,TypeError): return jsonify({'error':'Invalid quantity'}),400
        if not any(str(p['id'])==pid for p in PRODUCTS): return jsonify({'error':'Product not found'}),404
        if qty<1 or qty>20: return jsonify({'error':'Quantity must be between 1 and 20'}),400
        new_qty=min(20,int(cart.get(pid,0))+qty)
        if uid:
            db.execute('INSERT INTO cart_items(user_id,product_id,quantity) VALUES(?,?,?) ON CONFLICT(user_id,product_id) DO UPDATE SET quantity=excluded.quantity, updated_at=CURRENT_TIMESTAMP',(uid,int(pid),new_qty)); db.commit()
        else: cart[pid]=new_qty; session['cart']=cart; session.permanent=True
    elif request.method=='DELETE':
        data=request.get_json(silent=True) or {}; pid=str(data.get('product_id',''))
        if uid:
            if pid: db.execute('DELETE FROM cart_items WHERE user_id=? AND product_id=?',(uid,int(pid)))
            else: db.execute('DELETE FROM cart_items WHERE user_id=?',(uid,))
            db.commit()
        else:
            if pid: cart.pop(pid,None)
            else: cart={}
            session['cart']=cart; session.permanent=True
    if uid: cart={str(r['product_id']):int(r['quantity']) for r in db.execute('SELECT product_id,quantity FROM cart_items WHERE user_id=?',(uid,)).fetchall()}
    else: cart=session.get('cart',{})
    lines=[]; total=0
    for p in PRODUCTS:
        qty=int(cart.get(str(p['id']),0))
        if qty:
            line={**p,'quantity':qty,'subtotal':round(p['price']*qty,2)}; lines.append(line); total+=line['subtotal']
    return jsonify({'items':lines,'count':sum(x['quantity'] for x in lines),'total':round(total,2)})
@app.route('/checkout', methods=['GET','POST'])
def checkout():
    if not session.get('user_id'):
        flash('Please create an account or log in before checkout.', 'notice')
        return redirect(url_for('login', next=url_for('checkout')))
    uid=session.get('user_id')
    if uid:
        cart={str(r['product_id']):int(r['quantity']) for r in get_db().execute('SELECT product_id,quantity FROM cart_items WHERE user_id=?',(uid,)).fetchall()}
    else:
        cart=session.get('cart',{})
    lines=[]; total=0
    for p in PRODUCTS:
        qty=int(cart.get(str(p['id']),0))
        if qty: lines.append({**p,'quantity':qty,'subtotal':p['price']*qty}); total+=p['price']*qty
    if request.method=='POST':
        name=request.form.get('name','').strip(); email=request.form.get('email','').strip().lower(); address=request.form.get('address','').strip(); consent=request.form.get('demo_consent')=='yes'
        if not lines: flash('Your cart is empty.', 'error')
        elif not name or not re.match(r'^[^@\s]+@[^@\s]+\.[^@\s]+$',email) or not address or not consent: flash('Complete the required fields and acknowledge this is a demo order.', 'error')
        else:
            order_number='DEMO-'+secrets.token_hex(4).upper()
            cur=get_db().execute('INSERT INTO orders(user_id,order_number,customer_name,email,address,items_json,total) VALUES(?,?,?,?,?,?,?)',(session.get('user_id'),order_number,name,email,address,__import__('json').dumps(lines),total)); get_db().commit(); session['cart']={};
            if uid: get_db().execute('DELETE FROM cart_items WHERE user_id=?',(uid,)); get_db().commit()
            session['last_order']={'number':order_number,'total':total}; return redirect(url_for('order_success',order_id=cur.lastrowid))
    return render_template('checkout.html',items=lines,total=total)
@app.get('/order-success/<int:order_id>')
def order_success(order_id):
    order=get_db().execute('SELECT * FROM orders WHERE id=?',(order_id,)).fetchone()
    if not order: return render_template('404.html'),404
    if order['user_id'] and order['user_id']!=session.get('user_id'): return render_template('404.html'),404
    return render_template('order_success.html',order=order)
@app.route('/api/configurations', methods=['GET','POST'])
@login_required
def api_configurations():
    db=get_db()
    if request.method=='POST':
        d=request.get_json(silent=True) or {}; name=str(d.get('name','My configuration'))[:80]; colour=str(d.get('colour','Nocturne Black'))[:40]; interior=str(d.get('interior','Leather'))[:40]; wheels=str(d.get('wheels','Sport'))[:40]; finish=str(d.get('finish','Carbon fibre'))[:40]
        cur=db.execute('INSERT INTO configurations(user_id,name,colour,interior,wheels,finish) VALUES(?,?,?,?,?,?)',(session['user_id'],name,colour,interior,wheels,finish)); db.commit(); return jsonify({'ok':True,'id':cur.lastrowid})
    rows=db.execute('SELECT * FROM configurations WHERE user_id=? ORDER BY id DESC',(session['user_id'],)).fetchall(); return jsonify({'configurations':[dict(r) for r in rows]})
@app.route('/api/wishlist/<slug>', methods=['POST','DELETE'])
@login_required
def wishlist_toggle(slug):
    if not any(m['slug']==slug for m in MODELS): return jsonify({'error':'Model not found'}),404
    db=get_db()
    if request.method=='POST': db.execute('INSERT OR IGNORE INTO wishlist(user_id,model_slug) VALUES(?,?)',(session['user_id'],slug))
    else: db.execute('DELETE FROM wishlist WHERE user_id=? AND model_slug=?',(session['user_id'],slug))
    db.commit(); return jsonify({'saved':request.method=='POST'})
@app.get('/admin')
@login_required
@admin_required
def admin():
    db=get_db(); orders=db.execute('SELECT * FROM orders ORDER BY id DESC LIMIT 100').fetchall(); submissions=db.execute('SELECT * FROM form_submissions ORDER BY id DESC LIMIT 100').fetchall(); users=db.execute('SELECT id,name,email,is_admin,created_at FROM users ORDER BY id DESC').fetchall()
    return render_template('admin.html',orders=orders,submissions=submissions,users=users,products=PRODUCTS)
@app.errorhandler(404)
def not_found(_): return render_template('404.html'),404
@app.errorhandler(500)
def server_error(_): return render_template('500.html'),500

if __name__ == '__main__':
    app.run(debug=os.environ.get('FLASK_DEBUG','0')=='1', host=os.environ.get('HOST','127.0.0.1'), port=int(os.environ.get('PORT','5000')))
