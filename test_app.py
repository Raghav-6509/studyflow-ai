import unittest
import json
import app as app_module
from app import app, RESPONSE_CACHE

class StudyHelperTestCase(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        self.client = app.test_client()
        RESPONSE_CACHE.clear()

    def test_health_check(self):
        res = self.client.get('/api/health')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn('status', data)
        self.assertIn('model', data)
        self.assertIn('cached_items', data)

    def test_topic_validation(self):
        res = self.client.post('/api/generate-notes', json={'topic': ''})
        self.assertEqual(res.status_code, 400)
        data = res.get_json()
        self.assertIn('Topic is required', data['error'])

    def test_mock_study_pack_and_caching(self):
        # Enable mock AI to test full flow without burning Gemini quota
        original_mock = app_module.MOCK_AI
        app_module.MOCK_AI = True
        try:
            payload = {
                'topic': 'Photosynthesis',
                'level': 'Undergraduate',
                'goal': 'Revision'
            }
            res = self.client.post('/api/generate-study-pack', json=payload)
            self.assertEqual(res.status_code, 200)
            data = res.get_json()
            self.assertIn('notes', data)
            self.assertIn('questions', data)
            self.assertEqual(len(data['questions']), 5)
            self.assertIn('summary', data)
            self.assertIn('flashcards', data)
            self.assertIn('checklist', data)
            self.assertTrue(data.get('mock'))

            # Second request should be served from memory cache (0 API calls, instant response)
            cached_res = self.client.post('/api/generate-study-pack', json=payload)
            self.assertEqual(cached_res.status_code, 200)
            cached_data = cached_res.get_json()
            self.assertTrue(cached_data.get('cached'))
        finally:
            app_module.MOCK_AI = original_mock

    def test_mock_individual_endpoints(self):
        original_mock = app_module.MOCK_AI
        app_module.MOCK_AI = True
        try:
            # Notes
            res = self.client.post('/api/generate-notes', json={'topic': 'Calculus', 'level': 'High School'})
            self.assertEqual(res.status_code, 200)
            self.assertIn('notes', res.get_json())

            # Questions
            res = self.client.post('/api/generate-questions', json={'topic': 'Calculus', 'level': 'High School'})
            self.assertEqual(res.status_code, 200)
            self.assertEqual(len(res.get_json()['questions']), 5)

            # Summary
            res = self.client.post('/api/generate-summary', json={'topic': 'Calculus', 'level': 'High School'})
            self.assertEqual(res.status_code, 200)
            self.assertIn('summary', res.get_json())

            # Flashcards
            res = self.client.post('/api/generate-flashcards', json={'topic': 'Calculus', 'level': 'High School'})
            self.assertEqual(res.status_code, 200)
            self.assertGreater(len(res.get_json()['flashcards']), 0)
        finally:
            app_module.MOCK_AI = original_mock

if __name__ == '__main__':
    unittest.main()
