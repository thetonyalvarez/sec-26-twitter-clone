"""Message model tests."""

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

class MessageModelTestCase(TestCase):
    """Test models for messages."""

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

    def test_message_model(self):
        """Does basic model work?"""

        test_user = User(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD"
        )
        
        msg = Message(
            text="testing a new message"
        )
        

        db.session.add(test_user)
        test_user.messages.append(msg)
        db.session.commit()

        # Messages should have 1 entry
        self.assertEqual(len(test_user.messages), 1)