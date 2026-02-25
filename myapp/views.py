from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.models import User
from django.views.decorators.http import require_POST
import json
from django.db.models import Q, Sum
from decimal import Decimal
from .models import Product, CartItem, Order, OrderItem, Address, SpinHistory, UserProfile
# ================= SIGNALS FOR USER PROFILE =================
from django.db.models.signals import post_save
from django.dispatch import receiver


# mera
from django.views.decorators.csrf import csrf_exempt


# ================= HOME =================
def homePage(request):
    products = Product.objects.all()
    
    # Apply 5% discount to all products
    for product in products:
        if not product.discounted_price:
            product.discounted_price = product.price * Decimal('0.95')
    
    cart_count = 0
    user_profile = None
    badge_info = None
    
    if request.user.is_authenticated:
        cart_count = CartItem.objects.filter(user=request.user).count()
        
        # Get user badge info
        try:
            user_profile = UserProfile.objects.get(user=request.user)
            badge_info = {
                'badge': user_profile.badge,
                'icon': user_profile.get_badge_icon(),
                'discount': user_profile.discount_percentage,
                'loyalty_points': user_profile.loyalty_points,
                'total_spent': user_profile.total_spent,
            }
        except UserProfile.DoesNotExist:
            user_profile = None
    
    return render(request, 'index.html', {
        'products': products,
        'cart_count': cart_count,
        'user_profile': user_profile,
        'badge_info': badge_info,
    })
# ================= REGISTER =================
def register(request):
    if request.method == "POST":
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        # Validate
        if not username or not email or not password:
            messages.error(request, "All fields are required")
            return redirect('register')
        
        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already taken")
            return redirect('register')
        
        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already registered")
            return redirect('register')
        
        # Create user
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )
        
        # Auto login
        user = authenticate(username=username, password=password)
        if user:
            auth_login(request, user)
            messages.success(request, "Registration successful!")
            return redirect('index')
    
    return render(request, 'register.html')
# ================= LOGIN =================
def login(request):
    if request.method == "POST":
        email_or_username = request.POST.get('email')
        password = request.POST.get('password')
        
        # Try to find user by email first
        try:
            user_by_email = User.objects.get(email=email_or_username)
            user = authenticate(username=user_by_email.username, password=password)
        except User.DoesNotExist:
            # If not found by email, try username
            user = authenticate(username=email_or_username, password=password)
        
        if user is not None:
            auth_login(request, user)
            messages.success(request, "Login successful!")
            return redirect('index')
        else:
            messages.error(request, "Invalid email/username or password")
    
    return render(request, 'login.html')

# ================= LOGOUT =================
def logout(request):
    auth_logout(request)
    messages.success(request, "Logged out successfully!")
    return redirect('index')

# ================= ADD TO CART (AJAX) =================
@require_POST
def add_to_cart(request, product_id):
    """AJAX only - Add to cart without page reload"""
    if not request.user.is_authenticated:
        return JsonResponse({
            "status": "error",
            "message": "Please login first",
            "redirect": "/login/"
        },status=401)
    
    product = get_object_or_404(Product, id=product_id)
    
    cart_item, created = CartItem.objects.get_or_create(
        user=request.user,
        product=product,
        defaults={'quantity': 1}
    )
    
    if not created:
        cart_item.quantity += 1
        cart_item.save()
    
    cart_items = CartItem.objects.filter(user=request.user)
    cart_count = sum(item.quantity for item in cart_items)
    
    return JsonResponse({
        "status": "success",
        "message": f"{product.name} added to cart!",
        "cart_count": cart_count,
        "product_name": product.name
    },status=200)

# ================= BUY NOW =================
def buy_now(request, product_id):
    """Industry standard Buy Now - adds to cart and redirects to checkout"""
    if not request.user.is_authenticated:
        messages.info(request, "Please login to continue")
        return redirect('login')
    
    product = get_object_or_404(Product, id=product_id)
    
    # Clear existing cart items for Buy Now flow
    CartItem.objects.filter(user=request.user).delete()
    
    # Create new cart item with quantity 1
    CartItem.objects.create(
        user=request.user,
        product=product,
        quantity=1
    )
    
    messages.success(request, f"Ready to purchase {product.name}")
    return redirect('checkout')

# ================= VIEW CART =================
def view_cart(request):
    if not request.user.is_authenticated:
        messages.error(request, "Please login to view cart")
        return redirect('login')
    
    items = CartItem.objects.filter(user=request.user)
    total = sum(item.total() for item in items)
    
    return render(request, 'cart.html', {
        'items': items,
        'total': total
    })

# ================= INCREASE QUANTITY =================
def increase_quantity(request, item_id):
    """Increase quantity of cart item"""
    if not request.user.is_authenticated:
        return redirect('login')
    
    item = get_object_or_404(CartItem, id=item_id, user=request.user)
    item.quantity += 1
    item.save()
    
    return redirect('view_cart')

# ================= DECREASE QUANTITY =================
def decrease_quantity(request, item_id):
    """Decrease quantity of cart item"""
    if not request.user.is_authenticated:
        return redirect('login')
    
    item = get_object_or_404(CartItem, id=item_id, user=request.user)
    
    if item.quantity > 1:
        item.quantity -= 1
        item.save()
    else:
        item.delete()
    
    return redirect('view_cart')

# ================= REMOVE FROM CART =================
def remove_from_cart(request, item_id):
    """Remove item from cart completely"""
    if not request.user.is_authenticated:
        return redirect('login')
    
    item = get_object_or_404(CartItem, id=item_id, user=request.user)
    item.delete()
    
    return redirect('view_cart')

# ================= CHECKOUT =================
def checkout(request):
    if not request.user.is_authenticated:
        messages.error(request, "Please login to checkout")
        return redirect('login')
    
    cart_items = CartItem.objects.filter(user=request.user)
    
    if not cart_items.exists():
        messages.error(request, "Your cart is empty")
        return redirect('view_cart')
    
    # Calculate total with 5% product discount
    total = sum(item.total() for item in cart_items)
    
    # Apply user's badge discount
    try:
        profile = request.user.profile
        user_discount = (total * profile.discount_percentage) / 100
        final_total = total - user_discount
    except UserProfile.DoesNotExist:
        user_discount = 0
        final_total = total
    
    if request.method == "POST":
        # Get or update address
        address, created = Address.objects.get_or_create(
            user=request.user,
            defaults={
                "full_address": request.POST.get('address'),
                "city": request.POST.get('city'),
                "pincode": request.POST.get('pincode'),
                "phone": request.POST.get('phone'),
            }
        )
        
        if not created:
            address.full_address = request.POST.get('address')
            address.city = request.POST.get('city')
            address.pincode = request.POST.get('pincode')
            address.phone = request.POST.get('phone')
            address.save()
        
        # Create order with discounts
        order = Order.objects.create(
            user=request.user,
            address=address,
            total=total,
            discount_applied=user_discount,
            final_total=final_total,
            status='Processing'
        )
        
        # Create order items with discounted prices
        for cart_item in cart_items:
            OrderItem.objects.create(
                order=order,
                product=cart_item.product,
                quantity=cart_item.quantity,
                price=cart_item.product.price,
                discounted_price=cart_item.product.get_discounted_price()
            )
        
        # Clear cart
        cart_items.delete()
        
        # Show success message with savings
        savings = total - final_total
        messages.success(request, f"Order #{order.id} placed successfully! You saved ₹{savings:.2f}")
        return redirect('order_success', order_id=order.id)
    
    # Get existing address
    try:
        address = Address.objects.get(user=request.user)
    except Address.DoesNotExist:
        address = None
    
    # Get user profile for discount info
    try:
        profile = request.user.profile
        user_discount = profile.discount_percentage
        user_badge = profile.badge
        badge_icon = profile.get_badge_icon()
    except UserProfile.DoesNotExist:
        user_discount = 0
        user_badge = 'NEW'
        badge_icon = '🆕'
    
    return render(request, 'checkout.html', {
        'cart_items': cart_items,
        'total': total,
        'final_total': final_total,
        'user_discount': user_discount,
        'user_badge': user_badge,
        'badge_icon': badge_icon,
        'address': address,
        'savings': total - final_total if final_total else 0,
    })

# ================= ORDER SUCCESS =================
def order_success(request, order_id):
    """Show order details after successful purchase"""
    order = get_object_or_404(Order, id=order_id, user=request.user)
    order_items = OrderItem.objects.filter(order=order)
    
    # Calculate totals
    items_total = sum(item.get_item_total() for item in order_items)
    
    # Get user badge info
    try:
        profile = request.user.profile
        badge_info = {
            'badge': profile.badge,
            'icon': profile.get_badge_icon(),
            'discount': profile.discount_percentage,
        }
    except UserProfile.DoesNotExist:
        badge_info = None
    
    return render(request, 'order_success.html', {
        'order': order,
        'order_items': order_items,
        'items_total': items_total,
        'badge_info': badge_info,
    })
# ================= SAVE SPIN =================
def save_spin(request):
    if request.method == "POST":
        if not request.user.is_authenticated:
            return JsonResponse({"status": "error", "message": "Not logged in"})
        
        offer = request.POST.get('offer')
        SpinHistory.objects.create(user=request.user, offer=offer)
        
        return JsonResponse({"status": "saved"})
    return JsonResponse({"status": "error"})

def my_orders(request):
    """Show user's order history"""
    if not request.user.is_authenticated:
        messages.error(request, "Please login to view orders")
        return redirect('login')
    
    # Get orders for current user
    orders = []
    try:
        from .models import Order
        orders = Order.objects.filter(user=request.user).order_by('-created_at')
    except:
        pass  # If Order model doesn't exist yet
    
    return render(request, 'my_orders.html', {
        'orders': orders
    })

def order_detail(request, order_id):
    """Show detailed view of a specific order"""
    if not request.user.is_authenticated:
        return redirect('login')
    
    order = get_object_or_404(Order, id=order_id, user=request.user)
    order_items = OrderItem.objects.filter(order=order)
    
    return render(request, 'order_detail.html', {
        'order': order,
        'order_items': order_items
    })

def search(request):
    query = request.GET.get('q', '')
    products = Product.objects.filter(name__icontains=query) if query else []
    return render(request, 'search.html', {'products': products, 'query': query})


def service(request):
    cart_count = 0
    if request.user.is_authenticated:
        cart_count = CartItem.objects.filter(user=request.user).count()
    
    return render(request, "service.html", {'cart_count': cart_count})

def about(request):
    cart_count = 0
    if request.user.is_authenticated:
        cart_count = CartItem.objects.filter(user=request.user).count()
    
    return render(request, "about.html", {'cart_count': cart_count})

def contact(request):
    cart_count = 0
    if request.user.is_authenticated:
        cart_count = CartItem.objects.filter(user=request.user).count()
    
    return render(request, "contact.html", {'cart_count': cart_count})


def chat(request):
    """Live Chat Support Page"""
    if not request.user.is_authenticated:
        messages.error(request, "Please login to access live chat")
        return redirect('login')
    
    return render(request, 'chat.html')



@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Create UserProfile when new user is created"""
    if created:
        UserProfile.objects.create(user=instance)



# ================= MY ORDERS =================
# ================= MY ORDERS =================

# ================= ORDER DETAIL =================

# ================= SEARCH =================

# ================= STATIC PAGES =================

# ================= CHAT VIEW =================


@receiver(post_save, sender=Order)
def update_user_profile(sender, instance, created, **kwargs):
    """Update user's total spent and badge when order is placed"""
    if created:
        try:
            profile = instance.user.profile
            profile.total_spent += instance.total
            profile.total_orders += 1
            profile.update_badge()  # This will update badge and loyalty points
        except UserProfile.DoesNotExist:
            UserProfile.objects.create(
                user=instance.user,
                total_spent=instance.total,
                total_orders=1
            )

# ================= HOME WITH DISCOUNTS =================


# ================= UPDATED CHECKOUT WITH DISCOUNTS =================

# ================= UPDATED ORDER SUCCESS =================


# ================= USER PROFILE VIEW =================
def user_profile(request):
    """Show user's profile with badge and rewards"""
    if not request.user.is_authenticated:
        messages.error(request, "Please login to view profile")
        return redirect('login')
    
    try:
        profile = UserProfile.objects.get(user=request.user)
        
        # Get user's order history
        orders = Order.objects.filter(user=request.user).order_by('-created_at')[:10]
        
        # Badge requirements for next level
        badge_requirements = {
            'NEW': {'next': 'BRONZE', 'amount': 500, 'current': profile.total_spent},
            'BRONZE': {'next': 'SILVER', 'amount': 1000, 'current': profile.total_spent},
            'SILVER': {'next': 'GOLD', 'amount': 2500, 'current': profile.total_spent},
            'GOLD': {'next': 'PLATINUM', 'amount': 5000, 'current': profile.total_spent},
            'PLATINUM': {'next': 'DIAMOND', 'amount': 10000, 'current': profile.total_spent},
            'DIAMOND': {'next': None, 'amount': None, 'current': profile.total_spent},
        }
        
        next_level = badge_requirements.get(profile.badge, {})
        
    except UserProfile.DoesNotExist:
        profile = None
        orders = []
        next_level = {}
    
    return render(request, 'profile.html', {
        'profile': profile,
        'orders': orders,
        'next_level': next_level,
    })

# ================= LEADERBOARD VIEW =================
def leaderboard(request):
    """Show top users by spending"""
    top_users = UserProfile.objects.order_by('-total_spent')[:10]
    
    return render(request, 'leaderboard.html', {
        'top_users': top_users,
    })

# Add these new URLs to urls.py
"""
path('profile/', views.user_profile, name='user_profile'),
path('leaderboard/', views.leaderboard, name='leaderboard'),
"""