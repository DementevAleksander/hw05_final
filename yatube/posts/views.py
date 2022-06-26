from django.core.paginator import Paginator
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required


from .models import Post, Group, Follow
from .forms import PostForm, CommentForm

LIMIT_POSTS = 10
User = get_user_model()


def index(request):
    post_list = Post.objects.select_related().all()
    page_obj = paginator(request, post_list, LIMIT_POSTS)
    template = 'posts/index.html'

    context = {
        'page_obj': page_obj,
    }
    return render(request, template, context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    post_list = group.posts.all()
    page_obj = paginator(request, post_list, LIMIT_POSTS)
    template = 'posts/group_list.html'

    context = {
        'group': group,
        'page_obj': page_obj,
    }
    return render(request, template, context)


def profile(request, username):
    user = get_object_or_404(User, username=username)
    post_list = user.posts.all()
    template = 'posts/profile.html'
    page_obj = paginator(request, post_list, LIMIT_POSTS)

    follower = request.user
    followed = User.objects.get(username=username)
    following = False
    if follower.is_active:
        following = Follow.objects.filter(
            user=follower, author=followed).exists()

    context = {
        'author': user,
        'page_obj': page_obj,
        'post_list': post_list,
        'following': following,
    }
    return render(request, template, context)


def post_detail(request, post_id):
    post_list = get_object_or_404(Post, id=post_id)
    comments_list = post_list.comments.all()
    comment_form = CommentForm(request.POST or None)
    template = 'posts/post_detail.html'

    context = {
        'post_list': post_list,
        'comment_form': comment_form,
        'comments': comments_list,
    }
    return render(request, template, context)


@login_required
def post_create(request):
    if request.method == 'POST':
        form = PostForm(request.POST or None,
                        files=request.FILES or None,)
        if form.is_valid():
            new_post = form.save(commit=False)
            new_post.author = request.user
            new_post.save()
            return redirect('posts:profile', request.user.username)

    template = 'posts/create_post.html'
    form = PostForm(request.POST or None,
                    files=request.FILES or None,)
    context = {
        'form': form,
    }
    return render(request, template, context)


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if request.user != post.author:
        return redirect('posts:post_detail', post_id)
    form = PostForm(instance=post)

    if request.method == 'POST':
        form = PostForm(request.POST or None,
                        files=request.FILES or None,
                        instance=post)
        if form.is_valid():
            form.save()
            return redirect('posts:post_detail', post_id)

    template = 'posts/create_post.html'
    context = {
        'form': form,
        'is_edit': True,
        'post_id': post_id
    }
    return render(request, template, context)


def paginator(request, post_list, LIMIT_POSTS):
    paginator = Paginator(post_list, LIMIT_POSTS)
    page_number = request.GET.get('page')

    return paginator.get_page(page_number)


@login_required
def add_comment(request, post_id):
    post_instance = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post_instance
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    post_list = Post.objects.filter(
        author__following__user=request.user
    ).select_related('author', 'group')
    template = 'posts/follow.html'
    page_obj = paginator(request, post_list, LIMIT_POSTS)

    context = {
        'page_obj': page_obj,
    }
    return render(request, template, context)


@login_required
def profile_follow(request, username):
    follower = request.user
    followed = User.objects.get(username=username)
    subscribed_author = Follow.objects.filter(user=follower, author=followed)
    if follower == followed:
        return redirect('posts:profile', username=username)
    if not subscribed_author:
        Follow.objects.create(user=follower, author=followed)
    return redirect('posts:profile', username=username)


@login_required
def profile_unfollow(request, username):
    follower = request.user
    followed = User.objects.get(username=username)
    Follow.objects.get(user=follower, author=followed).delete()
    return redirect('posts:index')
