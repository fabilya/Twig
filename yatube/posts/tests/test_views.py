import datetime
import shutil
import tempfile
from django.conf import settings

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django import forms

from ..models import Post, Group, Follow

User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='Ilya')
        cls.group = Group.objects.create(
            title='test-title',
            slug='test-slug',
            description='test-description',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='text-example',
            group=cls.group,
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_list',
                    kwargs={'slug': 'test-slug'}): 'posts/group_list.html',
            reverse('posts:profile',
                    kwargs={'username': 'Ilya'}): 'posts/profile.html',
            reverse('posts:post_detail',
                    kwargs={'post_id': '1'}): 'posts/post_detail.html',
            reverse('posts:post_edit',
                    kwargs={'post_id': '1'}): 'posts/create_post.html',
            reverse('posts:post_create'): 'posts/create_post.html'
        }
        for reverse_name, templates in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, templates)

    def test_post_create_page_show_correct_context(self):
        """Шаблон create_post, edit сформированы с правильным контекстом."""
        response_create = self.authorized_client.get(
            reverse('posts:post_create')
        )
        response_edit = self.authorized_client.get(
            reverse('posts:post_edit', kwargs={'post_id': '1'})
        )
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field_create = (response_create.context.get(
                    'form').fields.get(value))
                form_field_edit = (response_edit.context.get(
                    'form').fields.get(value))
                self.assertIsInstance(form_field_create, expected)
                self.assertIsInstance(form_field_edit, expected)

    def test_post_detail_page_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse(
            'posts:post_detail', kwargs={'post_id': '1'}))
        self.assertEqual(response.context.get('post').text, 'text-example')
        self.assertEqual(response.context.get(
            'post').pub_date.date(), datetime.date.today())
        self.assertEqual(response.context.get(
            'post').author.username, 'Ilya')
        self.assertEqual(response.context.get(
            'post').group.title, 'test-title')

    def test_index_page_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:index'))
        first_object = response.context['page_obj'][0]
        post_text_0 = first_object.text
        post_pub_date_0 = first_object.pub_date.date()
        post_author_0 = first_object.author.username
        post_group_0 = first_object.group.title
        index_context = {
            post_text_0: 'text-example',
            post_pub_date_0: datetime.date.today(),
            post_author_0: 'Ilya',
            post_group_0: 'test-title'
        }
        for expected, real in index_context.items():
            with self.subTest(expected=expected):
                self.assertEqual(expected, real)

    def test_group_list_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': 'test-slug'}))
        first_object = response.context['page_obj'][0]
        post_text_0 = first_object.text
        post_pub_date_0 = first_object.pub_date.date()
        post_author_0 = first_object.author.username
        post_group_0 = first_object.group.title
        self.assertEqual(post_text_0, 'text-example')
        self.assertEqual(post_pub_date_0, datetime.date.today())
        self.assertEqual(post_author_0, 'Ilya')
        self.assertEqual(post_group_0, 'test-title')

    def test_profile_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:profile', kwargs={'username': 'Ilya'}))
        first_object = response.context['page_obj'][0]
        post_text_0 = first_object.text
        post_pub_date_0 = first_object.pub_date.date()
        post_author_0 = first_object.author.username
        post_group_0 = first_object.group.title
        self.assertEqual(post_text_0, 'text-example')
        self.assertEqual(post_pub_date_0, datetime.date.today())
        self.assertEqual(post_author_0, 'Ilya')
        self.assertEqual(post_group_0, 'test-title')


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='Ilya')
        cls.group = Group.objects.create(
            title='test-title',
            slug='test-slug',
            description='test-description',
        )
        cls.post1 = Post.objects.create(
            author=cls.user,
            text='text-example1',
        )
        cls.post2 = Post.objects.create(
            author=cls.user,
            text='text-example2',
            group=cls.group,
        )
        cls.post3 = Post.objects.create(
            author=cls.user,
            text='text-example3',
            group=cls.group,
        )
        cls.post4 = Post.objects.create(
            author=cls.user,
            text='text-example4',
            group=cls.group,
        )
        cls.post5 = Post.objects.create(
            author=cls.user,
            text='text-example5',
            group=cls.group,
        )
        cls.post6 = Post.objects.create(
            author=cls.user,
            text='text-example6',
            group=cls.group,
        )
        cls.post7 = Post.objects.create(
            author=cls.user,
            text='text-example7',
        )
        cls.post8 = Post.objects.create(
            author=cls.user,
            text='text-example8',
            group=cls.group,
        )
        cls.post9 = Post.objects.create(
            author=cls.user,
            text='text-example9',
            group=cls.group,
        )
        cls.post10 = Post.objects.create(
            author=cls.user,
            text='text-example10',
            group=cls.group,
        )
        cls.post11 = Post.objects.create(
            author=cls.user,
            text='text-example11',
            group=cls.group,
        )
        cls.post12 = Post.objects.create(
            author=cls.user,
            text='text-example12',
            group=cls.group,
        )
        cls.post13 = Post.objects.create(
            author=cls.user,
            text='text-example13',
            group=cls.group,
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_first_page_contains_ten_records(self):
        response_index = self.client.get(reverse('posts:index'))
        response_group = self.client.get(reverse(
            'posts:group_list', kwargs={'slug': 'test-slug'}))
        response_profile = self.client.get(reverse(
            'posts:profile', kwargs={'username': 'Ilya'}))
        self.assertEqual(len(response_index.context['page_obj']), 10)
        self.assertEqual(len(response_group.context['page_obj']), 10)
        self.assertEqual(len(response_profile.context['page_obj']), 10)

    def test_second_page_contains_n_records(self):
        response_index = self.client.get(reverse('posts:index') + '?page=2')
        response_group = self.client.get(reverse(
            'posts:group_list', kwargs={'slug': 'test-slug'}) + '?page=2')
        response_profile = self.client.get(reverse(
            'posts:profile', kwargs={'username': 'Ilya'}) + '?page=2')
        self.assertEqual(len(response_index.context['page_obj']), 3)
        self.assertEqual(len(response_group.context['page_obj']), 1)
        self.assertEqual(len(response_profile.context['page_obj']), 3)


class AdditionalTestCreatePost(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user1 = User.objects.create_user(username='Fedya')
        cls.user2 = User.objects.create_user(username='Vasya')
        cls.group1 = Group.objects.create(
            title='test-title1',
            slug='test-slug1',
            description='test-description1',
        )
        cls.group2 = Group.objects.create(
            title='test-title2',
            slug='test-slug2',
            description='test-description1',
        )
        cls.post1 = Post.objects.create(
            author=cls.user1,
            text='text-example1',
        )
        cls.post2 = Post.objects.create(
            author=cls.user2,
            text='text-example2',
            group=cls.group1,
        )

    def setUp(self):
        self.authorized_client = Client()

    def test_create_another_post_with_group(self):
        """
        Проверяет, что если при создании поста указать группу,
        то этот пост появляется:
        - на главной странице сайта
        - на странице выбранной группы
        - в профайле пользователя
        """
        response_index = self.authorized_client.get(reverse('posts:index'))
        response_group = self.authorized_client.get(reverse(
            'posts:group_list', kwargs={'slug': 'test-slug1'}))
        response_profile = self.authorized_client.get(reverse(
            'posts:profile', kwargs={'username': 'Vasya'}))
        response_another_group = self.authorized_client.get(reverse(
            'posts:group_list', kwargs={'slug': 'test-slug2'}))
        self.assertEqual(len(response_index.context.get(
            'page_obj').object_list), 2)
        self.assertEqual(len(response_group.context.get(
            'page_obj').object_list), 1)
        self.assertEqual(len(response_profile.context.get(
            'page_obj').object_list), 1)
        self.assertEqual(len(response_another_group.context.get(
            'page_obj').object_list), 0)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostWithImage(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='Ilya')
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.image = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        cls.group = Group.objects.create(
            title='test-title',
            slug='test-slug',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='text-example',
            group=cls.group,
            image=cls.image
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_image_context(self):
        response_index = self.guest_client.get(
            reverse('posts:index')
        )
        response_profile = self.guest_client.get(
            reverse('posts:profile',
                    kwargs={'username': 'Ilya'})
        )
        response_group = self.guest_client.get(
            reverse('posts:group_list',
                    kwargs={'slug': 'test-slug'})
        )
        response_post_detail = self.guest_client.get(
            reverse('posts:post_detail',
                    kwargs={'post_id': '1'})
        )

        index = response_index.context['page_obj'][0]
        profile = response_profile.context['page_obj'][0]
        group = response_group.context['page_obj'][0]
        detail = response_post_detail.context['post']

        post_img = index.image.name
        post_profile = profile.image.name
        post_group = group.image.name
        post_detail = detail.image.name

        self.assertEqual(post_img, 'posts/small.gif')
        self.assertEqual(post_profile, 'posts/small.gif')
        self.assertEqual(post_group, 'posts/small.gif')
        self.assertEqual(post_detail, 'posts/small.gif')


class IndexPostListCache(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='Ilya')
        cls.post1 = Post.objects.create(
            author=cls.user,
            text='text-example1',
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_cache(self):
        """Тестирование кэша на главной странице"""
        response = self.guest_client.get(reverse('posts:index'))
        Post.objects.filter(pk=1).delete()
        response2 = self.guest_client.get(reverse('posts:index'))
        self.assertEqual(response.content, response2.content)
        cache.clear()
        response3 = self.guest_client.get(reverse('posts:index'))
        self.assertNotEqual(response.content, response3.content)


class FollowTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='Ilya')
        cls.user2 = User.objects.create_user(username='John')
        cls.user3 = User.objects.create_user(username='Adele')
        cls.follow = Follow.objects.create(
            user=cls.user,
            author=cls.user2,
        )
        cls.post = Post.objects.create(
            text='Testing text',
            author=cls.user2,
        )
        cls.post2 = Post.objects.create(
            text='Adele text',
            author=cls.user3,
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_follow_auth_user(self):
        """Авторизованный пользователь может подписываться на других
        пользователей и удалять их из подписок."""
        response = self.authorized_client.get(
            reverse(
                'posts:profile',
                kwargs={'username': 'John'}
            )
        )
        self.assertTrue(response.context.get('following'))
        self.authorized_client.get(
            reverse(
                'posts:profile_unfollow',
                kwargs={'username': 'John'}
            )
        )
        response_unfollow = self.authorized_client.get(
            reverse(
                'posts:profile',
                kwargs={'username': 'John'}
            )
        )
        self.assertFalse(response_unfollow.context.get('following'))

    def test_new_post_in_follower_user(self):
        """Новая запись пользователя появляется в ленте тех,
        кто на него подписан и не появляется в ленте тех, кто не подписан."""
        response_il_john = self.authorized_client.get(
            reverse(
                'posts:profile',
                kwargs={'username': 'John'}
            )
        )
        response_il_adele = self.authorized_client.get(
            reverse(
                'posts:profile',
                kwargs={'username': 'Adele'}
            )
        )
        # Проверяем, что Илья подписан на Джона
        self.assertTrue(response_il_john.context.get('following'))
        resp = self.authorized_client.get(reverse('posts:follow_index'))
        # Проверяем, что с таким текстом, в ленте подписок есть пост Джона
        self.assertEqual(resp.context.get('page_obj')[0].text, 'Testing text')
        # Проверяем, что Илья НЕ подписан на Адель
        self.assertFalse(response_il_adele.context.get('following'))
        # Проверяем, что поста Адель с таким текстом, нет в ленте подписок Ильи
        self.assertNotIn('Adele text', resp.context.get('page_obj')[0].text)

