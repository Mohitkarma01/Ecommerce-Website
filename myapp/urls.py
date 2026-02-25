# from django.urls import path
# from . import views

# urlpatterns = [
#     # Home & Auth
#     path('', views.homePage, name='index'),
#     path('register/', views.register, name='register'),
#     path('login/', views.login, name='login'),
#     path('logout/', views.logout, name='logout'),
    
#     # Cart Operations
#     path('cart/add/<int:product_id>/', views.add_to_cart, name='add_to_cart'),  # AJAX POST
#     path('cart/buy-now/<int:product_id>/', views.buy_now, name='buy_now'),      # GET
#     path('cart/', views.view_cart, name='view_cart'),
#     path('cart/increase/<int:item_id>/', views.increase_quantity, name='increase_quantity'),
#     path('cart/decrease/<int:item_id>/', views.decrease_quantity, name='decrease_quantity'),
#     path('cart/remove/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
    
#     # Checkout
#    # Checkout URLs
#     path('checkout/', views.checkout, name='checkout'),
#     path('order-success/<int:order_id>/', views.order_success, name='order_success'),
    
#     # Other Pages
#     path('search/', views.search, name='search'),
#     path('service/', views.service, name='service'),
#     path('about/', views.about, name='about'),
#     path('contact/', views.contact, name='contact'),
#     path('save-spin/', views.save_spin, name='save_spin'),

#     # Order History
#     path('my-orders/', views.my_orders, name='my_orders'),
#     path('order-detail/<int:order_id>/', views.order_detail, name='order_detail'),

#      # Live Chat
#     path('chat/', views.chat, name='chat'),
# ]

from django.urls import path
from . import views

urlpatterns = [
    # Home & Auth
    path('', views.homePage, name='index'),
    path('register/', views.register, name='register'),
    path('login/', views.login, name='login'),
    path('logout/', views.logout, name='logout'),
    
    # Cart Operations
    path('cart/add/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/buy-now/<int:product_id>/', views.buy_now, name='buy_now'),
    path('cart/', views.view_cart, name='view_cart'),
    path('cart/increase/<int:item_id>/', views.increase_quantity, name='increase_quantity'),
    path('cart/decrease/<int:item_id>/', views.decrease_quantity, name='decrease_quantity'),
    path('cart/remove/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
    
    # Checkout
    path('checkout/', views.checkout, name='checkout'),
    path('order-success/<int:order_id>/', views.order_success, name='order_success'),
    
    # Other Pages
    path('search/', views.search, name='search'),
    path('service/', views.service, name='service'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    path('save-spin/', views.save_spin, name='save_spin'),

    # Order History
    path('my-orders/', views.my_orders, name='my_orders'),
    path('order-detail/<int:order_id>/', views.order_detail, name='order_detail'),

    # Live Chat
    path('chat/', views.chat, name='chat'),
    
    # ✅ NEW URLS FOR BADGE SYSTEM
    path('profile/', views.user_profile, name='user_profile'),  # ✅ Add this line
    path('leaderboard/', views.leaderboard, name='leaderboard'),  # ✅ Add this line
]