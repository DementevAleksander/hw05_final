from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import Group, Post

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа!',
            slug='airplane',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='1234567891123456789! Тестовая пост более 15 символов!',
        )

    def test_models_have_correct_object_names_for_post(self):
        """Проверяем, что у моделей корректно работает __str__ для post."""
        post = PostModelTest.post
        expected_post_str = post.text[:15]
        self.assertEqual(expected_post_str, str(post))

    def test_models_have_correct_object_names_for_group(self):
        """Проверяем, что у моделей корректно работает __str__ для group."""
        group = PostModelTest.group
        expected_group_str = group.title
        self.assertEqual(expected_group_str, str(group))

    def test_verbose_name(self):
        """verbose_name в полях совпадает с ожидаемым."""
        post = PostModelTest.post
        field_verboses = {
            'text': 'Пост',
        }
        for field, expected_value in field_verboses.items():
            with self.subTest(field=field):
                self.assertEqual(
                    post._meta.get_field(field).verbose_name, expected_value)

    def test_help_text(self):
        """help_text в полях совпадает с ожидаемым."""
        post = PostModelTest.post
        field_help_texts = {
            'text': 'Введите текст поста',
        }
        for field, expected_value in field_help_texts.items():
            with self.subTest(field=field):
                self.assertEqual(
                    post._meta.get_field(field).help_text, expected_value)
