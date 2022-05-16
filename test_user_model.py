"""User model tests."""

# run these tests like:
#
#    python -m unittest test_user_model.py

import os
from unittest import TestCase

from models import db, User, Message, Follows

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler_test_db"


# Now we can import app

from app import app

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.drop_all()
db.create_all()


class UserModelTestCase(TestCase):
    """Test models for users."""

    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()
        Message.query.delete()
        Follows.query.delete()

        self.client = app.test_client()
        
    def tearDown(self):
        """Remove any temp data in session.
        """
        
        db.session.rollback()

    def test_user_model(self):
        """Does basic model work?"""

        u = User(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD"
        )

        db.session.add(u)
        db.session.commit()

        # User should have no messages & no followers
        self.assertEqual(len(u.messages), 0)
        self.assertEqual(len(u.followers), 0)

    def test_user_details(self):
        """
        Test that user details can  be added to an
        existing user.
        """

        test_user = User(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD"
        )

        db.session.add(test_user)
        
        test_user.image_url = "/test/imageUrl.jpg"
        test_user.header_image_url = "/test/imageUrl.jpg"
        test_user.location = "user location"
        test_user.bio = "bio for the user"

        db.session.commit()
        
        # User should have no messages & no followers
        self.assertIn("/test/imageUrl.jpg", test_user.image_url)
        self.assertIn("/test/imageUrl.jpg", test_user.header_image_url)
        self.assertIn("user location", test_user.location)
        self.assertIn("bio for the user", test_user.bio)

    def test_user_repr(self):
        """
        Test that __repr__ function prints properly.
        """
        
        test_user = User(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD"
        )
        
        test_repr = f"<User #{test_user.id}: {test_user.username}, {test_user.email}>"

        self.assertEqual(repr(test_user), test_repr)
        
    def test_is_followed_by(self):
        """
        Test that test_user is followed by followed_user
        """
        
        test_user = User(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD"
        )
        
        followed_user = User(
            email="followed@test.com",
            username="followeduser",
            password="HASHED_PASSWORD"
        )

        test_user.followers.append(followed_user)
        
        self.assertEqual(test_user.is_followed_by(followed_user), True)

    def test_is_following(self):
        """
        Test that test_user is following following_user
        """
        
        test_user = User(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD"
        )
        
        following_user = User(
            email="following@test.com",
            username="followinguser",
            password="HASHED_PASSWORD"
        )

        test_user.following.append(following_user)
        
        self.assertEqual(test_user.is_following(following_user), True)

    def test_user_signup(self):
        """
        Test that User.signup() class method works.
        """
        
        new_user = User.signup('testuser', 'test@test.com', 'HASHED_PASSWORD', '/image.png')
        
        self.assertEqual(new_user.username, 'testuser')
        self.assertEqual(new_user.email, 'test@test.com')
        self.assertEqual(new_user.image_url, '/image.png')

        self.assertNotEqual(new_user.username, 'testuserasdf')
        self.assertNotEqual(new_user.email, 'testasdf@test.com')
        self.assertNotEqual(new_user.image_url, '/asdfimage.png')

    def test_user_authenticate(self):
        """
        Test that User.authenticate() class method works.
        """
        
        test_user = User.signup('testuser', 'test@test.com', 'HASHED_PASSWORD', '/image.png')

        new_user = User.authenticate('testuser', 'HASHED_PASSWORD')

        self.assertEqual(new_user.username, test_user.username)
        self.assertEqual(new_user.password, test_user.password)

        self.assertNotEqual(new_user.password, 'wrong_password')
        self.assertNotEqual(new_user.username, 'wrong_username')