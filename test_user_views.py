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
        # A user that follows our test user
        self.followeruser = User.signup(username="followeruser",
                                    email="follower@test.com",
                                    password="followeruser",
                                    image_url=None)
        # A user that our test user is following
        self.followinguser = User.signup(username="followinguser",
                                    email="following@test.com",
                                    password="followinguser",
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

    def test_filled_user_bio_on_profile(self):
        """
        Test that a user bio is visible on the profile.
        """
                        
        # add text in the bio field
        self.testuser.bio = "testing the bio"
        db.session.commit()
        
        # Since we need to change the session to mimic logging in,
        # we need to use the changing-session trick:
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
                
            # Now, that session setting is saved, so we can have
            # the rest of ours test

            resp = c.get(f"/users/{self.testuser.id}")
            html = resp.get_data(as_text=True)
            
            # Make sure it redirects
            self.assertEqual(resp.status_code, 200)

            self.assertIn(self.testuser.bio, html)

    def test_empty_user_bio_shows_fallback(self):
        """
        Test that an empty bio shows the fallback text.
        """
                        
        # this string is what should appear on the front end
        fallback_text = "No bio yet."
        
        # Since we need to change the session to mimic logging in,
        # we need to use the changing-session trick:
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
                
            # Now, that session setting is saved, so we can have
            # the rest of ours test

            resp = c.get(f"/users/{self.testuser.id}")
            html = resp.get_data(as_text=True)

            # Make sure it redirects
            self.assertEqual(resp.status_code, 200)

            self.assertIn(fallback_text, html)
            self.assertEqual(self.testuser.bio, None)

    def test_filled_user_location_on_profile(self):
        """
        Test that a user location is visible on the profile.
        """
                        
        # add text in the bio field
        self.testuser.location = "Los Angeles"
        db.session.commit()
        
        # Since we need to change the session to mimic logging in,
        # we need to use the changing-session trick:
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
                
            # Now, that session setting is saved, so we can have
            # the rest of ours test

            resp = c.get(f"/users/{self.testuser.id}")
            html = resp.get_data(as_text=True)

            # Make sure it redirects
            self.assertEqual(resp.status_code, 200)

            self.assertIn(self.testuser.location, html)

    def test_empty_user_location_shows_fallback(self):
        """
        Test that an empty user location shows the fallback text.
        """
                        
        # this string is what should appear on the front end
        fallback_text = "The World"
        
        # Since we need to change the session to mimic logging in,
        # we need to use the changing-session trick:
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
                
            # Now, that session setting is saved, so we can have
            # the rest of ours test

            resp = c.get(f"/users/{self.testuser.id}")
            html = resp.get_data(as_text=True)

            # Make sure it redirects
            self.assertEqual(resp.status_code, 200)

            self.assertIn(fallback_text, html)
            self.assertEqual(self.testuser.location, None)

    def test_filled_user_header_image_on_profile(self):
        """
        Test that a user header image is visible on the profile.
        """
                        
        # add text in the bio field
        self.testuser.header_image_url = "/test_header_image_string.png"
        db.session.commit()
        
        # Since we need to change the session to mimic logging in,
        # we need to use the changing-session trick:
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
                
            # Now, that session setting is saved, so we can have
            # the rest of ours test

            resp = c.get(f"/users/{self.testuser.id}")
            html = resp.get_data(as_text=True)

            # Make sure it redirects
            self.assertEqual(resp.status_code, 200)

            self.assertIn(self.testuser.header_image_url, html)

    def test_empty_user_header_image_shows_fallback(self):
        """
        Test that an empty user location shows the fallback text.
        """
                        
        # this string is the default fallback set by models.pg
        fallback_text = "/static/images/warbler-hero.jpg"
        
        # Since we need to change the session to mimic logging in,
        # we need to use the changing-session trick:
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
                
            # Now, that session setting is saved, so we can have
            # the rest of ours test

            resp = c.get(f"/users/{self.testuser.id}")
            html = resp.get_data(as_text=True)

            # Make sure it redirects
            self.assertEqual(resp.status_code, 200)

            self.assertIn(fallback_text, html)

    def test_followers_on_followers_page(self):
        """
        Test that a follower appears on the a user's follower's page.
        """

        # Since we need to change the session to mimic logging in,
        # we need to use the changing-session trick:
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
            # Now, that session setting is saved, so we can have
            # the rest of ours test
            
            # We have to query the user due to a restriction of Session's lazy load operation
            curr_user = User.query.get(sess[CURR_USER_KEY])
            
            # Add the followeruser to the testuser's list of followers
            curr_user.followers.append(self.followeruser)
            db.session.commit()

            resp = c.get(f"/users/{self.testuser.id}/followers")
            html = resp.get_data(as_text=True)

            # Make sure it redirects
            self.assertEqual(resp.status_code, 200)

            self.assertIn(self.followeruser.username, html)

    def test_bios_on_follower_cards(self):
        """
        Test that bio appear on user bio cards on a user's /followers page.
        """
        
        # Since we need to change the session to mimic logging in,
        # we need to use the changing-session trick:
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            # We have to query the user due to a restriction of Session's lazy load operation
            curr_user = User.query.get(sess[CURR_USER_KEY])
            
            # Add the followeruser to the testuser's list of followers
            self.followeruser.bio = "our follower bio"
            curr_user.followers.append(self.followeruser)
            db.session.commit()

            # Now, that session setting is saved, so we can have
            # the rest of ours test

            resp = c.get(f"/users/{self.testuser.id}/followers")
            html = resp.get_data(as_text=True)

            # Make sure it redirects
            self.assertEqual(resp.status_code, 200)

            self.assertIn(self.followeruser.bio, html)

    def test_following_on_following_page(self):
        """
        Test that a follower appears on the a user's following page.
        """

        # Since we need to change the session to mimic logging in,
        # we need to use the changing-session trick:
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
            # Now, that session setting is saved, so we can have
            # the rest of ours test
            
            # We have to query the user due to a restriction of Session's lazy load operation
            curr_user = User.query.get(sess[CURR_USER_KEY])
            
            # Add the followinguser to the testuser's list of followers
            curr_user.following.append(self.followinguser)
            db.session.commit()

            resp = c.get(f"/users/{self.testuser.id}/following")
            html = resp.get_data(as_text=True)

            # Make sure it redirects
            self.assertEqual(resp.status_code, 200)

            self.assertIn(self.followinguser.username, html)

    def test_bios_on_following_cards(self):
        """
        Test that bio appear on user bio cards on a user's /following page.
        """
        
        # Since we need to change the session to mimic logging in,
        # we need to use the changing-session trick:
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            # We have to query the user due to a restriction of Session's lazy load operation
            curr_user = User.query.get(sess[CURR_USER_KEY])
            
            # Add the followinguser to the testuser's list of followers
            self.followinguser.bio = "our following bio"
            curr_user.following.append(self.followinguser)
            db.session.commit()

            # Now, that session setting is saved, so we can have
            # the rest of ours test

            resp = c.get(f"/users/{self.testuser.id}/following")
            html = resp.get_data(as_text=True)

            # Make sure it redirects
            self.assertEqual(resp.status_code, 200)

            self.assertIn(self.followinguser.bio, html)

    def test_show_update_profile_page_for_curr_user_only(self):
        """
        Ensure that only the logged-in user can edit their own profile.
        """
        
        # Since we need to change the session to mimic logging in,
        # we need to use the changing-session trick:
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
                
            # We have to query the user due to a restriction of Session's lazy load operation
            curr_user = User.query.get(sess[CURR_USER_KEY])
            
            # Add the followinguser to the testuser's list of followers
            # just so that we can attach this User object to session
            curr_user.following.append(self.followinguser)
            db.session.commit()
                
            resp = c.get("/users/profile")
            html = resp.get_data(as_text=True)

            # Make sure it redirects
            self.assertEqual(resp.status_code, 200)

            self.assertIn(self.testuser.username, html)
            self.assertNotIn(self.followinguser.username, html)

    def test_show_update_profile_page_redirect_for_anon_users(self):
        """
        Ensure that only the logged-in user can edit their own profile.
        """
        
        # Since we need to change the session to mimic logging in,
        # we need to use the changing-session trick:
        with self.client as c:
                
            resp = c.get("/users/profile")
            html = resp.get_data(as_text=True)

            # Make sure it sends a 302 redirect code
            self.assertEqual(resp.status_code, 302)

            self.assertIn("<a href=\"/\"", html)

    def test_show_update_profile_page_redirect_for_anon_users_followed(self):
        """
        Ensure that only the logged-in user can edit their own profile.
        """
        
        # Since we need to change the session to mimic logging in,
        # we need to use the changing-session trick:
        with self.client as c:
                
            resp = c.get("/users/profile", follow_redirects=True)
            html = resp.get_data(as_text=True)

            # Make sure it redirects
            self.assertEqual(resp.status_code, 200)

            self.assertIn("New to Warbler", html)

    # ! This works on front end, but test is not working!
    def test_update_profile_redirect_to_user_details_page_on_validation(self):
        """
        Show user details page on password validation.
        """

        # Since we need to change the session to mimic logging in,
        # we need to use the changing-session trick:

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            curr_user = User.query.get(sess[CURR_USER_KEY])

            resp = c.post("/users/profile", 
                          data={
                            'username': self.testuser.username,
                            'email': self.testuser.email,
                            'image_url': self.testuser.image_url,
                            'header_image_url': self.testuser.header_image_url,
                            'bio': self.testuser.bio,
                            'password': curr_user.password
                }, follow_redirects=True)
            
            import pdb
            pdb.set_trace()
            
            html = resp.get_data(as_text=True)

            # Make sure it redirects
            self.assertEqual(resp.status_code, 200)

            self.assertIn("testuser_edit", html)
