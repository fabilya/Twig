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
        cache.clear()
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

    def additional_test(self, request, parameter=False):
        if parameter is False:
            post = request.context['page_obj'][0]
        else:
            post = request.context['post']
        context = {
            post.text: self.post.text,
            post.pub_date: self.post.pub_date,
            post.author.username: self.post.author.username,
            post.group.title: self.post.group.title,
        }
        for expected, real in context.items():
            with self.subTest(expected=expected):
                self.assertEqual(expected, real)

    def test_index_page_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        self.additional_test(self.authorized_client.get(
            reverse('posts:index')))

    def test_group_list_page_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        self.additional_test(self.authorized_client.get(
            reverse('posts:group_list', args=[self.group.slug])))

    def test_profile_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        self.additional_test(self.authorized_client.get(
            reverse('posts:profile', args=[self.user.username])))

    def test_post_detail_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        self.additional_test(self.authorized_client.get(
            reverse('posts:post_detail', args=[self.post.pk])), parameter=True)

    def test_paginator(self):
        bulk_list = []
        for i in range(13):
            bulk_list.append(Post(
                text=f'Текст {i}',
                author=self.user,
                group=self.group,
            ))
        Post.objects.bulk_create(bulk_list)
        adresses = (
            ('posts:index', None),
            ('posts:group_list', self.group.slug),
            ('posts:profile', self.user.username),
        )
        number_of_posts_in_page = (
            ('?page=1', 10),
            ('?page=2', 4)
        )
        for adress, argument in adresses:
            with self.subTest(adress=adress):
                if argument is None:
                    for page, number in number_of_posts_in_page:
                        with self.subTest(page=page):
                            response = self.client.get(reverse(adress) + page)
                            self.assertEqual(
                                len(response.context['page_obj']), number)
                else:
                    for page, number in number_of_posts_in_page:
                        with self.subTest(page=page):
                            response = self.client.get(reverse(
                                adress, args=[argument]) + page)
                            self.assertEqual(
                                len(response.context['page_obj']), number)


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
        cache.clear()
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
        self.assertEqual(len(
            response_index.context['page_obj'].object_list), 2)
        self.assertEqual(len(
            response_group.context['page_obj'].object_list), 1)
        self.assertEqual(len(
            response_profile.context['page_obj'].object_list), 1)
        self.assertEqual(len(
            response_another_group.context['page_obj'].object_list), 0)


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
        cache.clear()
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def additional_image_context(self, request, parameter=False):
        if parameter is False:
            post = request.context['page_obj'][0]
        else:
            post = request.context['post']
        context = {
            post.image: self.post.image
        }
        for expected, real in context.items():
            with self.subTest(expected=expected):
                self.assertEqual(expected, real)

    def test_image_index_show_correct_context(self):
        self.additional_image_context(self.guest_client.get(
            reverse('posts:index')))

    def test_image_group_list_show_correct_context(self):
        self.additional_image_context(self.guest_client.get(
            reverse('posts:group_list', args=[self.group.slug])))

    def test_image_profile_show_correct_context(self):
        self.additional_image_context(self.guest_client.get(
            reverse('posts:profile', args=[self.user.username])))

    def test_image_post_detail_show_correct_context(self):
        self.additional_image_context(self.guest_client.get(
            reverse('posts:post_detail', args=[self.post.pk])), parameter=True)


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
        self.assertTrue(response_il_john.context.get('following'))
        resp = self.authorized_client.get(reverse('posts:follow_index'))
        self.assertEqual(resp.context.get('page_obj')[0].text, 'Testing text')
        self.assertFalse(response_il_adele.context.get('following'))
        self.assertNotIn('Adele text', resp.context.get('page_obj')[0].text)
