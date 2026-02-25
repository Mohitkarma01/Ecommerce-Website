from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator

# ❌ RegisterUser ko cart/order flow me use nahi karenge
class RegisterUser(models.Model):
    username = models.CharField(max_length=100)
    number = models.CharField(max_length=15)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=100)

    def __str__(self):
        return self.username


# ✅ Product (almost same)
class Product(models.Model):
    name = models.CharField(max_length=200)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    discounted_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    quantity = models.IntegerField(default=1)
    image = models.ImageField(upload_to='products/', null=True, blank=True)
    weight = models.DecimalField(max_digits=5, decimal_places=2)
    unit = models.CharField(
        max_length=10,
        choices=[('kg', 'Kilogram'), ('g', 'Gram')],
        default='kg'
    )
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        """Automatically calculate 5% discount on save"""
        if not self.discounted_price and self.price:
            discount_amount = (self.price * 5) / 100
            self.discounted_price = self.price - discount_amount
        super().save(*args, **kwargs)
    
    def get_discounted_price(self):
        """Return discounted price"""
        if self.discounted_price:
            return self.discounted_price
        return self.price


class UserProfile(models.Model):
    """Extended user profile for badges and rewards"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    total_spent = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_orders = models.IntegerField(default=0)
    loyalty_points = models.IntegerField(default=0)
    
    # Badge Levels
    BADGE_CHOICES = [
        ('NEW', 'New Customer'),
        ('BRONZE', 'Bronze 🥉'),
        ('SILVER', 'Silver 🥈'),
        ('GOLD', 'Gold 🥇'),
        ('PLATINUM', 'Platinum 💎'),
        ('DIAMOND', 'Diamond 🔷'),
    ]
    
    badge = models.CharField(max_length=20, choices=BADGE_CHOICES, default='NEW')
    
    # Discount eligibility
    discount_percentage = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(50)]
    )
    
    def __str__(self):
        return f"{self.user.username} - {self.badge}"
    
    def update_badge(self):
        """Automatically update badge based on total spent"""
        if self.total_spent >= 10000:
            self.badge = 'DIAMOND'
            self.discount_percentage = 15
        elif self.total_spent >= 5000:
            self.badge = 'PLATINUM'
            self.discount_percentage = 10
        elif self.total_spent >= 2500:
            self.badge = 'GOLD'
            self.discount_percentage = 7
        elif self.total_spent >= 1000:
            self.badge = 'SILVER'
            self.discount_percentage = 5
        elif self.total_spent >= 500:
            self.badge = 'BRONZE'
            self.discount_percentage = 3
        else:
            self.badge = 'NEW'
            self.discount_percentage = 0
        
        # Add loyalty points (1 point per ₹100 spent)
        self.loyalty_points = int(self.total_spent / 100)
        self.save()
    
    def get_badge_icon(self):
        """Return badge icon for display"""
        icons = {
            'NEW': '🆕',
            'BRONZE': '🥉',
            'SILVER': '🥈',
            'GOLD': '🥇',
            'PLATINUM': '💎',
            'DIAMOND': '🔷',
        }
        return icons.get(self.badge, '🆕')


class Address(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE) 
    full_address = models.TextField()
    city = models.CharField(max_length=100)
    pincode = models.CharField(max_length=10)
    phone = models.CharField(max_length=15)
    is_default = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.user.username} - {self.city}"

# ✅ Order (ONE order = many products)
class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    address = models.ForeignKey(Address, on_delete=models.CASCADE)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    discount_applied = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    final_total = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, default='Pending')
    
    def __str__(self):
        return f"Order #{self.id}"
    
    def save(self, *args, **kwargs):
        """Apply user's discount before saving"""
        if not self.final_total:
            try:
                profile = self.user.profile
                discount = (self.total * profile.discount_percentage) / 100
                self.discount_applied = discount
                self.final_total = self.total - discount
            except UserProfile.DoesNotExist:
                self.final_total = self.total
        super().save(*args, **kwargs)

    
# ✅ OrderItem (order ke andar products)
class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    discounted_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    def get_item_total(self):
        """Calculate item total with 5% product discount"""
        return self.discounted_price * self.quantity if self.discounted_price else self.price * self.quantity

# ✅ CartItem — NOW linked to Django User
class CartItem(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    date_added = models.DateTimeField(auto_now_add=True)
    
    def total(self):
        """Calculate total with 5% discount"""
        discounted_price = self.product.get_discounted_price()
        return self.quantity * discounted_price


# ⭐ SpinHistory untouched
class SpinHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    offer = models.CharField(max_length=120)
    date = models.DateField(auto_now_add=True)

class SpinResult(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    reward = models.CharField(max_length=100)
    value = models.CharField(max_length=50)
    points_earned = models.IntegerField(default=0)
    spun_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.reward}"