from django.test import TestCase

from posts.models import Group, Post, User


class TaskModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        test_author = User.objects.create(username='Sasha')
        cls.group = Group.objects.create(
            title='Бизнес',
            slug='bisnes',
            description='Описание',
        )
        cls.post = Post.objects.create(
            text='Hello my friend.My name is Aleksandr',
            author=test_author,
            group=cls.group,
        )

    def test_verbose_name(self):
        """1. verbose_name в полях совпадает с ожидаемым."""
        field_verboses = {
            'title': 'Название',
            'slug': 'Путь',
            'description': 'Описание',
        }
        for value, expected in field_verboses.items():
            with self.subTest(value=value):
                self.assertEqual(
                    self.group._meta.get_field(value).verbose_name,
                    expected,
                    f'Ошибка в verbose_name, group, в поле {value}')

        field_verboses = {
            'text': 'Текст',
            'pub_date': 'Дата публикации',
            'group': 'группа',
            'author': 'Автор'
        }
        for value, expected in field_verboses.items():
            with self.subTest(value=value):
                self.assertEqual(
                    self.post._meta.get_field(value).verbose_name,
                    expected,
                    f'Ошибка verbose_name в Post, в поле {value}')

    def test_help_text(self):
        """help_text в полях совпадает с ожидаемым."""
        field_help_texts_in_group = {
            'title': 'Введите название группы',
            'slug': 'Укажите путь страницы',
            'description': 'Введите краткое описание группы',
        }
        for value, expected in field_help_texts_in_group.items():
            with self.subTest(value=value):
                self.assertEqual(
                    self.group._meta.get_field(value).help_text,
                    expected,
                    f'Ошибка в help_text group, поле {value}')

        field_help_texts_in_post = {
            'text': 'Введите текст',
            'group': 'Выберете группу',
        }
        for value, expected in field_help_texts_in_post.items():
            with self.subTest(value=value):
                self.assertEqual(
                    self.post._meta.get_field(value).help_text,
                    expected,
                    f'Ошибка help_text в post, в поле {value}'
                )

    def test_object_name_is_title_field(self):
        """__str__  строчка с содержимым group.title &
        posts.author & posts.text"""
        expected_object_name = self.group.title
        self.assertEquals(
            str(self.group),
            expected_object_name,
            'Ошибка __str__ группы'
        )
        post_author = self.post.author
        post_text = self.post.text[:15]
        expected_object_name = f'Автор: {post_author} Текст: {post_text}'
        self.assertEquals(str(self.post), expected_object_name)
