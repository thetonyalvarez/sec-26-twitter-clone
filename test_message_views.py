"""Message View tests."""

# run these tests like:
#
#    FLASK_ENV=production python -m unittest test_message_views.py

import os
from unittest import TestCase

from models import db, connect_db, Message, User

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler_test_db"

# Now we can import app

from app import app, CURR_USER_KEY

app.config['SQLALCHEMY_ECHO'] = False

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

# Make Flask errors be real errors, rather than HTML pages with error info
app.config['TESTING'] = True

# This is a bit of hack, but don't use Flask DebugToolbar
app.config['DEBUG_TB_HOSTS'] = ['dont-show-debug-toolbar']

db.drop_all()
db.create_all()

# Don't have WTForms use CSRF at all, since it's a pain to test

app.config['WTF_CSRF_ENABLED'] = False


class MessageViewTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()
        Message.query.delete()

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

    def test_add_message_get(self):
        """
        Test that user sees Add Message form on get request.
        """

        # Since we need to change the session to mimic logging in,
        # we need to use the changing-session trick:

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            # Now, that session setting is saved, so we can have
            # the rest of ours test

            resp = c.get("/messages/new")
            html = resp.get_data(as_text=True)

            # Make sure it redirects
            self.assertEqual(resp.status_code, 200)

            self.assertIn("Add my message", html)

    def test_add_message_post(self):
        """Can user add a message?"""

        # Since we need to change the session to mimic logging in,
        # we need to use the changing-session trick:

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            # Now, that session setting is saved, so we can have
            # the rest of ours test

            resp = c.post("/messages/new", data={"text": "Hello"})

            # Make sure it redirects
            self.assertEqual(resp.status_code, 302)

            msg = Message.query.one()
            self.assertEqual(msg.text, "Hello")

    def test_anon_user_cannot_add_message(self):
        """
        Test that anon user is redirected to home if they attempt
        to reach add message endpoint.
        """

        # Since we need to change the session to mimic logging in,
        # we need to use the changing-session trick:

        with self.client as c:

            # test get request
            resp = c.get("/messages/new", follow_redirects=True)
            html = resp.get_data(as_text=True)

            # Make sure it redirects
            self.assertEqual(resp.status_code, 200)

            self.assertIn("danger", html)

            # test post request
            resp = c.post("/messages/new", data={"text": "Hello"}, follow_redirects=True)
            html = resp.get_data(as_text=True)

            # Make sure it redirects
            self.assertEqual(resp.status_code, 200)

            self.assertIn("danger", html)

    def test_show_message(self):
        """
        Test that a user can view a message.
        User does NOT need to be logged in to view.
        """
        
        testuser_message = Message(
            text = "testing a new message"
        )
        followinguser_message = Message(
            text = "testing a new message for following"
        )
        followeruser_message = Message(
            text = "testing a new message for follower"
        )
        
        self.testuser.messages.append(testuser_message)
        self.followinguser.messages.append(followinguser_message)
        self.followeruser.messages.append(followeruser_message)
        db.session.commit()

        with self.client as c:
            
            test_u = Message.query.get(self.testuser.messages[0].id)
            test_fl = Message.query.get(self.followinguser.messages[0].id)
            test_fr = Message.query.get(self.followeruser.messages[0].id)

            resp_u = c.get(f"/messages/{test_u.id}", follow_redirects=True)
            resp_fl = c.get(f"/messages/{test_fl.id}", follow_redirects=True)
            resp_fr = c.get(f"/messages/{test_fr.id}", follow_redirects=True)
            html_u = resp_u.get_data(as_text=True)
            html_fl = resp_fl.get_data(as_text=True)
            html_fr = resp_fr.get_data(as_text=True)

            # Make sure it redirects
            self.assertEqual(resp_u.status_code, 200)
            self.assertEqual(resp_fl.status_code, 200)
            self.assertEqual(resp_fr.status_code, 200)

            self.assertIn(test_u.text, html_u)
            self.assertIn(test_fl.text, html_fl)
            self.assertIn(test_fr.text, html_fr)

    def test_redirect_for_invalid_message_id(self):
        """
        Test that a user is redirected if they attempt
        to visit an invalid message id.
        User does NOT need to be logged in to view.
        """
        
        with self.client as c:
            
            resp = c.get(f"/messages/1284941827125", follow_redirects=True)
            html = resp.get_data(as_text=True)

            # Make sure it redirects
            self.assertEqual(resp.status_code, 200)

            self.assertIn("danger", html)

    def test_delete_message(self):
        """
        Test that a curr user can delete their own message.
        User does NOT need to be logged in to view.
        """
        
        testuser_message = Message(
            text = "testing a new message"
        )
        followinguser_message = Message(
            text = "testing a new message for following"
        )
        followeruser_message = Message(
            text = "testing a new message for follower"
        )
        
        self.testuser.messages.append(testuser_message)
        self.followinguser.messages.append(followinguser_message)
        self.followeruser.messages.append(followeruser_message)
        db.session.commit()

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
                
            curr_user = User.query.get(sess[CURR_USER_KEY])
            
            test_msg = Message.query.get(curr_user.messages[0].id)

            resp = c.post(f"/messages/{curr_user.messages[0].id}/delete", follow_redirects=True)
            
            curr_user = User.query.get(sess[CURR_USER_KEY])

            self.assertEqual(len(curr_user.messages), 0)

    def test_user_cannot_delete_another_users_message(self):
        """
        Test that a curr user can delete their own message.
        User does NOT need to be logged in to view.
        """
        
        # create test message instances
        testuser_message = Message(
            text = "testing a new message"
        )
        followinguser_message = Message(
            text = "testing a new message for following"
        )

        # append each message to its respective user
        self.testuser.messages.append(testuser_message)
        self.followinguser.messages.append(followinguser_message)
        
        # curr user follows followinguser - this is so that we can 
        # access followinguser's messages in the session data
        self.testuser.following.append(self.followinguser)
        db.session.commit()

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
                
            # query the curr user
            curr_user = User.query.get(sess[CURR_USER_KEY])

            # query the message from the followinguser.
            # this is the msg that we are going to try to delete 
            # as curr user
            test_msg = Message.query.get(curr_user.following[0].messages[0].id)

            # make the post request to delete the msg
            resp = c.post(f"/messages/{test_msg.id}/delete", follow_redirects=True)
            html = resp.get_data(as_text=True)
            
            # assert that the danger error appears in the response
            self.assertIn("danger", html)
            
            # assert that the test msg exists
            test_msg = Message.query.get(curr_user.following[0].messages[0].id)
            self.assertNotEqual(test_msg, None)

    def test_anon_user_cannot_delete_message(self):
        """
        Test that anon user is redirected to home if they attempt
        to delete message endpoint.
        """
        
        # create test message instances
        testuser_message = Message(
            text = "testing a new message"
        )

        # append each message to its respective user
        self.testuser.messages.append(testuser_message)
        db.session.commit()

        # Since we need to change the session to mimic logging in,
        # we need to use the changing-session trick:

        with self.client as c:

            # test get request
            resp = c.get("/messages/1/delete", follow_redirects=True)
            html = resp.get_data(as_text=True)

            # Make sure it redirects
            self.assertEqual(resp.status_code, 200)

            self.assertIn("danger", html)

            # test post request
            resp = c.post("/messages/1/delete", follow_redirects=True)
            html = resp.get_data(as_text=True)

            # Make sure it redirects
            self.assertEqual(resp.status_code, 200)

            self.assertIn("danger", html)