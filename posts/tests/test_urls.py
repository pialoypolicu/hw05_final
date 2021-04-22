from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Group, Post

User = get_user_model()


class TaskURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.test_author = User.objects.create_user(username='Sasha')

        cls.group = Group.objects.create(
            title='Бизнес',
            slug='bisnes',
            description='test',
        )
        cls.post = Post.objects.create(
            text='Тестовый заголовок',
            author=cls.test_author,
            group=cls.group,
        )
        cls.URLS_FOR_FOR_ALL_USERS = [
            reverse('index'),
            reverse('group', kwargs={'slug': cls.group.slug}),
            reverse('profile', kwargs={'username': cls.post.author}),
            reverse('post',
                    kwargs={
                        'username': cls.post.author,
                        'post_id': cls.post.id
                    }),
        ]
        cls.URLS_FOR_AUTHORIZED_USERS = [
            reverse('new_post'),
            reverse(
                'post_edit',
                kwargs={'username': cls.post.author,
                        'post_id': cls.post.id}
            )
        ]

        cls.FOR_TEST_CORRECT_TEMPLATE = {
            reverse('index'): 'index.html',
            reverse('group', kwargs={'slug': cls.group.slug}): 'group.html',
            reverse('new_post'): 'new_post.html',
            reverse('post_edit', kwargs={
                'username': cls.post.author,
                'post_id': cls.post.id}): 'new_post.html'}

    def setUp(self):
        self.guest_client = Client()

        self.user = User.objects.create_user(username='Masha')
        self.user_masha = Client()
        self.user_masha.login(username='Masha')

        self.authorized_client_sasha = Client()
        self.authorized_client_sasha.force_login(self.test_author)

    def test_url_exists_at_desired_location(self):
        """Страницы доступные любому пользователю."""
        for url in self.URLS_FOR_FOR_ALL_USERS:
            with self.subTest():
                response = self.guest_client.get(url)
                self.assertEqual(
                    response.status_code,
                    HTTPStatus.OK,
                    f'guest {url}'
                )
                response = self.authorized_client_sasha.get(url)
                self.assertEqual(
                    response.status_code,
                    HTTPStatus.OK,
                    f'auth {url}'
                )

    def test_url_exists_at_desired_location_authorized(self):
        """Страницы доступные авторизованному пользователю. Если пользователь
        не авторизован, то происходит редирект"""
        for url in self.URLS_FOR_AUTHORIZED_USERS:
            with self.subTest():
                response = self.authorized_client_sasha.get(url)
                self.assertEqual(
                    response.status_code,
                    HTTPStatus.OK,
                    f'auth path {url}'
                )
                response = self.guest_client.get(url)
                self.assertEqual(
                    response.status_code,
                    HTTPStatus.FOUND,
                    f'guest path {url}'
                )

    def test_edit_post_not_author(self):
        """Может ли не автор редактировать чужие посты"""
        response = self.user_masha.get(reverse(
            'post_edit',
            kwargs={'username': self.post.author, 'post_id': self.post.id}
        ))
        self.assertEqual(
            response.status_code,
            HTTPStatus.FOUND,
            'Не можешь редактировать чужой пост'
        )

    def test_task_list_url_redirect_anonymous_on_admin_login(self):
        """Проверяем корректно ли происходит redirect."""
        response = self.guest_client.get(reverse('new_post'), follow=True)
        reverse_post_edit = reverse(
            'post_edit',
            kwargs={
                'username': self.post.author,
                'post_id': self.post.id
            }
        )
        redirect_path_login = reverse('login') + '?next=' + reverse_post_edit

        self.assertRedirects(
            response,
            reverse('login') + '?next=' + reverse('new_post')
        )
        response = self.guest_client.get(reverse_post_edit, follow=True)
        self.assertRedirects(response, redirect_path_login)
        response = self.user_masha.get(reverse_post_edit, follow=True)
        self.assertRedirects(response, redirect_path_login)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        for reverse_name, template in self.FOR_TEST_CORRECT_TEMPLATE.items():
            with self.subTest():
                response = self.authorized_client_sasha.get(reverse_name)
                self.assertTemplateUsed(
                    response,
                    template,
                    f'Шаблон {template}, не соответствует - {reverse_name}')

    def test_get_404_page(self):
        """выводит ли 404 ошибку"""
        response = self.authorized_client_sasha.get(
            reverse('profile', args=('vrotmnenogi',)))
        self.assertEqual(
            response.status_code,
            HTTPStatus.NOT_FOUND,
        )
