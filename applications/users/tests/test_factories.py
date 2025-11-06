# applications/users/tests/test_factories.py
from django.test import TestCase
from django.core.exceptions import ValidationError
from applications.users.factories import UserFactory, RegularUserInput
from applications.users.models import User, Regular, UserRole

class UserFactoryTests(TestCase):
    def test_create_regular_ok(self):
        inp = RegularUserInput(
            nombre="Jorge Llanos",
            email="jorge@example.com",
            password="secret123",
            telefono="999999999",
            fecha_nacimiento="2000-01-01",
            direccion="Lima"
        )
        user = UserFactory.create_regular(inp)

        self.assertIsNotNone(user.id)
        self.assertEqual(user.rol, UserRole.REGULAR)
        self.assertTrue(Regular.objects.filter(user=user).exists())

    def test_create_regular_fails_on_missing_required(self):
        inp = RegularUserInput(
            nombre="",  # faltante
            email="missing@example.com",
            password="x"
        )
        with self.assertRaises(ValidationError):
            UserFactory.create_regular(inp)

    def test_create_regular_fails_on_duplicate_email(self):
        # primer usuario OK
        UserFactory.create_regular(RegularUserInput(
            nombre="A", email="dup@example.com", password="p"
        ))
        # segundo con mismo email -> falla
        with self.assertRaises(ValidationError):
            UserFactory.create_regular(RegularUserInput(
                nombre="B", email="dup@example.com", password="q"
            ))
