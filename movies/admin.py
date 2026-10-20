from django.contrib import admin
from django.db.models import Count, Sum
from django.shortcuts import render
from django.urls import path
from cart.models import Item
from .models import Movie, Review


def stats_view(request):
    """Admin screen showing the most bought and the most reviewed movie.

    Both measurables are reported independently, so a single movie can show up
    twice (once as most bought, once as most reviewed) when it leads both.
    """
    most_bought = (
        Item.objects
        .values('movie_id', 'movie__name')
        .annotate(total=Sum('quantity'))
        .order_by('-total', 'movie__name')
        .first()
    )

    most_reviewed = (
        Review.objects
        .values('movie_id', 'movie__name')
        .annotate(total=Count('id'))
        .order_by('-total', 'movie__name')
        .first()
    )

    return render(request, 'admin/stats.html', {
        'most_bought': most_bought,
        'most_reviewed': most_reviewed,
    })


class MovieAdmin(admin.ModelAdmin):
    ordering = ['name']
    search_fields = ['name']

    def get_urls(self):
        return [
            path('stats/', self.admin_site.admin_view(stats_view),
                name='movies_movie_stats'),
        ] + super().get_urls()


admin.site.register(Movie, MovieAdmin)
admin.site.register(Review)
