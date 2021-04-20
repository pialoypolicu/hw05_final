from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render, reverse
from django.views.decorators.cache import cache_page

from posts.forms import CommentForm, PostForm
from posts.models import Group, Post, User, Follow
from yatube.settings import POSTS_ON_PAGE


def index(request):
    latest = Post.objects.all()
    paginator = Paginator(latest, POSTS_ON_PAGE)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(
        request,
        'index.html',
        {'page': page}
    )


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.all()
    paginator = Paginator(posts, POSTS_ON_PAGE)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(request, 'group.html', {'page': page, 'group': group})


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
        return render(
            request,
            'new_post.html',
            {'form': form, 'is_new_post': True}
        )
    form = PostForm()
    return render(
        request,
        'new_post.html',
        {'form': form, 'is_new_post': True}
    )


def profile(request, username):
    username = get_object_or_404(User, username=username)
    #__import__('pdb').set_trace()
    user = request.user
    posts = username.posts.all()
    paginator = Paginator(posts, POSTS_ON_PAGE)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    following = (user.is_authenticated and
                 Follow.objects.filter(user=user, author=username).exists()
                 )
    if following and user != username:
        following = True
    elif user != username:
        following = False
    return render(
        request,
        'profile.html',
        {'page': page, 'author': username, 'following': following}
    )


def post_view(request, username, post_id):
    post = get_object_or_404(Post, author__username=username, id=post_id)
    author = post.author
    form = CommentForm()
    comments = post.comments.all()
    user = request.user
    following = (user.is_authenticated and
                 Follow.objects.filter(user=user, author=author).exists()
                 )
    if following and user != author:
        following = True
    elif user != author:
        following = False
    context = {
        'post': post,
        'author': author,
        'form': form,
        'comments': comments,
        'following': following
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
    return render(request, 'new_post.html', {'form': form})


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
    return render(request, "follow.html", {'page': page})

@login_required
def profile_follow(request, username):
    save = get_object_or_404(User, username=username)
    fol = Follow(user=request.user, author=save)
    fol.save()
    return redirect('profile', username=username)


@login_required
def profile_unfollow(request, username):
    save = get_object_or_404(User, username=username)
    fol = Follow.objects.filter(user=request.user, author=save)
    fol.delete()
    return redirect('profile', username=username)
