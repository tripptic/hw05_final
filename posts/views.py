from xxlimited import Null
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.contrib.auth import get_user_model
from django.http import HttpResponseRedirect
from django.urls import reverse

from .models import Post, Group, Follow
from .forms import PostForm, CommentForm


User = get_user_model()


def index(request):
    post_list = Post.objects.select_related("group", "author")
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get("page")
    page = paginator.get_page(page_number)
    return render(request, "index.html", {"page": page,
                                          "paginator": paginator})


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    post_list = group.posts.select_related("group", "author")

    paginator = Paginator(post_list, 10)
    page_number = request.GET.get("page")
    page = paginator.get_page(page_number)
    return render(request, "group.html", {"group": group, "page": page,
                                          "paginator": paginator})


@login_required
def new_post(request):
    form = PostForm(request.POST or None, files=request.FILES or None)
    if request.method == "POST" and form.is_valid():
        new_post = form.save(commit=False)
        new_post.author = request.user
        new_post.save()
        return redirect("/")
    return render(request, "new_post.html", {"form": form})


@login_required
def post_edit(request, username, post_id):
    user = get_object_or_404(User, username=username)
    post = get_object_or_404(Post, id=post_id, author=user)
    if user != request.user:
        return redirect("post", username=username, post_id=post_id)

    form = PostForm(request.POST or None, files=request.FILES or None,
                    instance=post)
    if request.method == "POST" and form.is_valid():
        edited_post = form.save(commit=False)
        edited_post.author = request.user
        edited_post.save()
        return redirect("post", username=username, post_id=post_id)

    return render(request, "new_post.html", {"form": form, "post": post})


def profile(request, username):
    author = get_object_or_404(User, username=username)
    post_list = author.posts.select_related("group", "author")
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get("page")
    page = paginator.get_page(page_number)
    if request.user.is_authenticated:
        following = author.following.filter(user=request.user).exists()
    else:
        following = False
    following_count = author.following.count()
    follower_count = author.follower.count()
    post_count = paginator.count
    context = {
        "author": author,
        "page": page,
        "post_count": post_count,
        "paginator": paginator,
        "following": following,
        "following_count": following_count,
        "follower_count": follower_count,
    }
    return render(request, "profile.html", context)


def post_view(request, username, post_id):
    author = get_object_or_404(User, username=username)
    post_count = author.posts.count()
    post = get_object_or_404(Post, id=post_id)
    comments = post.comments.all()
    if request.user.is_authenticated:
        following = author.following.filter(user=request.user).exists()
    else:
        following = False
    following_count = author.following.count()
    follower_count = author.follower.count()
    context = {
        "author": author,
        "post": post,
        "post_count": post_count,
        "comments": comments,
        "form": CommentForm(),
        "following": following,
        "following_count": following_count,
        "follower_count": follower_count,
    }
    return render(request, "post.html", context)


@login_required
def add_comment(request, username, post_id):
    user = get_object_or_404(User, username=username)
    post = get_object_or_404(Post, id=post_id, author=user)
    form = CommentForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        new_comment = form.save(commit=False)
        new_comment.author = request.user
        new_comment.post = post
        new_comment.save()
    return redirect("post", username=username, post_id=post_id)


def page_not_found(request, exception):
    return render(
        request,
        "misc/404.html",
        {"path": request.path},
        status=404
    )


def server_error(request):
    return render(request, "misc/500.html", status=500)


@login_required
def follow_index(request):
    authors = Follow.objects.filter(user=request.user).values_list('author')
    post_list = Post.objects.filter(author__in=authors)
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get("page")
    page = paginator.get_page(page_number)
    return render(request, "follow.html", {"page": page,
                                           "paginator": paginator})


@login_required
def profile_follow(request, username):
    user = request.user
    author = get_object_or_404(User, username=username)
    if user != author and not user.follower.filter(author=author).exists():
        Follow.objects.create(user=user, author=author)
    back_url = reverse("profile", kwargs={"username": username})
    return redirect(request.META.get('HTTP_REFERER', back_url))


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    Follow.objects.filter(user=request.user, author=author).delete()
    back_url = reverse("profile", kwargs={"username": username})
    return redirect(request.META.get('HTTP_REFERER', back_url))
