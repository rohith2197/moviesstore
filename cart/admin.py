from django.contrib import admin
from django.contrib.auth.models import User
from django.db.models import Count
from django.shortcuts import render
from django.urls import path
from .models import Order, Item

class OrderAdmin(admin.ModelAdmin):
    def get_urls(self):
        return [ path('top-users/', 
                      self.admin_site.admin_view(self.top_users_view),
                      name='cart_order_top_users'),
                ] + super().get_urls()

    def top_users_view(self, request):
        limit = request.GET.get('limit', '').strip()
        users = User.objects.annotate(
                    purchase_count=Count('order__item')
                ).order_by('-purchase_count', 'username')

        if limit.isdigit() and int(limit) > 0:
            users = users[:int(limit)]

        context = {
                    **self.admin_site.each_context(request),
                    'title': 'Top users by purchases',
                    'users': users,
                    'limit': limit,
                }

        return render(request, 'admin/top_users.html', context)

admin.site.register(Order, OrderAdmin)
admin.site.register(Item)
