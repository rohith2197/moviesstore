from django.shortcuts import render
from django.shortcuts import get_object_or_404, redirect
from movies.models import Movie
from .utils import calculate_cart_total
from .models import Order, Item
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Sum

def index(request):
    cart_total = 0
    movies_in_cart = []
    cart = request.session.get('cart', {})
    movie_ids = list(cart.keys())
    if (movie_ids != []):
        movies_in_cart = Movie.objects.filter(id__in=movie_ids)
        cart_total = calculate_cart_total(cart, movies_in_cart)

    template_data = {}
    template_data['title'] = 'Cart'
    template_data['movies_in_cart'] = movies_in_cart
    template_data['cart_total'] = cart_total
    return render(request, 'cart/index.html', {'template_data': template_data})

def add(request, id):
    get_object_or_404(Movie, id=id)
    cart = request.session.get('cart', {})
    cart[id] = request.POST['quantity']
    request.session['cart'] = cart
    return redirect('cart.index')

def clear(request):
    request.session['cart'] = {}
    return redirect('cart.index')

@login_required
def purchase(request):
    if request.method != 'POST':
        return redirect('cart.index')
    cart = request.session.get('cart', {})
    movie_ids = list(cart.keys())
    if (movie_ids == []):
        return redirect('cart.index')
    movies_in_cart = Movie.objects.filter(id__in=movie_ids)
    cart_total = calculate_cart_total(cart, movies_in_cart)
    order = Order()
    order.user = request.user
    order.total = cart_total
    if request.POST.get('lat', '') != '' and request.POST.get('lng', '') != '':
        order.region_id = str(int(float(request.POST['lat']))) + ',' + str(int(float(request.POST['lng'])))
    order.save()
    for movie in movies_in_cart:
        item = Item()
        item.movie = movie
        item.price = movie.price
        item.order = order
        item.quantity = cart[str(movie.id)]
        item.save()
    request.session['cart'] = {}
    template_data = {}
    template_data['title'] = 'Purchase confirmation'
    template_data['order_id'] = order.id
    return render(request, 'cart/purchase.html',
        {'template_data': template_data})

def trending_map(request):
    # movies sold per region, most first
    regions = list(Item.objects.exclude(order__region_id='')
        .values('order__region_id')
        .annotate(count=Sum('quantity'))
        .order_by('-count'))

    # best-selling movie inside each region
    for r in regions:
        top = (Item.objects.filter(order__region_id=r['order__region_id'])
            .values('movie__name')
            .annotate(count=Sum('quantity'))
            .order_by('-count')
            .first())
        r['region_id'] = r.pop('order__region_id')
        r['top_movie'] = top['movie__name'] if top else ''
        r['top_movie_count'] = top['count'] if top else 0

    template_data = {}
    template_data['title'] = 'Local Popularity Map'
    template_data['regions'] = regions
    return render(request, 'cart/trending.html', {'template_data': template_data})

def region_top_movies(request, region_id):
    # best-selling movies inside one region
    movies = (Item.objects.filter(order__region_id=region_id)
        .values('movie__id', 'movie__name', 'movie__image')
        .annotate(count=Sum('quantity'))
        .order_by('-count')[:5])

    template_data = {}
    template_data['title'] = 'Top Movies'
    template_data['region_id'] = region_id
    template_data['movies'] = movies
    return render(request, 'cart/region.html', {'template_data': template_data})
