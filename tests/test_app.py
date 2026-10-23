import os, tempfile, unittest
from pathlib import Path
import app as project

class BugattiAppSmokeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._old_db = project.DB_PATH
        cls.temp_dir = tempfile.TemporaryDirectory()
        project.DB_PATH = Path(cls.temp_dir.name) / 'test.sqlite3'
        with project.app.app_context(): project.init_db()
        project.app.config.update(TESTING=True, SECRET_KEY='test-key')

    @classmethod
    def tearDownClass(cls):
        project.DB_PATH = cls._old_db
        cls.temp_dir.cleanup()

    def setUp(self):
        self.client = project.app.test_client()

    def test_pages_render(self):
        for path in ['/', '/models', '/history', '/sur-mesure', '/live', '/store', '/configurator', '/login', '/register', '/contact', '/dealer-finder', '/service', '/careers']:
            response = self.client.get(path)
            self.assertEqual(response.status_code, 200, path)

    def test_products_api(self):
        response = self.client.get('/api/products?q=cap')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(any('Cap' in item['name'] for item in response.get_json()['products']))

    def test_cart_add_and_remove(self):
        response = self.client.post('/api/cart', json={'product_id': 1, 'quantity': 2})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()['count'], 2)
        response = self.client.delete('/api/cart', json={'product_id': 1})
        self.assertEqual(response.get_json()['count'], 0)

    def test_registration_and_dashboard(self):
        response = self.client.post('/register', data={'name':'Test User','email':'test@example.test','password':'testing-pass-123','confirm_password':'testing-pass-123'}, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Welcome', response.data)
        self.assertEqual(self.client.get('/dashboard').status_code, 200)

if __name__ == '__main__': unittest.main()
