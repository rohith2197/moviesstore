from django.test import TestCase
from django.contrib.auth.models import User

from cart.models import Item, Order
from .models import Movie, Review


class MovieStatsViewTests(TestCase):
    """Covers the admin "Movie Stats" screen (most bought / most reviewed)."""

    def setUp(self):
        self.admin_user = User.objects.create_superuser(
            username='admin_user', email='admin@example.com', password='adminpass123')
        self.member = User.objects.create_user(
            username='member', email='member@example.com', password='memberpass123')

        self.inception = Movie.objects.create(
            name='Inception', price=12, description='Mind bending')
        self.avatar = Movie.objects.create(
            name='Avatar', price=13, description='Visually crazy')

        self.client.login(username='admin_user', password='adminpass123')

    def _stats_html(self):
        response = self.client.get('/admin/movies/movie/stats/')
        self.assertEqual(response.status_code, 200)
        return response.content.decode()

    def _review(self, movie, comment='great movie'):
        self.client.logout()
        self.client.login(username='member', password='memberpass123')
        self.client.post(f'/movies/{movie.id}/review/create/', {'comment': comment})
        self.client.logout()
        self.client.login(username='admin_user', password='adminpass123')

    def _purchase(self, movie, times=1):
        self.client.logout()
        self.client.login(username='member', password='memberpass123')
        for _ in range(times):
            self.client.post(f'/cart/{movie.id}/add/', {'quantity': '1'})
            response = self.client.post('/cart/purchase/')
            self.assertEqual(response.status_code, 200)
        self.client.logout()
        self.client.login(username='admin_user', password='adminpass123')

    def test_stats_screen_is_staff_only(self):
        self.client.logout()
        response = self.client.get('/admin/movies/movie/stats/')
        self.assertIn(response.status_code, (302, 403))

    def test_stats_screen_renders_both_measurables(self):
        html = self._stats_html()
        self.assertIn('Most bought movie', html)
        self.assertIn('Most reviewed movie', html)

    def test_same_movie_shows_for_both_measurables(self):
        self._review(self.inception)
        self._purchase(self.inception)

        html = self._stats_html()
        self.assertIn('Most bought movie', html)
        bought = html.split('Most bought movie')[1].split('Most reviewed movie')[0]
        reviewed = html.split('Most reviewed movie')[1]

        self.assertIn('Inception', bought)
        self.assertIn('Inception', reviewed)
        self.assertIn('1', bought)

    def test_most_bought_and_most_reviewed_differ(self):
        self._review(self.inception)
        self._purchase(self.inception)
        self._purchase(self.avatar, times=2)

        html = self._stats_html()
        bought = html.split('Most bought movie')[1].split('Most reviewed movie')[0]
        reviewed = html.split('Most reviewed movie')[1]

        self.assertIn('Avatar', bought)
        self.assertNotIn('Inception', bought)
        self.assertIn('Inception', reviewed)
        self.assertNotIn('Avatar', reviewed)

    def test_stats_count_quantities(self):
        self.client.logout()
        self.client.login(username='member', password='memberpass123')
        self.client.post(f'/cart/{self.avatar.id}/add/', {'quantity': '3'})
        self.client.post('/cart/purchase/')

        item = Item.objects.get(movie=self.avatar)
        self.assertEqual(item.quantity, 3)

        self.client.logout()
        self.client.login(username='admin_user', password='adminpass123')
        html = self._stats_html()
        self.assertIn('Avatar', html)
        self.assertIn('3', html)

    def test_empty_state_message(self):
        html = self._stats_html()
        self.assertIn('No movie has been bought yet.', html)
        self.assertIn('No movie has been reviewed yet.', html)


class TopCommenterTests(TestCase):
    def setUp(self):
        self.admin_user = User.objects.create_superuser(
            'testadmin', 'admin@exmaple.com', 'testpass123'
        )
        self.user_a = User.objects.create_user(
            'user_a', password = 'testpass123'
        )
        self.user_b = User.objects.create_user(
            'user_b', password = 'testpass123'
        )
        self.movie = Movie.objects.create(
            name = 'Test Movie',
            price = 10,
            description = 'Test description'
        )
        self.url = '/admin/movies/movie/top-commenter/'
    def add_comments(self, user, count):
        for i in range(count):
            Review.objects.create(
                user = user,
                movie = self.movie,
                comment = f'Test comment {i}'
            )
    def test_admin_only(self):
        self.client.force_login(self.user_a)
        response = self.client.get(self.url)
        self.assertNotEqual(response.status_code, 200)

    def test_top_commenter(self):
        self.add_comments(self.user_a, 2)
        self.client.force_login(self.admin_user)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['top_commenter']['user__username'], 'user_a')
        self.assertEqual(response.context['top_commenter']['comment_count'], 2)
        self.add_comments(self.user_b, 3)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['top_commenter']['user__username'], 'user_b')
        self.assertEqual(response.context['top_commenter']['comment_count'], 3)

    def test_no_comments(self):
        self.client.force_login(self.admin_user)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'No comments have been posted yet.')


        