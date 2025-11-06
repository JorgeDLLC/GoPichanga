# applications/users/tests/test_views.py
from django.test import TestCase
from django.urls import reverse
from applications.users.models import User, Regular, UserRole

class CreateRegularViewTests(TestCase):
    def test_get_renders_form(self):
        url = reverse("users:regular_create")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "<form", status_code=200)

    def test_post_creates_user_and_regular_and_redirects(self):
        url = reverse("users:regular_create")
        payload = {
            "nombre": "Jorge",
            "email": "jorge@example.com",
            "password": "secret123",
            "telefono": "999999999",
            "fecha_nacimiento": "2000-01-01",
            "direccion": "Lima",
        }
        resp = self.client.post(url, data=payload, follow=False)
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp["Location"], reverse("users:regular_creado"))

        u = User.objects.get(email="jorge@example.com")
        self.assertEqual(u.rol, UserRole.REGULAR)
        self.assertTrue(Regular.objects.filter(user=u).exists())

    def test_post_invalid_shows_errors(self):
        url = reverse("users:regular_create")
        resp = self.client.post(url, data={"nombre": "", "email": "", "password": ""})
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "error", status_code=200)
