"""All test classes"""

from django.test import TestCase


class URLTests(TestCase):
    """test if all expected URL are there"""

    def test_home_view(self):
        """check homepage"""
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)

    def test_about_view(self):
        """check about page"""
        response = self.client.get("/about/")
        self.assertEqual(response.status_code, 200)

    def test_downloads_view(self):
        """check downloads page"""
        response = self.client.get("/downloads/")
        self.assertEqual(response.status_code, 200)

    def test_channel_view(self):
        """check channel page"""
        response = self.client.get("/channel/")
        self.assertEqual(response.status_code, 200)

    def test_settings_view(self):
        """check settings page"""
        response = self.client.get("/settings/")
        self.assertEqual(response.status_code, 200)

    def test_progress_view(self):
        """check ajax progress endpoint"""
        response = self.client.get("/downloads/progress/")
        self.assertEqual(response.status_code, 200)

    def test_process_view(self):
        """check process ajax endpoint"""
        response = self.client.get("/process/")
        self.assertEqual(response.status_code, 200)
