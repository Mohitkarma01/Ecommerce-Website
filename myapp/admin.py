from django.contrib import admin
from .models import RegisterUser
from .models import Product, CartItem


admin.site.register(Product)
admin.site.register(CartItem)

@admin.register(RegisterUser)
class RegisterUserAdmin(admin.ModelAdmin):
    list_display = ('id', 'username', 'email', 'number')
    search_fields = ('username', 'email')
