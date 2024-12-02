# users/tests.py
from rest_framework.test import APITestCase
from rest_framework import status

class AuthenticationTest(APITestCase):
    def test_user_registration(self):
        data = {"username": "testuser", "email": "test@example.com", "password": "testpassword"}
        response = self.client.post('/register/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
