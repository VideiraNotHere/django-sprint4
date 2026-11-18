from django import forms
from django.contrib.auth import get_user_model

from .models import Comment, Post

User = get_user_model()


class PostForm(forms.ModelForm):
    """Форма создания и редактирования публикации."""

    class Meta:
        model = Post
        exclude = ('author',)
        widgets = {
            'pub_date': forms.DateTimeInput(
                format='%Y-%m-%dT%H:%M',
                attrs={'type': 'datetime-local'},
            ),
        }


class CommentForm(forms.ModelForm):
    """Форма добавления и редактирования комментария."""

    class Meta:
        model = Comment
        fields = ('text',)


class UserEditForm(forms.ModelForm):
    """Форма редактирования профиля пользователя."""

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'username', 'email')
