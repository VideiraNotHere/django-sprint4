from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import CommentForm, PostForm, UserEditForm
from .models import Category, Comment, Post

User = get_user_model()

POSTS_PER_PAGE = 10


def get_posts_queryset(
    manager=Post.objects,
    filter_published=True,
    annotate_comments=True,
):
    """Формирует queryset постов с фильтрацией и подсчётом комментариев."""
    queryset = manager.select_related('author', 'location', 'category')
    if filter_published:
        queryset = queryset.filter(
            is_published=True,
            pub_date__lte=timezone.now(),
            category__is_published=True,
        )
    if annotate_comments:
        queryset = queryset.annotate(
            comment_count=Count('comments')
        ).order_by('-pub_date')
    return queryset


def paginate_posts(request, queryset, per_page=POSTS_PER_PAGE):
    """Возвращает объект страницы пагинатора."""
    paginator = Paginator(queryset, per_page)
    page_number = request.GET.get('page')
    return paginator.get_page(page_number)


def index(request):
    """Главная страница со списком опубликованных постов."""
    post_list = get_posts_queryset()
    page_obj = paginate_posts(request, post_list)
    return render(request, 'blog/index.html', {'page_obj': page_obj})


def post_detail(request, post_id):
    """Страница отдельной публикации и её комментариев."""
    post = get_object_or_404(
        get_posts_queryset(
            filter_published=False,
            annotate_comments=False,
        ),
        pk=post_id,
    )
    if post.author != request.user:
        post = get_object_or_404(
            get_posts_queryset(
                filter_published=True,
                annotate_comments=False,
            ),
            pk=post_id,
        )
    form = CommentForm()
    comments = post.comments.select_related('author')
    context = {
        'post': post,
        'form': form,
        'comments': comments,
    }
    return render(request, 'blog/detail.html', context)


def category_posts(request, category_slug):
    """Страница выбранной категории."""
    category = get_object_or_404(
        Category,
        slug=category_slug,
        is_published=True,
    )
    post_list = get_posts_queryset(manager=category.posts)
    page_obj = paginate_posts(request, post_list)
    context = {
        'category': category,
        'page_obj': page_obj,
    }
    return render(request, 'blog/category.html', context)


def profile(request, username):
    """Страница профиля пользователя с его публикациями."""
    profile_user = get_object_or_404(User, username=username)
    filter_published = request.user != profile_user
    post_list = get_posts_queryset(
        manager=profile_user.posts,
        filter_published=filter_published,
    )
    page_obj = paginate_posts(request, post_list)
    context = {
        'profile': profile_user,
        'page_obj': page_obj,
    }
    return render(request, 'blog/profile.html', context)


@login_required
def edit_profile(request):
    """Страница редактирования профиля текущего пользователя."""
    form = UserEditForm(request.POST or None, instance=request.user)
    if form.is_valid():
        form.save()
        return redirect('blog:profile', username=request.user.username)
    return render(request, 'blog/user.html', {'form': form})


@login_required
def create_post(request):
    """Страница создания новой публикации."""
    form = PostForm(request.POST or None, files=request.FILES or None)
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('blog:profile', username=request.user.username)
    return render(request, 'blog/create.html', {'form': form})


def edit_post(request, post_id):
    """Страница редактирования публикации (доступна только автору)."""
    post = get_object_or_404(Post, pk=post_id)
    if post.author != request.user:
        return redirect('blog:post_detail', post_id=post_id)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post,
    )
    if form.is_valid():
        form.save()
        return redirect('blog:post_detail', post_id=post_id)
    return render(request, 'blog/create.html', {'form': form})


@login_required
def delete_post(request, post_id):
    """Страница подтверждения и удаления публикации."""
    post = get_object_or_404(Post, pk=post_id)
    if post.author != request.user:
        return redirect('blog:post_detail', post_id=post_id)
    form = PostForm(instance=post)
    if request.method == 'POST':
        post.delete()
        return redirect('blog:profile', username=request.user.username)
    return render(
        request,
        'blog/create.html',
        {'form': form, 'post': post},
    )


@login_required
def add_comment(request, post_id):
    """Добавление комментария к публикации."""
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('blog:post_detail', post_id=post_id)


@login_required
def edit_comment(request, post_id, comment_id):
    """Редактирование собственного комментария."""
    comment = get_object_or_404(Comment, pk=comment_id, post_id=post_id)
    if comment.author != request.user:
        return redirect('blog:post_detail', post_id=post_id)
    form = CommentForm(request.POST or None, instance=comment)
    if form.is_valid():
        form.save()
        return redirect('blog:post_detail', post_id=post_id)
    return render(
        request,
        'blog/comment.html',
        {'form': form, 'comment': comment},
    )


@login_required
def delete_comment(request, post_id, comment_id):
    """Удаление собственного комментария."""
    comment = get_object_or_404(Comment, pk=comment_id, post_id=post_id)
    if comment.author != request.user:
        return redirect('blog:post_detail', post_id=post_id)
    if request.method == 'POST':
        comment.delete()
        return redirect('blog:post_detail', post_id=post_id)
    return render(
        request,
        'blog/comment.html',
        {'comment': comment},
    )
