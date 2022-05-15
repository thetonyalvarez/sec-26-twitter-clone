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

