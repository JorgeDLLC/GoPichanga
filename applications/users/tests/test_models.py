# applications/users/tests/test_models.py
from django.test import TestCase
from django.core.exceptions import ValidationError
from applications.users.models import User, Partner, UserRole

class PartnerModelTests(TestCase):
    def test_partner_requires_user_with_partner_role(self):
        # user regular
        u = User.objects.create(
            nombre="Reg", email="reg@example.com", password="x", rol=UserRole.REGULAR
        )
        p = Partner(user=u, dni="12345678", cci="12345678901234567890")
        with self.assertRaises(ValidationError):
            p.full_clean()  # dispara clean()

    def test_partner_ok_with_partner_role(self):
        u = User.objects.create(
            nombre="Socio", email="socio@example.com", password="x", rol=UserRole.PARTNER
        )
        p = Partner(user=u, dni="87654321", cci="09876543210987654321")
        # No debería lanzar excepción
        p.full_clean()
        p.save()
        self.assertIsNotNone(p.id)
