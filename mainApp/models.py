from decimal import Decimal
from django.core.exceptions import ValidationError
from django.db import models


class SlideImage(models.Model):
    image = models.ImageField(upload_to='slides/')
    title = models.CharField(max_length=200)
    description = models.TextField()

    def __str__(self):
        return self.title


class Categories(models.Model):
    name = models.CharField(max_length=50)
    image = models.ImageField(upload_to='categories')
    added_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Brands(models.Model):
    name = models.CharField(max_length=50)
    image = models.ImageField(upload_to='brands')
    added_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Products(models.Model):
    category = models.ForeignKey(Categories, on_delete=models.CASCADE)
    brand = models.ForeignKey(Brands, on_delete=models.CASCADE)
    product_name = models.CharField(max_length=100)
    image = models.ImageField(upload_to='products')
    price = models.DecimalField(max_digits=65, decimal_places=0)
    description = models.TextField()

    discount_amount = models.DecimalField(max_digits=50, decimal_places=0, blank=True, null=True)
    discount_percent = models.DecimalField(max_digits=5, decimal_places=1, blank=True, null=True)
    added_at = models.DateTimeField(auto_now_add=True)

    topsales = models.BooleanField(default=False)
    trending = models.BooleanField(default=False)
    dryskinproducts = models.BooleanField(default=False)
    oilyskin = models.BooleanField(default=False)
    acneprone = models.BooleanField(default=False)
    brightening = models.BooleanField(default=False)

    antiaging = models.BooleanField(default=False)
    sunscreen = models.BooleanField(default=False)
    lightening = models.BooleanField(default=False)

    is_out_of_stock = models.BooleanField(default=False)

    def __str__(self):
        return self.product_name

    def clean(self):
        if self.discount_amount and self.discount_percent:
            raise ValidationError("Use either discount amount or discount percent, not both.")

    @property
    def old_price(self):
        return self.price

    @property
    def has_discount(self):
        return (
            (self.discount_amount is not None and self.discount_amount > 0) or
            (self.discount_percent is not None and self.discount_percent > 0)
        )

    @property
    def discounted_price(self):
        price = Decimal(self.price)

        if self.discount_amount is not None and self.discount_amount > 0:
            discounted = price - Decimal(self.discount_amount)
            return discounted if discounted > 0 else Decimal("0")

        if self.discount_percent is not None and self.discount_percent > 0:
            discounted = price - ((price * Decimal(self.discount_percent)) / Decimal("100"))
            return discounted if discounted > 0 else Decimal("0")

        return price

    @property
    def amount_saved(self):
        return self.old_price - self.discounted_price

    @property
    def discount_percent_display(self):
        if self.discount_percent is not None and self.discount_percent > 0:
            return self.discount_percent

        if self.discount_amount is not None and self.discount_amount > 0 and self.price:
            percent = (Decimal(self.discount_amount) / Decimal(self.price)) * Decimal("100")
            return round(percent)

        return 0


class ProductImage(models.Model):
    product = models.ForeignKey(
        Products,
        default=None,
        on_delete=models.CASCADE,
        blank=True,
        null=True
    )
    image = models.ImageField(upload_to='product_other_images/')

    def __str__(self):
        return self.product.product_name if self.product else "No Product"


class ProductColor(models.Model):
    product = models.ForeignKey(
        Products,
        on_delete=models.CASCADE,
        related_name="colors"
    )
    color_hex = models.CharField(max_length=7)

    class Meta:
        unique_together = ("product", "color_hex")

    def __str__(self):
        return f"{self.product.product_name} - {self.color_hex}"


class CartItem(models.Model):
    product = models.ForeignKey(Products, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    session_key = models.CharField(max_length=400, blank=True, null=True)

    # Example: "#000000,#ffffff,#c79652"
    selected_colors = models.CharField(max_length=500, blank=True, null=True)

    class Meta:
        unique_together = ("product", "session_key", "selected_colors")

    @property
    def selected_color_list(self):
        if not self.selected_colors:
            return []
        return [color.strip() for color in self.selected_colors.split(",") if color.strip()]

    def __str__(self):
        return f"{self.product.product_name} x {self.quantity}"


class Order(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    address = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    country = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    total_price = models.IntegerField(default=1)

    def __str__(self):
        return f"Order #{self.id} - {self.first_name} {self.last_name}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Products, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    image = models.ImageField(upload_to='orders/', default='')
    price = models.IntegerField(default=1)

    # Example: "#000000,#ffffff,#c79652"
    selected_colors = models.CharField(max_length=500, blank=True, null=True)

    @property
    def selected_color_list(self):
        if not self.selected_colors:
            return []
        return [color.strip() for color in self.selected_colors.split(",") if color.strip()]

    def __str__(self):
        return f"{self.product.product_name} - Order #{self.order.id}"


class BuyNow2(models.Model):
    name = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=20)
    product_name = models.CharField(max_length=255)
    product_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    product_id = models.CharField(max_length=255)
    product_category = models.CharField(max_length=255, default='')

    # Example: "#000000,#ffffff,#c79652"
    selected_colors = models.CharField(max_length=500, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)

    @property
    def selected_color_list(self):
        if not self.selected_colors:
            return []
        return [color.strip() for color in self.selected_colors.split(",") if color.strip()]

    def __str__(self):
        return f"{self.name}'s Order for {self.product_name}"


class Currency(models.Model):
    name = models.CharField(max_length=50)
    code = models.CharField(max_length=3, unique=True)
    exchange_rate = models.DecimalField(max_digits=10, decimal_places=4, default=1.0)

    def __str__(self):
        return self.name


class WishlistItem(models.Model):
    session_key = models.CharField(max_length=100)
    product = models.ForeignKey(Products, on_delete=models.CASCADE)
    added_at = models.DateTimeField(auto_now_add=True)