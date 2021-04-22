from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render, reverse

from posts.forms import CommentForm, PostForm
from posts.models import Follow, Group, Post, User
from yatube.settings import POSTS_ON_PAGE


def index(request):
    latest = Post.objects.all()
    paginator = Paginator(latest, POSTS_ON_PAGE)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    context = {'page': page}
    return render(request, 'index.html', context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.all()
    paginator = Paginator(posts, POSTS_ON_PAGE)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    context = {'page': page, 'group': group}
    return render(request, 'group.html', context)


@login_required
def new_post(request):
    if request.method == 'POST':
        form = PostForm(
            request.POST or None,
            files=request.FILES or None,
        )
        if form.is_valid():
            new_post = form.save(commit=False)
            new_post.author = request.user
            new_post.save()
            return redirect('index')
        context = {'form': form, 'is_new_post': True}
        return render(request, 'new_post.html', context)
    form = PostForm()
    context = {'form': form, 'is_new_post': True}
    return render(request, 'new_post.html', context)


def profile(request, username):
    username = get_object_or_404(User, username=username)
    user = request.user
    posts = username.posts.all()
    paginator = Paginator(posts, POSTS_ON_PAGE)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    follow_mark = (user.is_authenticated and
                   user.follower.filter(author=username).exists()
                   )
    if follow_mark and user != username:
        follow_mark = True
    elif user != username:
        follow_mark = False
    context = {
        'page': page,
        'author': username,
        'follow_mark': follow_mark
    }
    return render(request, 'profile.html', context)


def post_view(request, username, post_id):
    post = get_object_or_404(Post, author__username=username, id=post_id)
    author = post.author
    form = CommentForm()
    comments = post.comments.all()
    user = request.user
    follow_mark = (user.is_authenticated
                   and Follow.objects.filter(user=user, author=author).exists()
                   )
    if follow_mark and user != author:
        follow_mark = True
    elif user != author:
        follow_mark = False
    context = {
        'post': post,
        'author': author,
        'form': form,
        'comments': comments,
        'follow_mark': follow_mark
    }
    return render(request, 'post.html', context)


@login_required
def add_comment(request, username, post_id):
    post = get_object_or_404(Post, author__username=username, id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
        return redirect('post', username=username, post_id=post_id)
    return redirect('post', username=username, post_id=post_id)


@login_required
def post_edit(request, username, post_id):
    post = get_object_or_404(Post, author__username=username, id=post_id)
    if request.user != post.author:
        return redirect(reverse('post', args=[username, post_id]))
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )
    if form.is_valid():
        form.save()
        return redirect(reverse('post', args=[username, post_id]))
    context = {'form': form, 'post': post}
    return render(request, 'new_post.html', context)


def page_not_found(request, exception):
    return render(
        request,
        'misc/404.html',
        {'path': request.path},
        status=404
    )


def server_error(request):
    return render(request, 'misc/500.html', status=500)


@login_required
def follow_index(request):
    user = request.user
    following_posts = Post.objects.filter(author__following__user=user)
    paginator = Paginator(following_posts, POSTS_ON_PAGE)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    context = {'page': page}
    return render(request, 'follow.html', context)


@login_required
def profile_follow(request, username):
    user = request.user
    username = get_object_or_404(User, username=username)
    following_author = get_object_or_404(User, username=username)
    if user != following_author and not Follow.objects.filter(
            user=user, author=username
    ).exists():
        follow = Follow(user=request.user, author=following_author)
        follow.save()
        return redirect('profile', username=username)
    return redirect('profile', username=username)


@login_required
def profile_unfollow(request, username):
    unfollowing_author = get_object_or_404(User, username=username)
    unfollow = Follow.objects.filter(
        user=request.user, author=unfollowing_author)
    unfollow.delete()
    return redirect('profile', username=username)
