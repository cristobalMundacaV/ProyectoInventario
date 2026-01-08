from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse

User = get_user_model()

class AuthLogoutTests(TestCase):
    def setUp(self):
        self.username = 'tester'
        self.password = 'pass'
        self.user = User.objects.create_user(self.username, 'tester@example.com', self.password)
        self.client = Client()

    def test_logout_via_get_logs_out(self):
        logged_in = self.client.login(username=self.username, password=self.password)
        self.assertTrue(logged_in)
        resp = self.client.get(reverse('logout'), follow=True)
        # Followed redirect to login; context may be None depending on redirect target.
        # Ensure session no longer contains auth user id
        self.assertNotIn('_auth_user_id', self.client.session)
        # And we ended up on a page (status 200 after follow)
        self.assertEqual(resp.status_code, 200)

    def test_logout_via_post_logs_out(self):
        logged_in = self.client.login(username=self.username, password=self.password)
        self.assertTrue(logged_in)
        resp = self.client.post(reverse('logout'), follow=True)
        self.assertIn('user', resp.context)
        self.assertFalse(resp.context['user'].is_authenticated)
        self.assertNotIn('_auth_user_id', self.client.session)
