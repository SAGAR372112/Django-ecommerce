from django.shortcuts import render, redirect, get_object_or_404

from orders.models import Order, OrderProduct
from .forms import RegistrationForm, UserForm, UserProfileForm
from .models import Account, UserProfile
from django.contrib import messages, auth
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse

# verification email
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import EmailMessage

from carts.models import Cart, CartItem
from carts.views import _cart_id

import requests

def register(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            first_name = form.cleaned_data['first_name']
            last_name = form.cleaned_data['last_name']
            phone_number = form.cleaned_data['phone_number']
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            username = email.split('@')[0].capitalize()
            user = Account.objects.create_user(first_name=first_name, last_name=last_name, email=email, username=username, password=password)
            user.phone_number = phone_number
            user.save()

            # USER ACTIVATION
            current_site = get_current_site(request) 
            mail_subject = 'Please activate your account'
            message = render_to_string('accounts/account_verification_email.html', {
                'user': user,
                'domain': current_site,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': default_token_generator.make_token(user),
            })
            to_email = email
            send_email = EmailMessage(mail_subject, message, to=[to_email])
            send_email.send()
            
            return redirect('/accounts/login/?command=verification&email='+to_email)
    else:
        form = RegistrationForm()
    context = {
        'form': form
    }
    return render(request, 'accounts/register.html', context)

def login(request):
    if request.method == 'POST':
        email = request.POST['email']
        password = request.POST['password']

        user = auth.authenticate(email=email, password=password)

        if user is not None:
            try:

                cart = Cart.objects.get(cart_id=_cart_id(request))
                is_cart_item_exists = CartItem.objects.filter( cart=cart).exists()
                if is_cart_item_exists:
                    cart_item = CartItem.objects.filter(cart=cart)


                    # for getting the product variation by cart id
                    product_variation = []  
                    for item in cart_item:
                        variation = item.variations.all()
                        product_variation.append(list(variation))

                    # for getting the product variation by user id
                    cart_item = CartItem.objects.filter(user=user)
                    existing_variation_list = []
                    id = []
                    for item in cart_item:
                        existing_variation = item.variations.all()
                        existing_variation_list.append(list(existing_variation))
                        id.append(item.id)

                    # product_variation = [1, 2, 3, 6]
                    # existing_variation_list = [4, 2, 1]

                    # for checking the product variation is already exists or not
                    for pr in product_variation:
                        if pr in existing_variation_list:
                            index = existing_variation_list.index(pr)
                            item_id = id[index]
                            item = CartItem.objects.get(id=item_id)
                            item.quantity += 1
                            item.user = user
                            item.save()
                            #  if the product variation is not exists then just add the product to the cart not update the quantity
                        else:
                            item = CartItem.objects.filter(cart=cart)
                            for item in cart_item:
                                item.user = user
                                item.save()
                        
            except Cart.DoesNotExist:
                cart= Cart.objects.create(
                    cart_id=_cart_id(request)
                )
                cart.user = user
                cart.save()
                
            auth.login(request, user)
            messages.success(request, 'You are now logged in.')
            url = request.META.get('HTTP_REFERER')
            try:
                query = requests.utils.urlparse(url).query
                # next=/cart/checkout/
                params = dict(x.split('=') for x in query.split('&'))
                if 'next' in params:
                    next_url = params['next']
                    return redirect(next_url)
            except:
                return redirect('dashboard')
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid login credentials')
            return redirect('login')
    return render(request, 'accounts/login.html')

@login_required(login_url='login')      
def logout(request):
    auth.logout(request)    
    messages.success(request, 'You are now logged out.')
    return redirect('login')

def activate(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64)
        user = Account._default_manager.get(pk=uid)
    except(TypeError, ValueError, OverflowError, Account.DoesNotExist):
        user = None
    
    if user is not None and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        messages.success(request, 'Congretulations !!! Your account is activated.')
        return redirect('login')
    else:
        messages.error(request, 'Invalid activation link')
        return redirect('register')

@login_required(login_url='login')
def dashboard(request):
    try:
        orders = Order.objects.order_by('-created_at').filter(user_id=request.user.id, is_ordered=True)
        orders_count = 0
        if orders:
            orders_count = orders.count()
            
        userprofile = UserProfile.objects.get(user_id=request.user.id)
        context = {
            'orders_count': orders_count,
            'userprofile': userprofile,
        }
        return render(request, 'accounts/dashboard.html', context)
    except:
        return render(request, 'accounts/dashboard.html')

def forgot_password(request):
    if request.method == 'POST':
        email = request.POST['email']
        if Account.objects.filter(email=email).exists():
            user = Account.objects.get(email__exact=email)

            #  RESET PASSWORD
            current_site = get_current_site(request) 
            mail_subject = 'Reset Your Password'
            message = render_to_string('accounts/reset_password_email.html', {
                'user': user,
                'domain': current_site,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': default_token_generator.make_token(user),
            })
            to_email = email
            send_email = EmailMessage(mail_subject, message, to=[to_email])
            send_email.send()
            messages.success(request, 'Password reset email has been sent to your email address.')
            return redirect('login')
        else:
            messages.error(request, 'Account does not exist!')
            return redirect('forgot_password')
    return render(request, 'accounts/forgot_password.html')

def reset_password_validate(request, uidb64, token):

    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = Account._default_manager.get(pk=uid)
    except(TypeError, ValueError, OverflowError, Account.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        request.session['uid'] = uid
        messages.success(request, 'Please reset your password')
        return redirect('reset_password')
    else:
        messages.error(request, 'This link has expired!')
        return redirect('forgot_password')

def reset_password(request):
   if request.method == 'POST':
       password = request.POST['password']
       confirm_password = request.POST['confirm_password']
       if password == confirm_password:
           uid = request.session.get('uid')
           user = Account.objects.get(pk=uid)
           user.set_password(password)
           user.save()
           messages.success(request, 'Password reset successful')
           return redirect('login')
       else:
           messages.error(request, 'Password do not match!')
           return redirect('reset_password')
   else:
       return render(request, 'accounts/reset_password.html')  

@login_required(login_url='login')
def my_orders(request):
    orders = Order.objects.filter(user=request.user, is_ordered=True).order_by('-created_at')
    context = {
        'orders': orders,
    }
    return render(request, 'accounts/my_orders.html', context)

@login_required(login_url='login')
def edit_profile(request):
    # Get or create user profile
    userprofile, created = UserProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        userform = UserForm(request.POST, instance=request.user)
        profileform = UserProfileForm(request.POST, request.FILES, instance=userprofile)
        if userform.is_valid() and profileform.is_valid():
            userform.save()
            profileform.save()
            messages.success(request, 'Profile updated successfully')
            return redirect('edit_profile')     
    else:
        userform = UserForm(instance=request.user)
        profileform = UserProfileForm(instance=userprofile)

    context = { 
        'userform': userform,
        'profileform': profileform,
    }
    return render(request, 'accounts/edit_profile.html', context)

@login_required(login_url='login')
def change_password(request):
    if request.method == 'POST':
        current_password = request.POST['current_password']
        new_password = request.POST['new_password']
        confirm_new_password = request.POST['confirm_new_password']

        user = Account.objects.get(username__exact=request.user.username)

        if new_password == confirm_new_password:    
            success = user.check_password(current_password)
            if success:
                user.set_password(new_password)
                user.save() 
                #auth.logout(request)    
                messages.success(request, 'Password updated successfully')
                return redirect('login')
            else:
                messages.error(request, 'Please enter valid current password')
                return redirect('change_password')
        else:
            messages.error(request, 'Password does not match!')
            return redirect('change_password')
    else:
        return render(request, 'accounts/change_password.html')

@login_required(login_url='login')
def order_detail(request, order_id):
    order_detail = OrderProduct.objects.filter(order__order_number=order_id)
    order = Order.objects.get(order_number=order_id)
    subtotal = 0
    tax = 2
    for i in order_detail:
        subtotal += i.product_price * i.quantity
    tax = 2 * subtotal / 100
    total = subtotal + tax
    context = {
        'order_detail': order_detail,
        'order': order,
        'subtotal': subtotal,
        'tax': tax,
        'total': total,
    }
    return render(request, 'accounts/order_detail.html', context)
