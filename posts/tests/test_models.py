from django.test import TestCase
from django.contrib.auth import get_user_model

from posts.models import Group, Post


class PostModelTest(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        user = get_user_model().objects.create_user(username="TestTestov")

        cls.group = Group.objects.create(
            title="Группа номер 1"
        )

        cls.post = Post.objects.create(
            text="Запись номер 1",
            author=user
        )

    def test_verbose_name(self):
        post = PostModelTest.post
        field_verboses = {
            "text": "Текст",
            "group": "Группа",
        }

        for value, expected in field_verboses.items():
            with self.subTest(value=value):
                self.assertEqual(
                    post._meta.get_field(value).verbose_name, expected
                )

    def test_help_text(self):
        post = PostModelTest.post
        field_help_texts = {
            "text": "Содержание поста",
            "group": "Группа, содержащая пост",
        }

        for value, expected in field_help_texts.items():
            with self.subTest(value=value):
                self.assertEqual(
                    post._meta.get_field(value).help_text, expected
                )

    def test_object_name(self):
        post = PostModelTest.post
        group = PostModelTest.group

        object_names = {
            post: post.text[:15],
            group: group.title,
        }

        for object, expected in object_names.items():
            with self.subTest(value=object):
                self.assertEqual(expected, str(object))
