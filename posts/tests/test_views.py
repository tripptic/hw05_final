import tempfile
import shutil

from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django import forms
from django.db import models
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.cache import cache

from posts.models import Group, Post, Follow

MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
User = get_user_model()


@override_settings(MEDIA_ROOT=MEDIA_ROOT)
class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.user = User.objects.create_user(username="TestTestov")

        cls.group = Group.objects.create(
            id=1,
            title="Группа номер 1",
            slug="test_group"
        )

        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x01\x00'
            b'\x01\x00\x00\x00\x00\x21\xf9\x04'
            b'\x01\x0a\x00\x01\x00\x2c\x00\x00'
            b'\x00\x00\x01\x00\x01\x00\x00\x02'
            b'\x02\x4c\x01\x00\x3b'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )

        cls.post = Post.objects.create(
            id=1,
            text="Запись номер 1",
            author=cls.user,
            group=cls.group,
            image=cls.uploaded
        )

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(MEDIA_ROOT, ignore_errors=False)
        super().tearDownClass()

    def setUp(self):
        self.guest_client = Client()

        self.authorized_client = Client()
        self.authorized_client.force_login(PostPagesTests.user)

    def test_pages_uses_correct_template(self):
        templates_page_names = {
            "index.html": reverse("index"),
            "group.html": (
                reverse("group_posts", kwargs={"slug": "test_group"})
            ),
            "new_post.html": reverse("new_post"),
            "profile.html": (
                reverse("profile",
                        kwargs={"username": PostPagesTests.user.username})
            ),
            "post.html": (
                reverse("post",
                        kwargs={"username": PostPagesTests.user.username,
                                "post_id": PostPagesTests.post.id})
            ),
        }

        for template, reverse_name in templates_page_names.items():
            with self.subTest(template=template):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_page_show_correct_context(self):
        response = self.guest_client.get(reverse("index"))

        post_fields = {
            "text": models.TextField,
            "pub_date": models.DateTimeField,
            "author": models.ForeignKey,
            "group": models.ForeignKey,
            "image": models.ImageField,
        }

        for value, expected in post_fields.items():
            with self.subTest(value=value):
                post_field = (response.context.get("page")[0]
                              ._meta.get_field(value))
                self.assertIsInstance(post_field, expected)

    def test_group_post_page_show_correct_context(self):
        response = self.guest_client.get(
                        reverse("group_posts", kwargs={"slug": "test_group"}))

        post_fields = {
            "text": models.TextField,
            "pub_date": models.DateTimeField,
            "author": models.ForeignKey,
            "group": models.ForeignKey,
            "image": models.ImageField,
        }
        for value, expected in post_fields.items():
            with self.subTest(value=value):
                post_field = (response.context.get("page")[0]
                              ._meta.get_field(value))
                self.assertIsInstance(post_field, expected)

        group_fields = {
            "title": models.CharField,
            "slug": models.SlugField,
            "description": models.TextField,
        }
        for value, expected in group_fields.items():
            with self.subTest(value=value):
                group_field = (response.context.get("group")
                               ._meta.get_field(value))
                self.assertIsInstance(group_field, expected)

    def test_new_post_page_show_correct_context(self):
        response = self.authorized_client.get(reverse("new_post"))

        form_fields = {
            "text": forms.fields.CharField,
            "group": forms.models.ModelChoiceField,
        }

        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get("form").fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_pages_show_correct_context_with_group(self):
        urls = (
            reverse("index"),
            reverse("group_posts", kwargs={"slug": "test_group"}),
        )

        for url in urls:
            with self.subTest(value=url):
                response = self.guest_client.get(url)
                post = response.context.get("page")[0]

                self.assertEqual(post.id, 1)
                self.assertEqual(post.text, "Запись номер 1")
                self.assertEqual(post.group, PostPagesTests.group)
                self.assertEqual(post.image, PostPagesTests.post.image)

    def test_group_post_page_show_correct_context_different_group(self):
        Group.objects.create(
            id=2,
            title="Группа номер 2",
            slug="second_group"
        )
        response = self.guest_client.get(
            reverse("group_posts", kwargs={"slug": "second_group"})
        )

        self.assertEqual(len(response.context.get("page")), 0)

    def test_profile_page_show_correct_context(self):
        response = self.guest_client.get(f"/{PostPagesTests.user.username}/")

        post_fields = {
            "text": models.TextField,
            "pub_date": models.DateTimeField,
            "author": models.ForeignKey,
            "group": models.ForeignKey,
            "image": models.ImageField,
        }

        post = response.context.get("page")[0]
        for value, expected in post_fields.items():
            with self.subTest(value=value):
                post_field = (post._meta.get_field(value))
                self.assertIsInstance(post_field, expected)

        self.assertEqual(post.id, 1)
        self.assertEqual(post.text, "Запись номер 1")
        self.assertEqual(post.group, PostPagesTests.group)
        self.assertEqual(post.image, PostPagesTests.post.image)

        author = response.context.get("author")
        self.assertEqual(author.username, PostPagesTests.user.username)

        paginator = response.context.get("paginator")
        self.assertEqual(paginator.count, 1)

    def test_post_page_show_correct_context(self):
        response = self.guest_client.get(
            f"/{PostPagesTests.user.username}/{PostPagesTests.post.id}/")

        post_fields = {
            "text": models.TextField,
            "pub_date": models.DateTimeField,
            "author": models.ForeignKey,
            "group": models.ForeignKey,
            "image": models.ImageField,
        }

        post = response.context.get("post")
        for value, expected in post_fields.items():
            with self.subTest(value=value):
                post_field = (post._meta.get_field(value))
                self.assertIsInstance(post_field, expected)

        self.assertEqual(post.id, 1)
        self.assertEqual(post.text, "Запись номер 1")
        self.assertEqual(post.group, PostPagesTests.group)
        self.assertEqual(post.image, PostPagesTests.post.image)

        author = response.context.get("author")
        self.assertEqual(author.username, PostPagesTests.user.username)

        post_count = response.context.get("post_count")
        self.assertEqual(post_count, 1)

    def test_post_edit_page_show_correct_context(self):
        response = self.authorized_client.get(
            f"/{PostPagesTests.user.username}/{PostPagesTests.post.id}/edit/")

        form_fields = {
            "text": forms.fields.CharField,
            "group": forms.models.ModelChoiceField,
        }

        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get("form").fields.get(value)
                self.assertIsInstance(form_field, expected)

        post = response.context.get("post")
        self.assertEqual(post.author.username, PostPagesTests.user.username)
        self.assertEqual(post.id, PostPagesTests.post.id)

    def test_index_page_show_correct_context_with_cache(self):
        reverse_index = reverse('index')
        initial_response = self.authorized_client.get(reverse_index)
        PostPagesTests.post.text = "123123"
        PostPagesTests.post.save()
        response_with_cache = self.authorized_client.get(reverse_index)

        self.assertHTMLEqual(str(initial_response.content),
                             str(response_with_cache.content))
        cache.clear()
        response_without_cache = self.authorized_client.get(reverse_index)

        self.assertHTMLNotEqual(str(initial_response.content),
                                str(response_without_cache.content))

    def test_profile_follow(self):
        author = User.objects.create_user(username="SomeAuthor")

        response = self.authorized_client.post(
            reverse("profile_follow", kwargs={"username": author.username}),
            follow=True
        )

        url = reverse("profile", kwargs={"username": author.username})
        self.assertRedirects(response, url)
        followed = Follow.objects.filter(user=PostPagesTests.user,
                                         author=author).exists()
        self.assertTrue(followed)

    def test_profile_unfollow(self):
        author = User.objects.create_user(username="SomeAuthor")

        Follow.objects.create(user=PostPagesTests.user, author=author)

        response = self.authorized_client.post(
            reverse("profile_unfollow", kwargs={"username": author.username}),
            follow=True
        )

        url = reverse("profile", kwargs={"username": author.username})
        self.assertRedirects(response, url)
        followed = Follow.objects.filter(user=PostPagesTests.user,
                                         author=author).exists()
        self.assertFalse(followed)

    def test_follow_page_correct_context(self):
        author = User.objects.create_user(username="SomeAuthor")
        post_text = "Запись отобразится у подписчиков"
        Post.objects.create(
            text=post_text,
            author=author
        )
        Follow.objects.create(user=PostPagesTests.user, author=author)
        response = self.authorized_client.get("/follow/")
        post = response.context.get("page")[0]

        self.assertEqual(post.text, post_text)

        non_subscriber = User.objects.create_user(username="non_subscriber")
        non_subscriber_client = Client()
        non_subscriber_client.force_login(non_subscriber)
        response = non_subscriber_client.get("/follow/")

        self.assertEqual(len(response.context.get("page")), 0)

    def test_add_comment_authorized(self):
        author = User.objects.create_user(username="SomeAuthor")
        new_post = Post.objects.create(
            id=4,
            text="Новая запись",
            author=author
        )

        form_data = {
            "text": "Измененный текст"
        }
        comment_url = reverse(
            "add_comment",
            kwargs={"username": author.username, "post_id": new_post.id}
        )
        response = self.authorized_client.post(comment_url, follow=True,
                                               data=form_data)

        url = reverse("post", kwargs={"username": author.username,
                                      "post_id": new_post.id})

        self.assertRedirects(response, url)
        self.assertEqual(new_post.comments.count(), 1)

    def test_add_comment_unauthorized(self):
        author = User.objects.create_user(username="SomeAuthor")
        new_post = Post.objects.create(
            id=4,
            text="Новая запись",
            author=author
        )

        form_data = {
            "text": "Измененный текст"
        }
        comment_url = reverse(
            "add_comment",
            kwargs={"username": author.username, "post_id": new_post.id}
        )
        response = self.guest_client.post(comment_url, follow=True,
                                          data=form_data)

        self.assertRedirects(response,
                             "/auth/login/?next=/SomeAuthor/4/comment/")
        self.assertEqual(new_post.comments.count(), 0)
