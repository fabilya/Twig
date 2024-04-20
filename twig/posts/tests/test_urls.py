from http import HTTPStatus
from http.client import OK

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase, Client
from django.urls import reverse

from ..models import Post, Group

User = get_user_model()


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='Ilya')
        cls.group = Group.objects.create(
            title='Басни',
            slug='basni',
            description='Тут будут басни'
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый текст'
        )

    def setUp(self):
        cache.clear()
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_urls_exists_at_desired_location(self):
        """Страницы / доступны любому пользователю."""
        url_for_guest = {
            '/': OK,
            '/group/basni/': OK,
            '/profile/Ilya/': OK,
            '/posts/1/': OK
        }

        for url, code in url_for_guest.items():
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, code)

        response = self.authorized_client.get(reverse(
            'posts:post_edit',
            args=[self.post.pk])
        )
        response_create = self.authorized_client.get(reverse(
            'posts:post_create')
        )
        self.assertEqual(response.status_code, OK)
        self.assertEqual(response_create.status_code, OK)

    def test_task_list_url_redirect_anonymous_on_admin_login(self):
        """Страницы по адресу перенаправит анонимного
        пользователя на страницу логина.
        """
        response_edit = self.guest_client.get('/posts/1/edit/', follow=True)
        response_create = self.guest_client.get('/create/', follow=True)
        self.assertRedirects(response_edit, '/auth/login/?next=/posts/1/edit/')
        self.assertRedirects(response_create, '/auth/login/?next=/create/')

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = {
            '/': 'posts/index.html',
            '/group/basni/': 'posts/group_list.html',
            '/profile/Ilya/': 'posts/profile.html',
            '/posts/1/': 'posts/post_detail.html',
            '/posts/1/edit/': 'posts/create_post.html',
            '/create/': 'posts/create_post.html',
        }
        for url, templates in templates_url_names.items():
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertTemplateUsed(response, templates)

    def test_custom_page_404(self):
        """Проверяет, что ошибка 404 вызывает кастомный шаблон"""
        response = self.guest_client.get('/404/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND.value)
        self.assertTemplateUsed(response, 'core/404.html')
