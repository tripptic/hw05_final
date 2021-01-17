from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Post


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.user = get_user_model().objects.create_user(username="TestTestov")

        posts = (Post(text=f"Номер {i}", author=cls.user) for i in range(13))
        Post.objects.bulk_create(posts)

        cls.urls = (
            reverse("index"),
            reverse("profile", kwargs={"username": cls.user.username}),
        )

    def setUp(self):
        self.guest_client = Client()

        self.authorized_client = Client()
        self.authorized_client.force_login(PaginatorViewsTest.user)

    def test_first_page_contains_ten_records(self):
        for url in PaginatorViewsTest.urls:
            response = self.client.get(url)
            self.assertEqual(len(response.context.get("page").object_list), 10)

    def test_second_page_contains_three_records(self):
        for url in PaginatorViewsTest.urls:
            response = self.client.get(url + "?page=2")
            self.assertEqual(len(response.context.get("page").object_list), 3)
