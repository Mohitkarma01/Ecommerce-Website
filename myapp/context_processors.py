from .models import CartItem

def cart_count(request):
    """Add cart count to all templates"""
    if request.user.is_authenticated:
        count = CartItem.objects.filter(user=request.user).count()
    else:
        count = 0
    return {'cart_count': count}