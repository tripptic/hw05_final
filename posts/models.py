from django.db import models
from django.contrib.auth import get_user_model


User = get_user_model()


class Group(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    description = models.TextField()

    def __str__(self):
        return self.title


class Post(models.Model):
    text = models.TextField(verbose_name="Текст", help_text="Содержание поста")
    pub_date = models.DateTimeField("date published", auto_now_add=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE,
                               related_name="posts", editable=False)
    group = models.ForeignKey(Group, on_delete=models.SET_NULL,
                              related_name="posts", blank=True, null=True,
                              verbose_name="Группа",
                              help_text="Группа, содержащая пост")
    image = models.ImageField(upload_to='posts/', blank=True, null=True)

    class Meta:
        ordering = ["-pub_date"]

    def __str__(self):
        return self.text[:15]


class Comment(models.Model):
    text = models.TextField("Текст", help_text="Комментарий к посту")
    author = models.ForeignKey(User, on_delete=models.CASCADE,
                               related_name="comments", editable=False)
    post = models.ForeignKey(Post, on_delete=models.CASCADE,
                             related_name="comments", editable=False)
    created = models.DateTimeField("Date created", auto_now_add=True)


class Follow(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE,
                             related_name="follower", editable=False)

    author = models.ForeignKey(User, on_delete=models.CASCADE,
                               related_name="following", editable=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user', 'author'],
                                    name='user_author')
        ]
