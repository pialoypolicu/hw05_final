import shutil
import tempfile

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Comment, Group, Post, User


class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        settings.MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
        cls.user = User.objects.create_user(username='Sasha')
        cls.group = Group.objects.create(
            title='Бизнес',
            slug='business',
            description='Для публикации офферов',
        )
        cls.test_post = Post.objects.create(
            text='Breaking bad',
            author=cls.user,
            group=cls.group,
        )

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_create_new_post(self):
        """
        Создаем новый пост.
        Переходим на главную страницу.
        Сверяем созданые поля.
        """
        total_posts = Post.objects.count()
        form_data = {
            'text': 'Крафтовый сыыыр',
            'group': self.group.id,
        }
        response = self.authorized_client.post(
            reverse('new_post'),
            data=form_data,
            follow=True
        )
        post = Post.objects.first()
        self.assertEqual(post.text, form_data['text'])
        self.assertEqual(post.author, self.user)
        self.assertEqual(post.group.id, form_data['group'])
        self.assertRedirects(response, reverse('index'))
        self.assertEqual(Post.objects.count(), total_posts + 1)

    def test_after_post_edit_shange(self):
        """Проверяем происходит ли редактирование поста"""
        post = Post.objects.create(
            text='Тестовый заголовок',
            author=self.user,
            group=self.group,
        )
        data_form = {
            'text': '777 Тестовый заголовок 777',
            'group': self.group.id
        }
        self.authorized_client.post(reverse('post_edit', kwargs={
            'username': post.author, 'post_id': post.id
        }), data=data_form, follow=True)
        post = Post.objects.first()
        self.assertEqual(post.text, data_form['text'])
        self.assertEqual(post.author, self.user)
        self.assertEqual(post.group.id, data_form['group'])

    def test_not_create_new_post(self):
        """Проверяем, что пост не создан не авторизованным юзером."""
        total_posts_before_create = Post.objects.count()
        data_form = {
            'text': 'Тестовый заголовок 777',
            'group': self.group.id,
            'author': self.guest_client
        }
        self.guest_client.post(
            reverse('new_post'),
            data=data_form,
            follow=True
        )
        total_posts_after_create = Post.objects.count()
        self.assertEqual(total_posts_before_create, total_posts_after_create)

    def test_context_post_with_image(self):
        """
        Изображение картинки отображается на страницах
        Проверяем, что пост был создан.
        """
        total_posts = Post.objects.count()
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
            'group': self.group.id,
            'image': uploaded,
        }
        self.authorized_client.post(
            reverse('new_post'),
            data=form_data,
            follow=True
        )
        self.assertEqual(Post.objects.count(), total_posts + 1)
        post = Post.objects.first()
        self.assertEqual(
            post.image.open().read(),
            form_data['image'].open().read()
        )

    def test_guest_add_comment(self):
        """Может ли гость оставить комментарий."""
        total_comments = Comment.objects.count()
        data_comment = {
            'post': self.test_post,
            'author': self.guest_client,
            'text': 'тест'
        }
        response = self.guest_client.post(
            reverse('add_comment', args=(
                self.test_post.author,
                self.test_post.id)),
            data=data_comment,
            follow=True)
        after_comment = Comment.objects.count()
        self.assertEqual(total_comments, after_comment)
        self.assertRedirects(
            response,
            reverse('login') + '?next=' + reverse(
                'add_comment',
                args=(self.test_post.author, self.test_post.id)))

    def test_auth_user_add_comment(self):
        """Может ли авторизованный юзер оставить комментарий."""
        total_comments = Comment.objects.count()
        data_comment = {
            'post': self.test_post,
            'author': self.user,
            'text': 'тест'
        }
        response = self.authorized_client.post(
            reverse('add_comment', args=(
                self.test_post.author,
                self.test_post.id)),
            data=data_comment,
            follow=True)
        after_comment = Comment.objects.count()
        self.assertNotEqual(total_comments, after_comment)
        self.assertRedirects(
            response,
            reverse('post', args=(self.test_post.author, self.test_post.id)))
        post = Comment.objects.first()
        self.assertEqual(post.post, data_comment['post'])
        self.assertEqual(post.author, data_comment['author'])
        self.assertEqual(post.text, data_comment['text'])
