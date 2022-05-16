"""User View tests."""

# run these tests like:
#
#    FLASK_ENV=production python -m unittest test_user_views.py

import os
from unittest import TestCase

from models import db, connect_db, User, Message, Follows, Likes

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

    def test_single_user_page_view(self):
        """
        Show a single user by id.
        User does NOT have to be logged in to view single user.
        """
        
        testuser = self.testuser.id
        
        # Since we need to change the session to mimic logging in,
        # we need to use the changing-session trick:

        with self.client as c:

            resp = c.get(f'/users/{testuser}')
            
            html = resp.get_data(as_text=True)

            self.assertIn("testuser", html)
            self.assertNotIn("followinguser", html)
            self.assertNotIn("New to Warbler", html)

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
        Test that a follower appears on the user's follower's page.
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

    def test_follow_a_user(self):
        """
        Test that curr user can follow another user.
        Test that curr user cannot follow an invalid user id.
        """
        
        following_user = self.followinguser.id
        
        # Since we need to change the session to mimic logging in,
        # we need to use the changing-session trick:
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
                
            curr_user = User.query.get(sess[CURR_USER_KEY])
            
            resp = c.post(f'/users/follow/{following_user}', follow_redirects=True)
            
            html = resp.get_data(as_text=True)
            
            self.assertIn("testuser", html)
            self.assertIn("followinguser", html)
            self.assertNotIn("followeruser", html)
            
            # Test that a non-existest user_id redirects to 404
            resp = c.post('/users/follow/99999', follow_redirects=True)
            
            html = resp.get_data(as_text=True)
            
            self.assertEqual(resp.status_code, 404)

    def test_anon_user_cannot_follow_a_user(self):
        """
        Test that anon user cannot follow another user.
        Instead, redirect them  to "/" and flash unauthorized message.
        """
        
        following_user = self.followinguser.id
        
        # Since we need to change the session to mimic logging in,
        # we need to use the changing-session trick:
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
                
            # Test invalid post request
            resp = c.post(f'/users/follow/{following_user}', follow_redirects=True)
            html = resp.get_data(as_text=True)
            
            # check for the "danger" flash message in the response.
            self.assertIn("danger", html)
            self.assertNotIn("followeruser", html)
            
            # Test invalid get request
            resp = c.get(f'/users/follow/{following_user}', follow_redirects=True)
            html = resp.get_data(as_text=True)
            
            # check for the "danger" flash message in the response.
            self.assertIn("danger", html)
            self.assertNotIn("followeruser", html)
            
            # Test that a non-existest user_id POST request redirects to 404
            resp = c.post('/users/follow/99999', follow_redirects=True)
            html = resp.get_data(as_text=True)
            
            self.assertEqual(resp.status_code, 404)

            # Test that a non-existest user_id GET request redirects to 404
            resp = c.get('/users/follow/99999', follow_redirects=True)
            html = resp.get_data(as_text=True)
            
            self.assertEqual(resp.status_code, 200)

    def test_unfollow_a_user(self):
        """
        Test that curr user can un-follow another user.
        Test that curr user cannot un-follow an invalid user id.
        """
        
        following_user = self.followinguser
        self.testuser.following.append(following_user)
        db.session.commit()
        
        # Since we need to change the session to mimic logging in,
        # we need to use the changing-session trick:
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
                
            curr_user = User.query.get(sess[CURR_USER_KEY])
            
            resp = c.post(f'/users/stop-following/{curr_user.following[0].id}', follow_redirects=True)
            html = resp.get_data(as_text=True)
            
            self.assertIn("testuser", html)
            self.assertNotIn("followinguser", html)
            self.assertNotIn("followeruser", html)
            
            # Test that a non-existest user_id redirects to 404
            resp = c.post('/users/stop-following/99999', follow_redirects=True)
            
            html = resp.get_data(as_text=True)
            
            self.assertEqual(resp.status_code, 404)

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
            
            # the password needs to be passed in the data as the literal string, not hashed.
            resp = c.post("/users/profile", 
                          json={
                            'username': "testuser_edit",
                            'email': self.testuser.email,
                            'image_url': self.testuser.image_url,
                            'header_image_url': self.testuser.header_image_url,
                            'bio': self.testuser.bio,
                            'password': "testuser"
                }, follow_redirects=True)
            
            html = resp.get_data(as_text=True)

            # Make sure it redirects
            self.assertEqual(resp.status_code, 200)

            self.assertIn("testuser_edit", html)

    def test_update_profile_redirect_to_home_on_invalid_password(self):
        """
        Show user details page on password validation.
        """

        # Since we need to change the session to mimic logging in,
        # we need to use the changing-session trick:

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            curr_user = User.query.get(sess[CURR_USER_KEY])
            
            # the password needs to be passed in the data as the literal string, not hash, for User auth to work.
            resp = c.post("/users/profile", 
                          json={
                            'username': "testuser_edit",
                            'email': self.testuser.email,
                            'image_url': self.testuser.image_url,
                            'header_image_url': self.testuser.header_image_url,
                            'bio': self.testuser.bio,
                            'password': "incorrectpassword"
                }, follow_redirects=True)
            
            html = resp.get_data(as_text=True)

            # Make sure it redirects
            self.assertEqual(resp.status_code, 200)

            # check for flashed 'Incorrect password' message
            self.assertIn("Incorrect password", html)

    def test_show_messages_from_users_that_curr_users_follows(self):
        """
        Show only messages from users that the user follows, plus curr user's messages.
        """
        
        # create a test message for our curr user, the user they follow, and a follower
        following_test_message = Message(
            text = "testing a new message from a person we follow"
        )
        follower_test_message = Message(
            text = "testing a new message from a person that follows curr user. this should not appear."
        )
        curr_test_message = Message(
            text = "testing our curr users new message"
        )
        
        # append the messages to each user
        self.followinguser.messages.append(following_test_message)
        self.followeruser.messages.append(follower_test_message)
        self.testuser.messages.append(curr_test_message)

        # Add the followinguser to the testuser's list of followers
        # just so that we can attach this User object to session
        self.testuser.following.append(self.followinguser)
        self.followeruser.following.append(self.testuser)
        db.session.commit()
        
        # Since we need to change the session to mimic logging in,
        # we need to use the changing-session trick:

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
            
            # We have to query the users due to a restriction of Session's lazy load operation
            curr_user = User.query.get(sess[CURR_USER_KEY])

            resp = c.get('/')

            html = resp.get_data(as_text=True)

            self.assertIn(curr_user.following[0].messages[0].text, html)
            self.assertIn(curr_user.messages[0].text, html)

            # make sure we don't see follower's messages in our curr user feed
            # since we don't follow them
            self.assertNotIn(curr_user.followers[0].messages[0].text, html)

    def test_show_signup_screen_for_anon_users(self):
        """
        Show signup screen when anon user visits "/".
        """
        
        # Since we need to change the session to mimic logging in,
        # we need to use the changing-session trick:

        with self.client as c:
            
            resp = c.get('/')

            html = resp.get_data(as_text=True)

            # make sure we don't see follower's messages in our curr user feed
            # since we don't follow them
            self.assertIn("New to Warbler?", html)

    def test_show_100_messages_max_for_curr_user(self):
        """
        Show only 100 messages max for a curr user.
        """
        
        i = 0

        while (i < 200):
            i += 1
            test_message = Message(
                text = f'message number {i}'
            )
            self.testuser.messages.append(test_message)
        
        db.session.commit()

        # Since we need to change the session to mimic logging in,
        # we need to use the changing-session trick:

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
            
            # We have to query the users due to a restriction of Session's lazy load operation
            curr_user = User.query.get(sess[CURR_USER_KEY])

            resp = c.get('/')

            html = resp.get_data(as_text=True)

            self.assertIn(curr_user.messages[0].text, html)
            self.assertIn(curr_user.messages[50].text, html)
            self.assertNotIn(curr_user.messages[150].text, html)
            self.assertNotIn(curr_user.messages[199].text, html)

    def test_delete_user(self):
        """
        Test that a user can be deleted successfully.
        """
        
        # Since we need to change the session to mimic logging in,
        # we need to use the changing-session trick:
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
                
            curr_user = User.query.get(sess[CURR_USER_KEY])
            
            resp = c.post(f'/users/delete', follow_redirects=True)
            html = resp.get_data(as_text=True)
            
            # query the curr_user session. This should return None 
            curr_user = User.query.get(sess[CURR_USER_KEY])
            
            # redirect to signup page
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Join Warbler", html)
            self.assertEqual(curr_user, None)

    def test_anon_user_cannot_delete_user(self):
        """
        Test that an anon user cannot delete a user
        and instead redirect them to "/"
        and flash them unauthorized message.
        """
        
        # Since we need to change the session to mimic logging in,
        # we need to use the changing-session trick:
        with self.client as c:
            
            # Test invalid post request
            resp = c.post('/users/delete', follow_redirects=True)
            html = resp.get_data(as_text=True)
            
            # check for the "danger" flash message in the response.
            self.assertIn("danger", html)
            self.assertNotIn("testuser", html)
            self.assertNotIn("followeruser", html)
            
            # Test invalid get request
            resp = c.get('/users/delete', follow_redirects=True)
            html = resp.get_data(as_text=True)
            
            # check for the "danger" flash message in the response.
            self.assertIn("danger", html)
            self.assertNotIn("testuser", html)
            self.assertNotIn("followeruser", html)

class LikesTestCase(TestCase):
    """Test likes for users."""

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

    def test_add_like_post(self):
        """
        Test that user can like a message.
        Users should not be able to like their own messages.
        """
        
        # create a test message for our curr user, the user they follow, and a follower
        following_test_message = Message(
            text = "testing a new message from a person we follow"
        )
        follower_test_message = Message(
            text = "testing a new message from a person that follows curr user. this should not appear."
        )
        curr_test_message = Message(
            text = "testing our curr users new message"
        )
        
        # append the messages to each user
        self.followinguser.messages.append(following_test_message)
        self.followeruser.messages.append(follower_test_message)
        self.testuser.messages.append(curr_test_message)

        # Add the followinguser to the testuser's list of followers
        # just so that we can attach this User object to session
        self.testuser.following.append(self.followinguser)
        self.followeruser.following.append(self.testuser)
        db.session.commit()
        
        # Since we need to change the session to mimic logging in,
        # we need to use the changing-session trick:

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
            
            curr_user = User.query.get(sess[CURR_USER_KEY])
            followinguser = curr_user.following[0]
            msg_to_like = followinguser.messages[0]
            
            # test that post request works
            resp = c.post(f'/users/add_like/{msg_to_like.id}', follow_redirects=True)
            html = resp.get_data(as_text=True)
            
            self.assertIn("remove_like", html)
            
            # test that post request does NOT work for g.users own message
            curr_user = User.query.get(sess[CURR_USER_KEY])
            resp = c.post(f'/users/add_like/{curr_user.messages[0].id}', follow_redirects=True)
            html = resp.get_data(as_text=True)
            
            self.assertIn("danger", html)

    def test_add_like_get(self):
        """
        Test that user cannot access add_like endpoint as
        a get request.
        """
        
        # create a test message for our curr user, the user they follow, and a follower
        following_test_message = Message(
            text = "testing a new message from a person we follow"
        )
        follower_test_message = Message(
            text = "testing a new message from a person that follows curr user. this should not appear."
        )
        curr_test_message = Message(
            text = "testing our curr users new message"
        )
        
        # append the messages to each user
        self.followinguser.messages.append(following_test_message)
        self.followeruser.messages.append(follower_test_message)
        self.testuser.messages.append(curr_test_message)

        # Add the followinguser to the testuser's list of followers
        # just so that we can attach this User object to session
        self.testuser.following.append(self.followinguser)
        self.followeruser.following.append(self.testuser)
        db.session.commit()
        
        # Since we need to change the session to mimic logging in,
        # we need to use the changing-session trick:

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
            
            curr_user = User.query.get(sess[CURR_USER_KEY])
            followinguser = curr_user.following[0]
            msg_to_like = followinguser.messages[0]

            # test that GET request does not work
            resp = c.get(f'/users/add_like/{msg_to_like.id}', follow_redirects=True)
            html = resp.get_data(as_text=True)
            
            self.assertIn("danger", html)

    def test_anon_cannot_add_like_post_or_get(self):
        """
        Test that anon user cannot like a message.
        Anon users should not be able to like any messages.
        """
        
        with self.client as c:
            
            # test that anon user cannot add like
            resp = c.post('/users/add_like/1', follow_redirects=True)
            html = resp.get_data(as_text=True)
            
            self.assertIn("danger", html)
            
            # test that post request does NOT work for g.users own message
            resp = c.get('/users/add_like/1', follow_redirects=True)
            html = resp.get_data(as_text=True)
            
            self.assertIn("danger", html)

    def test_remove_like_post(self):
        """
        Test that user can like a message.
        Users should not be able to like their own messages.
        """
        
        # create a test message for our curr user, the user they follow, and a follower
        following_test_message = Message(
            text = "testing a new message from a person we follow"
        )
        follower_test_message = Message(
            text = "testing a new message from a person that follows curr user. this should not appear."
        )
        curr_test_message = Message(
            text = "testing our curr users new message"
        )
        
        # append the messages to each user
        self.followinguser.messages.append(following_test_message)
        self.followeruser.messages.append(follower_test_message)
        self.testuser.messages.append(curr_test_message)
        
        testuser_liked_msg = Likes(
            user_id = self.testuser.id,
            message_id = self.followinguser.messages[0].id
        )
        
        # Add the followinguser to the testuser's list of followers
        # just so that we can attach this User object to session
        self.testuser.following.append(self.followinguser)
        self.followeruser.following.append(self.testuser)
        db.session.add(testuser_liked_msg)
        db.session.commit()
        
        # Since we need to change the session to mimic logging in,
        # we need to use the changing-session trick:

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
            
            curr_user = User.query.get(sess[CURR_USER_KEY])
            curr_like = Likes.query.first()
            
            # import pdb
            # pdb.set_trace()

            # test that post request works
            resp = c.post(f'/users/remove_like/{curr_like.message_id}', follow_redirects=True)
            html = resp.get_data(as_text=True)
            
            self.assertIn("add_like", html)

    def test_remove_like_get(self):
        """
        Test that user cannot access remove_like endpoint as
        a get request.
        """
        
        # create a test message for our curr user, the user they follow, and a follower
        following_test_message = Message(
            text = "testing a new message from a person we follow"
        )
        follower_test_message = Message(
            text = "testing a new message from a person that follows curr user. this should not appear."
        )
        curr_test_message = Message(
            text = "testing our curr users new message"
        )
        
        testuser_liked_msg = Likes(
            user_id = self.testuser.id,
            message_id = following_test_message.id,
        )
        
        # append the messages to each user
        self.followinguser.messages.append(following_test_message)
        self.followeruser.messages.append(follower_test_message)
        self.testuser.messages.append(curr_test_message)

        # Add the followinguser to the testuser's list of followers
        # just so that we can attach this User object to session
        self.testuser.following.append(self.followinguser)
        self.followeruser.following.append(self.testuser)
        db.session.commit()
        
        # Since we need to change the session to mimic logging in,
        # we need to use the changing-session trick:

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
            
            curr_user = User.query.get(sess[CURR_USER_KEY])
            followinguser = curr_user.following[0]
            msg_to_like = followinguser.messages[0]

            # test that GET request does not work
            resp = c.get(f'/users/remove_like/{msg_to_like.id}', follow_redirects=True)
            html = resp.get_data(as_text=True)
            
            self.assertIn("danger", html)

    def test_anon_cannot_remove_like_post_or_get(self):
        """
        Test that user can un-like a message.
        Anon users should not be able to un-like any messages.
        """
        
        with self.client as c:
            
            # test that anon user cannot add like
            resp = c.post('/users/remove_like/1', follow_redirects=True)
            html = resp.get_data(as_text=True)
            
            self.assertIn("danger", html)
            
            # test that post request does NOT work for g.users own message
            resp = c.get('/users/remove_like/1', follow_redirects=True)
            html = resp.get_data(as_text=True)
            
            self.assertIn("danger", html)

    def test_show_likes(self):
        """
        Test that user can see all liked messages for any user.
        User must be logged in to view another user's likes.
        """
        
        # create a test message for our curr user, the user they follow, and a follower
        following_test_message = Message(
            text = "testing a new message from a person we follow"
        )
        
        # append the messages to each user
        self.followinguser.messages.append(following_test_message)
        
        # Add the followinguser to the testuser's list of followers
        # just so that we can attach this User object to session
        self.testuser.following.append(self.followinguser)

        db.session.commit()

        # Since we need to change the session to mimic logging in,
        # we need to use the changing-session trick:

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            curr_user = User.query.get(sess[CURR_USER_KEY])
            
            testuser_liked_msg = Likes(
                user_id = self.testuser.id,
                message_id = curr_user.following[0].messages[0].id,
            )
            
            db.session.add(testuser_liked_msg)
            db.session.commit()

            resp = c.get(f'/users/{curr_user.id}/likes', follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertIn("testing a new message from a person we follow", html)

    def test_anon_cannot_see_likes(self):
        """
        Test that anon user cannot see liked messages for any user.
        User must be logged in to view another user's likes.
        """

        # Since we need to change the session to mimic logging in,
        # we need to use the changing-session trick:

        with self.client as c:
            
            resp = c.get('/users/1/likes', follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertIn("danger", html)
