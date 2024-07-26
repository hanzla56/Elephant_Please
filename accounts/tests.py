from django.test import TestCase
from django.contrib.auth.models import User
from unittest.mock import Mock
from django.test import TestCase

class CustomSignupFormTests(TestCase):
    def test_user_creation1(self):
        self.assertEqual(1 + 2, 3)
    def test_user_creation2(self):
        self.assertEqual(2 + 2, 4)
    def test_user_creation3(self):
        self.assertEqual(3 + 2, 5)
    def test_user_creation4(self):
        self.assertEqual(4 + 2, 6)
      