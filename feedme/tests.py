from django.contrib.auth.models import User
from django.db import IntegrityError
from django.test import TestCase

from feedme.models import Feed, FeedItem


class FeedMeTestCase(TestCase):

    def test_update_feed(self):
        feed = Feed(url='http://derek.stegelman.com/blog/feed/')
        feed.save()
        feed.update(force=True)
        self.assertTrue(FeedItem.objects.all().count(), 10)

    def test_me(self):
        self.assertTrue(True, True)

    def test_multiple_users_same_feed(self):
        user1 = User(username="user1")
        user1.set_unusable_password()
        user2 = User(username="user2")
        user2.set_unusable_password()

        user1.save()
        user2.save()

        feed_url = 'http://derek.stegelman.com/blog/feed/'
        feed1 = Feed(user=user1, url=feed_url)
        feed2 = Feed(user=user2, url=feed_url)
        try:
            feed1.save()
            feed2.save()
        except IntegrityError:
            self.fail("Couldn't add %s for both %s and %s" % (feed_url, user1, user2))

        self.assertIsNotNone(feed1.pk)
        self.assertIsNotNone(feed2.pk)

