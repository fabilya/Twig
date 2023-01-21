from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
import shutil
import tempfile

from ..models import Post, User, Group, Comment
from ..forms import PostForm

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='Ilya')
        cls.group = Group.objects.create(
            title='test-title',
            slug='slug-title',
        )
        Post.objects.create(
            text='Тестовый текст',
            author=cls.user,
            group=cls.group
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
        posts_count = Post.objects.count()
        """Валидная форма создает запись в Post."""
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
            'text': 'Тестовый текст',
            'image': uploaded,
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse(
            'posts:profile', kwargs={'username': 'Ilya'}))
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertTrue(
            Post.objects.filter(
                text='Тестовый текст',
                image='posts/small.gif'
            ).exists()
        )

    def test_post_edit(self):
        """Валидная форма редактирования поста
        не создает новую запись в Post."""
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Измененный текст поста',
            'group': '1'
        }
        self.authorized_client.post(
            reverse('posts:post_edit', args='1'),
            data=form_data,
            follow=True
        )
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertTrue(
            Post.objects.filter(
                text='Измененный текст поста',
                group='1'
            ).exists()
        )

    def test_post_edit2(self):
        """Валидная форма редактирования поста
        неавторизованного пользователя не может изменить БД"""
        form_data = {
            'text': 'Измененный текст поста',
            'group': '1'
        }
        self.guest_client.post(
            reverse('posts:post_edit', args='1'),
            data=form_data,
            follow=True
        )
        self.assertFalse(
            Post.objects.filter(
                text='Измененный текст поста',
                group='1'
            ).exists()
        )

    def test_comment_post_with_authorized_client(self):
        comments_count = Comment.objects.count()
        """Валидная форма создает комментарий"""
        form_data = {
            'text': 'Тестовый комментарий',
        }
        self.authorized_client.post(
            reverse('posts:add_comment', args='1'),
            data=form_data,
        )
        self.assertEqual(Comment.objects.count(), comments_count + 1)
        self.assertTrue(
            Comment.objects.filter(
                text='Тестовый комментарий',
            ).exists()
        )

    def test_comment_post_with_guest_client(self):
        comments_count = Comment.objects.count()
        """Валидная форма создает комментарий"""
        form_data = {
            'text': 'Тестовый комментарий',
        }
        self.guest_client.post(
            reverse('posts:add_comment', args='1'),
            data=form_data,
        )
        self.assertEqual(Comment.objects.count(), comments_count)
        self.assertFalse(
            Comment.objects.filter(
                text='Тестовый комментарий',
            ).exists()
        )

    def test_new_profile(self):
        users_count = User.objects.count()
        """Валидная форма создает запись в User."""
        form_data = {
            'first_name': 'Sergey',
            'last_name': 'Ivanov',
            'username': 'SEREGA',
            'email': 'serega@yandex.ru',
            'password1': '1QweR432!',
            'password2': '1QweR432!'
        }
        self.guest_client.post(
            reverse('users:signup'),
            data=form_data,
            follow=True
        )
        self.assertEqual(User.objects.count(), users_count + 1)
