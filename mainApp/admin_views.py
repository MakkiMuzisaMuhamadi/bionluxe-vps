from django.db.models import Sum
from django.utils import timezone
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required

from mainApp.admin_forms import ProductForm, CategoryForm, BrandForm, SlideForm
from mainApp.models import (
    Products,
    ProductImage,
    ProductColor,
    Categories,
    Brands,
    SlideImage,
    Order,
    OrderItem,
    BuyNow2,
    WishlistItem,
)


def admin_required(view_func):
    @login_required
    def wrapper(request, *args, **kwargs):
        if not request.user.is_staff:
            return redirect("login")
        return view_func(request, *args, **kwargs)
    return wrapper


@admin_required
def dashboard(request):
    now = timezone.now()

    total_products = Products.objects.count()
    total_orders = Order.objects.count()
    total_categories = Categories.objects.count()
    total_brands = Brands.objects.count()
    total_buy_now = BuyNow2.objects.count()
    total_wishlist = WishlistItem.objects.count()
    total_revenue = Order.objects.aggregate(total=Sum("total_price"))["total"] or 0

    recent_orders = Order.objects.order_by("-created_at")[:8]

    month_labels = []
    monthly_sales = []
    monthly_orders = []

    for i in range(5, -1, -1):
        ref_date = now - timezone.timedelta(days=i * 30)
        month = ref_date.month
        year = ref_date.year

        month_labels.append(ref_date.strftime("%b %Y"))

        qs = Order.objects.filter(created_at__year=year, created_at__month=month)
        monthly_sales.append(qs.aggregate(total=Sum("total_price"))["total"] or 0)
        monthly_orders.append(qs.count())

    category_labels = []
    category_counts = []
    for category in Categories.objects.all():
        category_labels.append(category.name)
        category_counts.append(Products.objects.filter(category=category).count())

    brand_labels = []
    brand_counts = []
    for brand in Brands.objects.all():
        brand_labels.append(brand.name)
        brand_counts.append(Products.objects.filter(brand=brand).count())

    context = {
        "now": now,
        "total_products": total_products,
        "total_orders": total_orders,
        "total_categories": total_categories,
        "total_brands": total_brands,
        "total_buy_now": total_buy_now,
        "total_wishlist": total_wishlist,
        "total_revenue": total_revenue,
        "recent_orders": recent_orders,
        "month_labels": month_labels,
        "monthly_sales": monthly_sales,
        "monthly_orders": monthly_orders,
        "category_labels": category_labels,
        "category_counts": category_counts,
        "brand_labels": brand_labels,
        "brand_counts": brand_counts,
    }

    return render(request, "dashboard/index.html", context)


# =========================
# PRODUCT COLORS HELPER
# =========================
def _save_product_colors(product, request):
    """
    Saves colors from admin color picker inputs.
    Template input name must be: product_colors
    Example posted values: #000000, #ffffff, #c79652
    """
    colors = request.POST.getlist("product_colors")

    ProductColor.objects.filter(product=product).delete()

    clean_colors = []

    for color in colors:
        color = (color or "").strip().lower()

        if not color:
            continue

        if not color.startswith("#"):
            continue

        if len(color) != 7:
            continue

        if color not in clean_colors:
            clean_colors.append(color)

    for color in clean_colors:
        ProductColor.objects.create(product=product, color_hex=color)


# =========================
# PRODUCTS
# =========================
@admin_required
def admin_products(request):
    products = (
        Products.objects
        .select_related("category", "brand")
        .prefetch_related("colors")
        .order_by("-added_at")
    )

    return render(request, "dashboard/products/product_list.html", {
        "products": products,
        "page_title": "Products",
    })


@admin_required
def admin_add_product(request):
    if request.method == "POST":
        form = ProductForm(request.POST, request.FILES)

        if form.is_valid():
            product = form.save()

            _save_product_colors(product, request)

            gallery_images = request.FILES.getlist("images")
            for image in gallery_images:
                ProductImage.objects.create(product=product, image=image)

            messages.success(request, "Product added successfully.")
            return redirect("admin_products")
    else:
        form = ProductForm()

    return render(request, "dashboard/products/product_form.html", {
        "form": form,
        "page_title": "Add Product",
        "submit_text": "Save Product",
        "is_edit": False,
        "product_colors": [],
    })


@admin_required
def admin_edit_product(request, pk):
    product = get_object_or_404(Products, pk=pk)
    extra_images = ProductImage.objects.filter(product=product)
    product_colors = product.colors.all().order_by("id")

    if request.method == "POST":
        form = ProductForm(request.POST, request.FILES, instance=product)

        if form.is_valid():
            product = form.save()

            _save_product_colors(product, request)

            gallery_images = request.FILES.getlist("images")
            for image in gallery_images:
                ProductImage.objects.create(product=product, image=image)

            messages.success(request, "Product updated successfully.")
            return redirect("admin_products")
    else:
        form = ProductForm(instance=product)

    return render(request, "dashboard/products/product_form.html", {
        "form": form,
        "product": product,
        "extra_images": extra_images,
        "product_colors": product_colors,
        "page_title": "Edit Product",
        "submit_text": "Update Product",
        "is_edit": True,
    })


@admin_required
def admin_delete_product(request, pk):
    product = get_object_or_404(Products, pk=pk)

    if request.method == "POST":
        product.delete()
        messages.success(request, "Product deleted successfully.")
        return redirect("admin_products")

    return redirect("admin_products")


@admin_required
def admin_delete_product_image(request, pk):
    image = get_object_or_404(ProductImage, pk=pk)
    product_id = image.product.id if image.product else None

    if request.method == "POST":
        image.delete()
        messages.success(request, "Product image removed successfully.")

    if product_id:
        return redirect("admin_edit_product", pk=product_id)

    return redirect("admin_products")


# =========================
# CATEGORIES
# =========================
@admin_required
def admin_categories(request):
    categories = Categories.objects.order_by("-added_at")

    return render(request, "dashboard/categories/category_list.html", {
        "categories": categories,
        "page_title": "Categories",
    })


@admin_required
def admin_add_category(request):
    if request.method == "POST":
        form = CategoryForm(request.POST, request.FILES)

        if form.is_valid():
            form.save()
            messages.success(request, "Category added successfully.")
            return redirect("admin_categories")
    else:
        form = CategoryForm()

    return render(request, "dashboard/categories/category_form.html", {
        "form": form,
        "page_title": "Add Category",
        "submit_text": "Save Category",
    })


@admin_required
def admin_edit_category(request, pk):
    category = get_object_or_404(Categories, pk=pk)

    if request.method == "POST":
        form = CategoryForm(request.POST, request.FILES, instance=category)

        if form.is_valid():
            form.save()
            messages.success(request, "Category updated successfully.")
            return redirect("admin_categories")
    else:
        form = CategoryForm(instance=category)

    return render(request, "dashboard/categories/category_form.html", {
        "form": form,
        "page_title": "Edit Category",
        "submit_text": "Update Category",
    })


@admin_required
def admin_delete_category(request, pk):
    category = get_object_or_404(Categories, pk=pk)

    if request.method == "POST":
        category.delete()
        messages.success(request, "Category deleted successfully.")

    return redirect("admin_categories")


# =========================
# BRANDS
# =========================
@admin_required
def admin_brands(request):
    brands = Brands.objects.order_by("-added_at")

    return render(request, "dashboard/brands/brand_list.html", {
        "brands": brands,
        "page_title": "Brands",
    })


@admin_required
def admin_add_brand(request):
    if request.method == "POST":
        form = BrandForm(request.POST, request.FILES)

        if form.is_valid():
            form.save()
            messages.success(request, "Brand added successfully.")
            return redirect("admin_brands")
    else:
        form = BrandForm()

    return render(request, "dashboard/brands/brand_form.html", {
        "form": form,
        "page_title": "Add Brand",
        "submit_text": "Save Brand",
    })


@admin_required
def admin_edit_brand(request, pk):
    brand = get_object_or_404(Brands, pk=pk)

    if request.method == "POST":
        form = BrandForm(request.POST, request.FILES, instance=brand)

        if form.is_valid():
            form.save()
            messages.success(request, "Brand updated successfully.")
            return redirect("admin_brands")
    else:
        form = BrandForm(instance=brand)

    return render(request, "dashboard/brands/brand_form.html", {
        "form": form,
        "page_title": "Edit Brand",
        "submit_text": "Update Brand",
    })


@admin_required
def admin_delete_brand(request, pk):
    brand = get_object_or_404(Brands, pk=pk)

    if request.method == "POST":
        brand.delete()
        messages.success(request, "Brand deleted successfully.")

    return redirect("admin_brands")


# =========================
# SLIDES
# =========================
@admin_required
def admin_slides(request):
    slides = SlideImage.objects.order_by("-id")

    return render(request, "dashboard/slides/slide_list.html", {
        "slides": slides,
        "page_title": "Slides",
    })


@admin_required
def admin_add_slide(request):
    if request.method == "POST":
        form = SlideForm(request.POST, request.FILES)

        if form.is_valid():
            form.save()
            messages.success(request, "Slide added successfully.")
            return redirect("admin_slides")
    else:
        form = SlideForm()

    return render(request, "dashboard/slides/slide_form.html", {
        "form": form,
        "page_title": "Add Slide",
        "submit_text": "Save Slide",
    })


@admin_required
def admin_edit_slide(request, pk):
    slide = get_object_or_404(SlideImage, pk=pk)

    if request.method == "POST":
        form = SlideForm(request.POST, request.FILES, instance=slide)

        if form.is_valid():
            form.save()
            messages.success(request, "Slide updated successfully.")
            return redirect("admin_slides")
    else:
        form = SlideForm(instance=slide)

    return render(request, "dashboard/slides/slide_form.html", {
        "form": form,
        "page_title": "Edit Slide",
        "submit_text": "Update Slide",
    })


@admin_required
def admin_delete_slide(request, pk):
    slide = get_object_or_404(SlideImage, pk=pk)

    if request.method == "POST":
        slide.delete()
        messages.success(request, "Slide deleted successfully.")

    return redirect("admin_slides")


# =========================
# ORDERS
# =========================
@admin_required
def admin_orders(request):
    new_order_cutoff = timezone.now() - timezone.timedelta(hours=24)

    orders = Order.objects.all().order_by("-created_at")

    return render(request, "dashboard/orders/order_list.html", {
        "orders": orders,
        "page_title": "Orders",
        "new_order_cutoff": new_order_cutoff,
    })


@admin_required
def admin_buy_now(request):
    new_order_cutoff = timezone.now() - timezone.timedelta(hours=24)

    buy_now_orders = BuyNow2.objects.all().order_by("-created_at")

    return render(request, "dashboard/orders/buy_now_list.html", {
        "buy_now_orders": buy_now_orders,
        "page_title": "Buy Now Orders",
        "new_order_cutoff": new_order_cutoff,
    })


@admin_required
def admin_order_detail(request, pk):
    order = get_object_or_404(Order, pk=pk)
    order_items = order.items.select_related("product").all()

    return render(request, "dashboard/orders/order_detail.html", {
        "order": order,
        "order_items": order_items,
        "page_title": f"Order #{order.id}",
    })


@admin_required
def admin_delete_order(request, pk):
    order = get_object_or_404(Order, pk=pk)

    if request.method == "POST":
        order.delete()
        messages.success(request, "Order deleted successfully.")

    return redirect("admin_orders")


@admin_required
def admin_delete_buy_now(request, pk):
    order = get_object_or_404(BuyNow2, pk=pk)

    if request.method == "POST":
        order.delete()
        messages.success(request, "Buy now order deleted successfully.")

    return redirect("admin_buy_now")


# =========================
# OTHER ADMIN PAGES
# =========================
@admin_required
def admin_customers(request):
    return render(request, "dashboard/customers.html")


@admin_required
def admin_analytics(request):
    return render(request, "dashboard/analytics.html")


@admin_required
def admin_settings(request):
    return render(request, "dashboard/settings.html")