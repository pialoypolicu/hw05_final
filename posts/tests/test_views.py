import shutil
import tempfile

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Follow, Group, Post
from yatube.settings import POSTS_ON_PAGE

User = get_user_model()


class TaskPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        settings.MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
        cls.test_author = User.objects.create_user(username='Sasha')
        cls.group = Group.objects.create(
            title='Бизнес',
            slug='business',
            description='Для публикации офферов',
        )
        cls.another_group = Group.objects.create(
            title='Сообщество',
            slug='snowball',
            description='Тайное сообщество любителей...'
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
            text='Тестовый заголовок',
            author=cls.test_author,
            group=cls.group,
            image=uploaded
        )
        cls.EXPECTED_TEMPLATES = {
            'index.html': reverse('index'),
            'group.html': reverse('group', kwargs={'slug': cls.group.slug}),
            'new_post.html': reverse('new_post'),
        }

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.user = User.objects.create_user(username='StasBasov')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

        self.authorized_client_sasha = Client()
        self.authorized_client_sasha.force_login(self.test_author)

    def check_context_post(self, context):
        if 'post' in context:
            context_object = context['post']
        else:
            context_object = context['page'][0]
        post_text = context_object.text
        post_author = context_object.author
        post_group = context_object.group
        post_image = context_object.image
        self.assertEqual(post_text, self.post.text)
        self.assertEqual(post_author, self.post.author)
        self.assertEqual(post_group, self.post.group)
        self.assertEqual(post_image, self.post.image)

    def test_index_page_shows_correct_context(self):
        """Проверяем контекст главной страницы."""
        response = self.authorized_client.get(reverse('index'))
        self.check_context_post(response.context)

    def test_group_page_shows_correct_context(self):
        """Шаблон group/slug сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse(
            'group',
            kwargs={'slug': self.group.slug}
        ))
        self.check_context_post(response.context)

    def test_page_username_shows_correct_context(self):
        """шаблон username сформирован с правильным контекстом"""
        response = self.authorized_client.get(
            reverse(
                'profile',
                kwargs={
                    'username': self.post.author.username
                }))
        self.check_context_post(response.context)

    def test_page_post_view_shows_correct_context(self):
        """шаблон post_view сформирован с правильным контекстом"""
        response = self.authorized_client.get(reverse('post', kwargs={
            'username': self.post.author.username,
            'post_id': self.post.id
        }))
        self.check_context_post(response.context)

    def test_pages_use_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        for template, reverse_name in self.EXPECTED_TEMPLATES.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_new_page_shows_correct_context(self):
        """Шаблон new_post сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('new_post'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_new_post_not_in_wrong_group(self):
        """
        Проверяем, что новый пост не отображается
        в смежной группе
        """
        response_another_group = self.authorized_client.get(
            reverse('group', kwargs={
                'slug': self.another_group.slug
            })
        )
        context_paginator = response_another_group.context['page'].paginator
        self.assertEqual(
            context_paginator.count, 0,
            'Пост отображается в смежной группе.'
        )

    def test_posts_on_page(self):
        """Проверка пагинации, выводим верное кол-во постов на странице"""
        for create_post in range(POSTS_ON_PAGE):
            Post.objects.create(
                text=create_post,
                author=self.test_author,
                group=self.group, )
        response_page_one = self.authorized_client.get(reverse('index'))
        total_posts_page_one = len(response_page_one.context['page'])
        self.assertEqual(
            total_posts_page_one,
            POSTS_ON_PAGE,
            'Кол-во постов не совпадает с заданным в паджинаторе'
        )
        response_page_two = self.authorized_client.get(
            reverse('index') + '?page=2'
        )
        expected_posts_page_two = Post.objects.count() - POSTS_ON_PAGE

        self.assertEqual(
            len(response_page_two.context['page']),
            expected_posts_page_two,
            'Кол-во постов не совпадает с заданным в паджинаторе'
        )

    def test_cache_index_page(self):
        """Работает ли кэширование"""
        response = self.authorized_client.get(reverse('index'))
        Post.objects.create(
            text='До сброса кэша',
            author=self.test_author,
            group=self.group,
        )
        response_before_cleared_cache = self.authorized_client.get(
            reverse('index')
        )
        self.assertEqual(
            response.content,
            response_before_cleared_cache.content
        )
        cache.clear()
        response_after_cleared_cache = self.authorized_client.get(
            reverse('index')
        )
        self.assertNotEqual(
            response.content,
            response_after_cleared_cache.content
        )

    def test_follow_process(self):
        """Работает ли подписка"""
        total_before_follow = Follow.objects.count()
        self.authorized_client.get(reverse('profile_follow', args=(
            self.test_author,
        )))
        __import__('pdb').set_trace()
        total_after_follow = Follow.objects.count()
        self.assertEqual(total_before_follow + 1, total_after_follow)
        follower = Follow.objects.first()
        self.assertEqual(follower.author, self.test_author)
        self.assertEqual(follower.user, self.user)

    def test_unfollow_process(self):
        """Работает ли отписка"""
        Follow.objects.create(user=self.user, author=self.test_author)
        total_before_unfollow = Follow.objects.count()
        self.authorized_client.get(
            reverse('profile_unfollow', args=(self.test_author,))
        )
        total_after_unfollow = Follow.objects.count()
        self.assertEqual(total_before_unfollow - 1, total_after_unfollow)

    def test_following_posts(self):
        """Отображается ли пост у подписчика на стр. foollow_index."""
        Follow.objects.create(user=self.user, author=self.test_author)
        response = self.authorized_client.get(reverse('follow_index'))
        self.check_context_post(response.context)

    def test_not_follower_posts(self):
        """Проверяем, посты не отображаются у юзера, который не подписан"""
        new_user = User.objects.create_user(username='Валера_настал_твой_час')
        auth_new_user = Client()
        auth_new_user.force_login(new_user)
        response_new_user = auth_new_user.get(reverse('follow_index'))
        Follow.objects.create(user=self.user, author=self.test_author)
        response = self.authorized_client.get(reverse('follow_index'))
        self.assertNotIn(
            response.context['page'][0], response_new_user.context['page']
        )
