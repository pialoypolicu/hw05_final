from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from http import HTTPStatus

User = get_user_model()


class TaskURLTests(TestCase):
    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='AndreyG')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

        self.URLS_NAME = ['about:author', 'about:tech']

    def test_url_exists_at_desired_location_guest_user(self):
        """Страница доступна неавторизованному пользователю."""
        for url in self.URLS_NAME:
            with self.subTest():
                response = self.guest_client.get(reverse(url))
                self.assertEqual(
                    response.status_code,
                    HTTPStatus.OK,
                    f'guest {url}'
                )

    def test_url_exists_at_desired_location_authorized_user(self):
        """Страница доступна авторизованному пользователю"""
        for url in self.URLS_NAME:
            with self.subTest():
                response = self.authorized_client.get(reverse(url))
                self.assertEqual(
                    response.status_code,
                    HTTPStatus.OK,
                    f'auth {url}'
                )
