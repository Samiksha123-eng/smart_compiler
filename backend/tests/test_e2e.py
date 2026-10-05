"""
End-to-End API Integration Test.
Verifies all REST API routes using Flask test client.
"""

import unittest
from backend.app import app
from backend.sample_programs import SAMPLES


class TestFlaskAPI(unittest.TestCase):

    def setUp(self):
        self.client = app.test_client()

    def test_get_languages(self):
        res = self.client.get('/api/languages')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data['success'])
        self.assertIn("C", data['languages'])
        self.assertIn("Python", data['languages'])

    def test_get_samples(self):
        res = self.client.get('/api/samples')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data['success'])
        self.assertIn("c", data['samples'])

    def test_analyze_c_buggy(self):
        res = self.client.post('/api/analyze', json={
            "language": "c",
            "source_code": SAMPLES["c"]["buggy"]
        })
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertFalse(data['success'])
        self.assertGreater(data['total_errors'], 0)
        self.assertGreater(len(data['errors']), 0)
        self.assertGreater(len(data['tokens']), 0)
        self.assertGreater(len(data['symbol_table']), 0)

    def test_analyze_python_clean(self):
        res = self.client.post('/api/analyze', json={
            "language": "python",
            "source_code": SAMPLES["python"]["clean"]
        })
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data['success'])
        self.assertEqual(data['total_errors'], 0)

    def test_history_flow(self):
        # 1. Trigger an analysis
        self.client.post('/api/analyze', json={
            "language": "c",
            "source_code": "int main() { return 0; }"
        })

        # 2. Get history
        res = self.client.get('/api/history')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data['success'])
        self.assertGreater(len(data['history']), 0)

        # 3. Clear history
        del_res = self.client.delete('/api/history')
        self.assertEqual(del_res.status_code, 200)

        # 4. Verify cleared
        res2 = self.client.get('/api/history')
        self.assertEqual(len(res2.get_json()['history']), 0)


if __name__ == "__main__":
    unittest.main()
