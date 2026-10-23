(() => {
  const $=(s,r=document)=>r.querySelector(s), $$=(s,r=document)=>[...r.querySelectorAll(s)];
  const menuToggle=$('.menu-toggle'), nav=$('.main-nav');
  if(menuToggle&&nav) menuToggle.addEventListener('click',()=>{const open=nav.classList.toggle('mobile-open');menuToggle.setAttribute('aria-expanded',String(open));});
  $$('.nav-trigger').forEach(btn=>btn.addEventListener('click',()=>{const group=btn.closest('.nav-group');const isOpen=group.classList.toggle('open');btn.setAttribute('aria-expanded',String(isOpen));}));
  const searchPanel=$('.search-panel');
  $('.search-open')?.addEventListener('click',()=>{searchPanel.hidden=false;$('#site-search-input')?.focus();});
  $('.search-close')?.addEventListener('click',()=>{searchPanel.hidden=true;$('#search-results').innerHTML='';});
  const searchForm=$('#site-search-form');
  searchForm?.addEventListener('submit',async e=>{e.preventDefault();const q=$('#site-search-input').value.trim();const box=$('#search-results');box.innerHTML='';if(!q)return;try{const r=await fetch('/api/search?q='+encodeURIComponent(q));const d=await r.json();if(!d.results.length){box.textContent='No matching results found.';return;}d.results.forEach(item=>{const a=document.createElement('a');a.className='search-result';a.href=item.url;const title=document.createElement('strong');title.textContent=item.title;const type=document.createElement('span');type.textContent=item.type;a.append(type,title);box.append(a);});}catch{box.textContent='Search is temporarily unavailable.';}});

  // Accessible full-screen image viewer for vehicle and store imagery.
  const viewer=$('#image-viewer');
  if(viewer){
    const viewImg=$('.viewer-image',viewer), caption=$('.viewer-caption',viewer);
    const sources=$$('[data-zoom-src]').map(el=>({src:el.dataset.zoomSrc,title:el.dataset.zoomTitle||el.getAttribute('aria-label')||'Bugatti'}));
    let active=0, lastFocus=null;
    const openViewer=(el)=>{const src=el.dataset.zoomSrc;if(!src)return;const list=sources.length?sources:[{src,title:el.dataset.zoomTitle||'Bugatti'}];active=Math.max(0,list.findIndex(x=>x.src===src));viewer._sources=list;lastFocus=el;viewImg.src=list[active].src;viewImg.alt=list[active].title;caption.textContent=list[active].title;viewer.hidden=false;document.body.classList.add('viewer-open');$('.viewer-close',viewer).focus();};
    const move=(delta)=>{const list=viewer._sources||sources;if(!list.length)return;active=(active+delta+list.length)%list.length;viewImg.src=list[active].src;viewImg.alt=list[active].title;caption.textContent=list[active].title;};
    $$('[data-zoom-src]').forEach(el=>el.addEventListener('click',e=>{e.preventDefault();e.stopPropagation();openViewer(el);}));
    $('.viewer-close',viewer)?.addEventListener('click',()=>{viewer.hidden=true;document.body.classList.remove('viewer-open');if(lastFocus?.focus)lastFocus.focus();});
    $('.viewer-prev',viewer)?.addEventListener('click',()=>move(-1));$('.viewer-next',viewer)?.addEventListener('click',()=>move(1));
    viewer.addEventListener('click',e=>{if(e.target===viewer){viewer.hidden=true;document.body.classList.remove('viewer-open');lastFocus?.focus?.();}});
    document.addEventListener('keydown',e=>{if(viewer.hidden)return;if(e.key==='Escape')$('.viewer-close',viewer)?.click();if(e.key==='ArrowLeft')move(-1);if(e.key==='ArrowRight')move(1);});
  }
  // Native anchor scroll is smooth; this gives the hero cue a small, reliable scroll on click.
  $$('.scroll-cue,.editorial-scroll').forEach(link=>link.addEventListener('click',e=>{const target=$(link.getAttribute('href'));if(target){e.preventDefault();target.scrollIntoView({behavior:matchMedia('(prefers-reduced-motion: reduce)').matches?'auto':'smooth',block:'start'});}}));

  $$('.flash').forEach(el=>setTimeout(()=>el.remove(),6500));
  const toast=(message)=>{const t=$('#toast');if(!t)return;t.textContent=message;t.classList.add('show');clearTimeout(window.__toastTimer);window.__toastTimer=setTimeout(()=>t.classList.remove('show'),2400);};
  window.BugattiDemo={toast};
  $$('.wishlist-button').forEach(btn=>btn.addEventListener('click',async()=>{try{const method=btn.dataset.saved==='true'?'DELETE':'POST';const r=await fetch('/api/wishlist/'+encodeURIComponent(btn.dataset.slug),{method});if(r.status===401){location.href='/login';return;}if(!r.ok){if(r.redirected){location.href='/login';return;}throw Error();}const d=await r.json();btn.dataset.saved=String(d.saved);btn.textContent=d.saved?'♥ SAVED':'♡ SAVE TO FAVOURITES';toast(d.saved?'Added to favourites':'Removed from favourites');}catch{toast('Please log in to save favourite models.');}}));
  $$('[data-model-filter]').forEach(btn=>btn.addEventListener('click',()=>{$$('[data-model-filter]').forEach(b=>b.classList.remove('active'));btn.classList.add('active');const f=btn.dataset.modelFilter;$$('[data-model-type]').forEach(card=>card.classList.toggle('hidden',f!=='All'&&card.dataset.modelType!==f));}));
})();
