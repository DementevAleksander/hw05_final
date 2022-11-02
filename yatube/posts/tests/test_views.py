from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django import forms
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
import tempfile
import shutil
from django.conf import settings
from ..models import Group, Post, Follow

User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='system')
        cls.group = Group.objects.create(
            title='Тестовая группа про самолёты',
            slug='airplane',
            description='Описание новой группы про самолёты!',
        )
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
        cls.post = Post.objects.create(
            author=cls.user,
            group=cls.group,
            text='Тестовый текст поста про самолёты!',
            image=uploaded,
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        cache.clear()
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        reverse_index = reverse('posts:index')
        reverse_group_list = reverse(
            'posts:group_list', kwargs={'slug': self.group.slug})
        reverse_profile = reverse(
            'posts:profile', kwargs={'username': self.user.username})
        reverse_post_detail = reverse(
            'posts:post_detail', kwargs={'post_id': self.post.id})
        reverse_post_create = reverse(
            'posts:post_create')
        reverse_post_edit = reverse(
            'posts:post_edit', kwargs={'post_id': self.post.id})

        templates_pages_names = {
            reverse_index: 'posts/index.html',
            reverse_group_list: 'posts/group_list.html',
            reverse_profile: 'posts/profile.html',
            reverse_post_detail: 'posts/post_detail.html',
            reverse_post_create: 'posts/create_post.html',
            reverse_post_edit: 'posts/create_post.html',
        }

        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_page_show_correct_context(self):
        """Шаблон index.html сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:index'))
        first_object = response.context['page_obj'][0]
        self.assertEqual(first_object.text,
                         'Тестовый текст поста про самолёты!')
        self.assertEqual(first_object.group.title,
                         'Тестовая группа про самолёты')
        self.assertEqual(first_object.image,
                         'posts/small.gif')

    def test_group_list_correct_context(self):
        """Шаблон group_list.html сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:group_list',
                    kwargs={'slug': self.group.slug}))
        first_object = response.context['page_obj'][0]
        self.assertEqual(first_object.text,
                         'Тестовый текст поста про самолёты!')
        self.assertEqual(first_object.group.title,
                         'Тестовая группа про самолёты')
        self.assertEqual(first_object.image,
                         'posts/small.gif')

    def test_profile_list_page_show_correct_context(self):
        """Шаблон profile.html сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:profile',
                                              kwargs={'username': 'system'}))
        first_object = response.context['page_obj'][0]
        self.assertEqual(first_object.author, self.post.author)
        self.assertEqual(first_object.text, self.post.text)
        self.assertEqual(first_object.group.title,
                         'Тестовая группа про самолёты')
        self.assertEqual(first_object.image,
                         'posts/small.gif')

    def test_post_detail_list_page_show_correct_context(self):
        """Шаблон post_detail.html сформирован с правильным контекстом."""
        response = (self.authorized_client.
                    get(reverse('posts:post_detail',
                        kwargs={'post_id': self.post.id})))
        self.assertEqual(response.context.get('post_list').text,
                         self.post.text)
        self.assertEqual(response.context.get('post_list').image,
                         'posts/small.gif')

    def test_post_edit_list_page_show_correct_context(self):
        """Шаблон create_post.html редактирование поста
            сформирован с правильным контекстом.
        """
        response = (self.authorized_client.
                    get(reverse('posts:post_edit',
                        kwargs={'post_id': self.post.id})))

        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }

        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_create_post_list_page_show_correct_context(self):
        """Шаблон create_post.html создание поста
            сформирован с правильным контекстом.
        """
        response = (self.authorized_client.
                    get(reverse('posts:post_create')))

        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }

        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='system')
        cls.group = Group.objects.create(
            title='Тестовая группа про самолёты',
            slug='airplane',
            description='Описание новой группы про самолёты!',
        )
        for x in range(14):
            cls.post = Post.objects.create(
                author=cls.user,
                group=cls.group,
                text='Тестовый текст поста про самолёты!',
            )

    def setUp(self):
        cache.clear()
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_index_first_page_contains_ten_records(self):
        """Первая страница index.html сформирована с правильным paginator."""
        response = self.guest_client.get(reverse('posts:index'))
        self.assertEqual(len(response.context['page_obj']), 10)

    def test_index_second_page_contains_four_records(self):
        """Вторая страница index.html сформирована с правильным paginator."""
        response = self.guest_client.get(reverse('posts:index') + '?page=2')
        self.assertEqual(len(response.context['page_obj']), 4)

    def test_group_list_first_page_contains_ten_records(self):
        """Первая страница group_list.html
           сформирована с правильным paginator."""
        response = self.guest_client.get(reverse('posts:group_list',
                                         kwargs={'slug': self.group.slug}))
        self.assertEqual(len(response.context['page_obj']), 10)

    def test_group_list_second_page_contains_four_records(self):
        """Вторая страница group_list.html
           сформирована с правильным paginator."""
        response = self.guest_client.get(reverse('posts:group_list',
                                         kwargs={'slug': self.group.slug})
                                         + '?page=2')
        self.assertEqual(len(response.context['page_obj']), 4)

    def test_profile_first_page_contains_ten_records(self):
        """Первая страница profile.html
           сформирована с правильным paginator."""
        response = self.guest_client.get(reverse('posts:profile',
                                         kwargs={'username': 'system'}))
        self.assertEqual(len(response.context['page_obj']), 10)

    def test_profile_second_page_contains_four_records(self):
        """Вторая страница profile.html
           сформирована с правильным paginator."""
        response = self.guest_client.get(reverse('posts:profile',
                                                 kwargs={'username': 'system'})
                                         + '?page=2')
        self.assertEqual(len(response.context['page_obj']), 4)


# @override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
# class CacheTests(TestCase):
#     @classmethod
#     def setUpClass(cls):
#         super().setUpClass()
#         cls.user = User.objects.create_user(username='system')
#         cls.group = Group.objects.create(
#             title='Тестовая группа про самолёты',
#             slug='airplane',
#             description='Описание новой группы про самолёты!',
#         )
#         small_gif = (
#             b'\x47\x49\x46\x38\x39\x61\x02\x00'
#             b'\x01\x00\x80\x00\x00\x00\x00\x00'
#             b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
#             b'\x00\x00\x00\x2C\x00\x00\x00\x00'
#             b'\x02\x00\x01\x00\x00\x02\x02\x0C'
#             b'\x0A\x00\x3B'
#         )
#         uploaded = SimpleUploadedFile(
#             name='small.gif',
#             content=small_gif,
#             content_type='image/gif'
#         )
#         cls.post = Post.objects.create(
#             author=cls.user,
#             group=cls.group,
#             text='Тестовый текст поста про самолёты!',
#             image=uploaded,
#         )

#     @classmethod
#     def tearDownClass(cls):
#         super().tearDownClass()
#         shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

#     def setUp(self):
#         self.guest_client = Client()
#         self.authorized_client = Client()
#         self.authorized_client.force_login(self.user)

#     def test_cache_index(self):
#         """Тест, проверяющий работу кэширования страницы index.html."""
#         first_state = self.authorized_client.get(reverse('posts:index'))
#         post_for_edit = Post.objects.get(id=self.post.id)
#         post_for_edit.delete()
#         altered_state = self.authorized_client.get(reverse('posts:index'))
#         self.assertEqual(first_state.content, altered_state.content)
#         cache.clear()
#         final_status_state = self.authorized_client.get(
#             reverse('posts:index')
#         )
#         self.assertNotEqual(first_state.content, final_status_state.content)


class FollowTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.followed = User.objects.create_user(username='followed')
        cls.follower = User.objects.create_user(username='follower')
        cls.create_posts = Post.objects.create(text='Пост тест!',
                                               author=cls.followed,)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.follower)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_subscribe_unsubscribe(self):
        """Авторизованный пользователь может подписываться
           на других пользователей и удалять их из подписок."""
        self.authorized_client.get(reverse(
            'posts:profile_follow',
            kwargs={'username': self.followed}))
        self.assertEqual(Follow.objects.count(), 1)

        self.authorized_client.get(reverse(
            'posts:profile_unfollow',
            kwargs={'username': self.followed}))
        self.assertEqual(Follow.objects.count(), 0)

    def test_new_entry_appears_feed(self):
        """Новая запись пользователя появляется в ленте тех, кто
           на него подписан и не появляется в ленте тех, кто не подписан."""
        self.authorized_client.get(reverse(
            'posts:profile_follow',
            kwargs={'username': self.followed}))
        self.assertEqual(Follow.objects.count(), 1)

        followed = Follow.objects.filter(author=self.followed)
        followed_author = followed[0].author
        posts = Post.objects.filter(author=followed_author)
        posts_count = posts.count()
        self.assertEqual(posts_count, 1)
        self.assertEqual(str(posts[0]), 'Пост тест!')

        response = self.authorized_client.get(reverse('posts:follow_index'))
        self.assertContains(response, 'Пост тест!',)

        new_user = User.objects.create_user(username='new_user')
        self.authorized_client = Client()
        self.authorized_client.force_login(new_user)

        response = self.authorized_client.get(reverse('posts:follow_index'))
        self.assertNotContains(response, 'Пост тест!',)
