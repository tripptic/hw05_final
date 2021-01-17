import tempfile
import shutil

from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile

from posts.forms import PostForm
from posts.models import Post


User = get_user_model()
MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=MEDIA_ROOT)
class TaskCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.form = PostForm()

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(MEDIA_ROOT, ignore_errors=False)
        super().tearDownClass()

    def setUp(self):
        self.guest_client = Client()

        self.user = User.objects.create_user(username="TestTestov")
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_create_post(self):
        posts_count = Post.objects.count()

        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x01\x00'
            b'\x01\x00\x00\x00\x00\x21\xf9\x04'
            b'\x01\x0a\x00\x01\x00\x2c\x00\x00'
            b'\x00\x00\x01\x00\x01\x00\x00\x02'
            b'\x02\x4c\x01\x00\x3b'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        form_data = {
            "text": "Новый пост",
            "image": uploaded,
        }
        response = self.authorized_client.post(
            reverse("new_post"),
            data=form_data,
            follow=True
        )

        self.assertRedirects(response, "/")
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertTrue(Post.objects.filter(text="Новый пост").exists())

    def test_edit_post(self):
        Post.objects.create(
            id=1,
            text="Запись номер 1",
            author=self.user
        )

        form_data = {
            "text": "Измененный текст"
        }
        response = self.authorized_client.post(
            reverse("post_edit", kwargs={"username": self.user.username,
                                         "post_id": 1}),
            data=form_data,
            follow=True
        )

        url = reverse("post", kwargs={"username": self.user.username,
                                      "post_id": 1})
        self.assertRedirects(response, url)
        self.assertEqual(Post.objects.count(), 1)
        self.assertTrue(Post.objects.filter(text="Измененный текст").exists())
