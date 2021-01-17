from django.test import TestCase, Client


class StaticURLTests(TestCase):
    def setUp(self):
        self.guest_client = Client()

    def test_author_page(self):
        response = self.guest_client.get('/about/author/')
        self.assertEqual(response.status_code, 200)

    def test_technology_page(self):
        response = self.guest_client.get('/about/tech/')
        self.assertEqual(response.status_code, 200)
