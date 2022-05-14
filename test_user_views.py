"""User View tests."""

# run these tests like:
#
#    FLASK_ENV=production python -m unittest test_user_views.py

import os
from unittest import TestCase

from models import db, connect_db, User, Message, Follows

# Use test database and don't clutter tests with SQL
os.environ['DATABASE_URL'] = "postgresql:///warbler_test_db"

from app import app, CURR_USER_KEY

app.config['SQLALCHEMY_ECHO'] = False

# Make Flask errors be real errors, rather than HTML pages with error info
app.config['TESTING'] = True

# This is a bit of hack, but don't use Flask DebugToolbar
app.config['DEBUG_TB_HOSTS'] = ['dont-show-debug-toolbar']

# Don't req CSRF for testing
app.config['WTF_CSRF_ENABLED'] = False


db.drop_all()
db.create_all()


class UserViewTestCase(TestCase):
    """Test views for users."""

    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()

        self.client = app.test_client()

        self.testuser = User.signup(username="testuser",
                                    email="test@test.com",
                                    password="testuser",
                                    image_url=None)

        db.session.commit()
        
    def tearDown(self):
        """Tear down any session data we added."""
        
        db.session.rollback()

    def test_logout_redirect(self):
        """
        Test that when a user clicks logout, they are redirected to /.
        """

        # Since we need to change the session to mimic logging in,
        # we need to use the changing-session trick:
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            # Now, that session setting is saved, so we can have
            # the rest of ours test

            resp = c.get("/logout")
            html = resp.get_data(as_text=True)

            # Make sure it redirects
            self.assertEqual(resp.status_code, 302)
            self.assertIn("<a href=\"/\">", html)

    def test_logout_followed(self):
        """Test that user can log out and redirect to index with a flash message confirming that they have logged out."""

        # Since we need to change the session to mimic logging in,
        # we need to use the changing-session trick:
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            # Now, that session setting is saved, so we can have
            # the rest of ours test

            resp = c.get("/logout", follow_redirects=True)
            html = resp.get_data(as_text=True)

            # Make sure it redirects
            self.assertEqual(resp.status_code, 200)

            self.assertIn("danger", html)
            self.assertIn("New to Warbler?", html)

    def test_logout_no_flash_for_anon_visitor(self):
        """
        If a user isn't logged in and tries to visit /logout,
        redirect to "/" WITHOUT a flash message.
        """

        # Since we need to change the session to mimic logging in,
        # we need to use the changing-session trick:
        with self.client as c:

            resp = c.get("/logout", follow_redirects=True)
            html = resp.get_data(as_text=True)

            # Make sure it redirects
            self.assertEqual(resp.status_code, 200)

            self.assertNotIn("danger", html)
            self.assertIn("New to Warbler?", html)