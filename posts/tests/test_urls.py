from django.test import TestCase, Client
from django.contrib.auth import get_user_model

from posts.models import Group, Post


User = get_user_model()


class StaticURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.group = Group.objects.create(
            id=1,
            title="Группа номер 1",
            slug="test_group"
        )

        username = "TestTestov"
        cls.user = User.objects.create_user(username=username)

        cls.post = Post.objects.create(
            id=1,
            text="Запись номер 1",
            author=cls.user,
            group=cls.group
        )

        cls.templates_url_names = {
            "index.html": "/",
            "group.html": f"/group/{cls.group.slug}/",
            "new_post.html": "/new/",
            "profile.html": f"/{username}/",
            "post.html": f"/{username}/{cls.post.id}/",
            "new_post.html": f"/{username}/{cls.post.id}/edit/",
        }

        cls.post_view_url = f"/{cls.user.username}/{cls.post.id}/"
        cls.post_edit_url = f"/{cls.user.username}/{cls.post.id}/edit/"

    def setUp(self):
        self.guest_client = Client()

        self.authorized_client = Client()
        self.authorized_client.force_login(StaticURLTests.user)

    def test_homepage(self):
        response = self.guest_client.get("/")
        self.assertEqual(response.status_code, 200)

    def test_group_page(self):
        group_slug = StaticURLTests.group.slug
        response = self.guest_client.get("/group/" + group_slug + "/")
        self.assertEqual(response.status_code, 200)

    def test_new_page_authorized(self):
        response = self.authorized_client.get("/new/")
        self.assertEqual(response.status_code, 200)

    def test_new_page_anonymous(self):
        response = self.guest_client.get("/new/", follow=True)
        self.assertRedirects(
            response, "/auth/login/?next=/new/"
        )

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = StaticURLTests.templates_url_names
        for template, url in templates_url_names.items():
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertTemplateUsed(response, template)

    def test_profile_page(self):
        response = self.guest_client.get(f"/{StaticURLTests.user.username}/")
        self.assertEqual(response.status_code, 200)

    def test_post_page(self):
        response = self.guest_client.get(StaticURLTests.post_view_url)
        self.assertEqual(response.status_code, 200)

    def test_edit_post_page_anonymous(self):
        response = self.guest_client.get(StaticURLTests.post_edit_url,
                                         follow=True)

        self.assertRedirects(response,
                             f"/auth/login/?next={StaticURLTests.post_edit_url}")

    def test_edit_post_page_authorized_owner(self):
        response = self.authorized_client.get(StaticURLTests.post_edit_url)
        self.assertEqual(response.status_code, 200)

    def test_edit_post_page_authorized_guest(self):
        visitor = User.objects.create_user(username="GuestUser")
        visitor_client = Client()
        visitor_client.force_login(visitor)
        response = visitor_client.get(StaticURLTests.post_edit_url,
                                      follow=True)
        self.assertRedirects(response, StaticURLTests.post_view_url)

    def test_404(self):
        response = self.guest_client.get("/40404040404040404040404/")
        self.assertEqual(response.status_code, 404)
