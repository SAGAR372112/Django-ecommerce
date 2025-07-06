from django.shortcuts import render, redirect
from store.models import Product, Variation
from .models import Cart, CartItem
from django.http import HttpResponse
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import get_object_or_404

from django.contrib.auth.decorators import login_required

# for getting the cart id from session-id is present in the cookie session
def _cart_id(request):
    cart = request.session.session_key
    if not cart:
        cart = request.session.create()
    return cart

# for adding the cart item
def add_cart(request, product_id):

    current_user = request.user
    # for getting the product
    product = Product.objects.get(id=product_id)

    # if current user is authenticated
    if current_user.is_authenticated:
        product_variation = []
        if request.method == 'POST':
            for key, value in request.POST.items():
                if key in ['color', 'size'] and value:
                    try:
                        variation = Variation.objects.filter(
                            product=product, 
                            variation_category__iexact=key, 
                            variation_value__iexact=value
                        ).first()
                        if variation:
                            product_variation.append(variation)
                    except Variation.DoesNotExist:
                        pass

        # for checking if the cart item already exists
        is_cart_item_exists = CartItem.objects.filter(product=product, user=current_user).exists()
                
        # for checking existing variation list and current variation list          
        if is_cart_item_exists:
            cart_item = CartItem.objects.filter(product=product, user=current_user)

            # for getting the existing variation list and id list   
            existing_variation_list = []
            id = []
            for item in cart_item:
                existing_variation = item.variations.all()
                existing_variation_list.append(list(existing_variation))
                id.append(item.id)

            # incrementing the quantity of the cart item
            if product_variation in existing_variation_list:
                index = existing_variation_list.index(product_variation)
                item_id = id[index]
                item = CartItem.objects.get(product=product, id=item_id)
                item.quantity += 1
                item.save()

            # for creating the cart item
            else:
                item = CartItem.objects.create(
                    product=product,
                    quantity=1,
                    user=current_user
                )
                if len(product_variation) > 0:
                    item.variations.clear()
                    item.variations.add(*product_variation)
                item.save()
        # If the user is not authenticated
        else:
            cart_item = CartItem.objects.create(
                product=product,
                quantity=1,
                user=current_user
                )
            if len(product_variation) > 0:
                cart_item.variations.clear()
                cart_item.variations.add(*product_variation)
            cart_item.save()
        return redirect('cart')

    else:    
        product_variation = []
        if request.method == 'POST':
            for item in request.POST:
                for key, value in request.POST.items():
                    if key in ['color', 'size'] and value:
                        try:
                            variation = Variation.objects.filter(
                                product=product, 
                                variation_category__iexact=key, 
                                variation_value__iexact=value
                            ).first()
                            if variation:
                                product_variation.append(variation)
                        except Variation.DoesNotExist:
                            pass
    
        # for getting the cart using the cart_id present in the session
        try:
            cart = Cart.objects.get(cart_id=_cart_id(request)) #get the cart using the cart_id present in the session
        except Cart.DoesNotExist:
            cart = Cart.objects.create(cart_id=_cart_id(request))
        cart.save()

        # for checking if the cart item already exists
        is_cart_item_exists = CartItem.objects.filter(product=product, cart=cart).exists()
                
        # for checking existing variation list and current variation list          
        if is_cart_item_exists:
            cart_item = CartItem.objects.filter(product=product, cart=cart)

            #existing_variation -> database
            #current variation -> product_variation
            #item in cart_item -> cart_item

            # for getting the existing variation list and id list   
            existing_variation_list = []
            id = []
            for item in cart_item:
                existing_variation = item.variations.all()
                existing_variation_list.append(list(existing_variation))
                id.append(item.id)

            # incrementing the quantity of the cart item
            if product_variation in existing_variation_list:
                index = existing_variation_list.index(product_variation)
                item_id = id[index]
                item = CartItem.objects.get(product=product, id=item_id)
                item.quantity += 1
                item.save()

            # for creating the cart item
            else:
                item = CartItem.objects.create(
                    product=product,
                    quantity=1,
                    cart=cart
                )
                if len(product_variation) > 0:
                    item.variations.clear()
                    item.variations.add(*product_variation)
                item.save()
        # for creating and saving cart item
        else:
            cart_item = CartItem.objects.create(
                product=product,
                quantity=1,
                cart=cart
                )
            if len(product_variation) > 0:
                cart_item.variations.clear()
                cart_item.variations.add(*product_variation)
            cart_item.save()
        return redirect('cart')

# for removing the cart item by reducing the quantity
def remove_cart(request, product_id, cart_item_id):
    
    product = get_object_or_404(Product, id=product_id)
    try:
        if request.user.is_authenticated:
            cart_item = CartItem.objects.get(product=product, user=request.user, id=cart_item_id)
        else:
            cart_item = CartItem.objects.get(product=product, cart=cart, id=cart_item_id)
        if cart_item.quantity > 1:
            cart_item.quantity -= 1
            cart_item.save()
        else:
            cart_item.delete()
    except Exception as e:
        pass
    return redirect('cart')

# for removing the cart all quantity item if quantity is more then one
def remove_cart_item(request, product_id, cart_item_id):
    cart = Cart.objects.get(cart_id=_cart_id(request))
    product = get_object_or_404(Product, id=product_id)
    if request.user.is_authenticated:
        cart_item = CartItem.objects.get(product=product, user=request.user, id=cart_item_id)
    else:
        cart_item = CartItem.objects.get(product=product, cart=cart, id=cart_item_id)
    cart_item.delete()
    return redirect('cart')

# for displaying the cart items
def cart(request, total=0, quantity=0, cart_items=None):
    try:
        tax = 0
        grand_total = 0
        # for checking if the user is authenticated
        if request.user.is_authenticated:   
            cart_items = CartItem.objects.filter(user=request.user, is_active=True)
        else:
            cart = Cart.objects.get(cart_id=_cart_id(request))
            cart_items = CartItem.objects.filter(cart=cart, is_active=True)
        for cart_item in cart_items:
            total += (cart_item.product.price * cart_item.quantity)
            quantity += cart_item.quantity
        tax = (2 * total)/100
        grand_total = total + tax
    except ObjectDoesNotExist:
        pass

    context = {
        'total': total,
        'quantity': quantity,
        'cart_items': cart_items,
        'tax': tax,
        'grand_total': grand_total,
    }
    return render(request, 'store/cart.html', context)

# for displaying the checkout page
@login_required(login_url='login')
def checkout(request, total=0, quantity=0, cart_items=None):
    try:
        tax = 0
        grand_total = 0
        if request.user.is_authenticated:   
            cart_items = CartItem.objects.filter(user=request.user, is_active=True)
        else:
            cart = Cart.objects.get(cart_id=_cart_id(request))
            cart_items = CartItem.objects.filter(cart=cart, is_active=True)
        for cart_item in cart_items:
            total += (cart_item.product.price * cart_item.quantity)
            quantity += cart_item.quantity
        tax = (2 * total)/100
        grand_total = total + tax
    except ObjectDoesNotExist:
        pass

    context = {
        'total': total,
        'quantity': quantity,
        'cart_items': cart_items,
        'tax': tax,
        'grand_total': grand_total,
    }
    return render(request, 'store/checkout.html', context)
