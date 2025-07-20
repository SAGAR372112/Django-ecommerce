from django.shortcuts import render
from store.models import Product, ReviewRating

def home(request):
    products = Product.objects.all().filter(is_available=True).order_by('-created_date')
    product_reviews = {}
    # Get the reviews

    for product in products:
        reviews = ReviewRating.objects.filter(product_id=product.id, status=True)
        product_reviews[product.id] = reviews

    context = {
        'products': products,
         'product_reviews': product_reviews,
    }
    return render( request, 'home.html', context)