import shutil
import tempfile
import random
from django.contrib.auth import get_user_model
from ..forms import PostForm, CommentForm
from ..models import Group, Post, Comment
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile


User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='system')
        cls.group = Group.objects.create(
            title='Тестовая группа про самолёты',
            slug='airplane',
            description='Описание новой группы про самолёты!',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            group=cls.group,
            text='Тестовый текст поста про самолёты!',
        )
        cls.form = PostForm()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_create_post(self):
        """Валидная форма создает запись в Post."""
        post_count = Post.objects.count()

        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )

        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )

        form_data = {
            'text': 'Тестовый пост про самолёты!',
            'group': self.group.id,
            'author': self.user.username,
            'image': uploaded,
        }

        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
        )

        self.assertRedirects(response, reverse(
            'posts:profile',
            kwargs={'username': self.user.username}))
        self.assertEqual(Post.objects.count(), post_count + 1)
        self.assertTrue(
            Post.objects.filter(
                text='Тестовый пост про самолёты!',
                group=self.group.id,
                author=self.user.id,
                image='posts/small.gif',
            ).exists()
        )

    def test_edit_post(self):
        """Валидная форма редактирует запись в Post."""
        random_post = random.choice(list(Post.objects.values('id').all()))
        random_post_id = random_post['id']
        self.authorized_client.get(
            reverse('posts:post_edit', kwargs={'post_id': random_post_id}))

        form_data = {
            'text': 'Тестовый текст поста про самолёты!!!!',
            'group': self.group.id,
            'author': self.user.username,
        }
        changed_text = form_data['text']

        self.authorized_client.post(
            reverse('posts:post_edit',
                    kwargs={'post_id': random_post_id}), form_data
        )

        changed_random_post = Post.objects.get(id=random_post_id)
        self.assertEqual(changed_random_post.text, changed_text)
        self.assertTrue(
            Post.objects.filter(
                text=changed_text,
                group=self.group.id,
                author=self.user.id,
            ).exists()
        )


class CommentCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='system')
        cls.group = Group.objects.create(
            title='Тестовая группа про самолёты',
            slug='airplane',
            description='Описание новой группы про самолёты!',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            group=cls.group,
            text='Тестовый текст поста про самолёты!',
        )
        cls.form_post = PostForm()
        cls.comment = Comment.objects.create(
            text='Очень интересный пост я прокомментировал!',
            author=cls.user,
            post=cls.post,
        )
        cls.form_comment = CommentForm()

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_create_comment(self):
        """Валидная форма создает запись в Comment."""
        comment_count = Comment.objects.count()

        random_post = random.choice(list(Post.objects.values('id').all()))
        random_post_id = random_post['id']

        form_data = {
            'text': 'А это второй комментарий под интересным постом!',
            'author': self.user.username,
            'post': random_post_id
        }

        response = self.authorized_client.post(
            reverse('posts:add_comment',
                    kwargs={'post_id': random_post_id}), data=form_data
        )

        self.assertRedirects(response, reverse(
            'posts:post_detail',
            kwargs={'post_id': random_post_id}))
        self.assertEqual(Comment.objects.count(), comment_count + 1)
        self.assertTrue(
            Comment.objects.filter(
                text='А это второй комментарий под интересным постом!',
                author=self.user.id,
                post=random_post_id,
            ).exists()
        )
