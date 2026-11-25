import re
from decimal import Decimal
from difflib import SequenceMatcher

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login, logout
from django.contrib.auth.decorators import login_required
from django.core.mail import EmailMultiAlternatives
from django.db.models import Q, Case, When, Value, IntegerField
from django.http import JsonResponse
from django.shortcuts import redirect, render, get_object_or_404
from django.template.loader import render_to_string
from django.utils.html import strip_tags

from twilio.rest import Client

from mainApp.models import (
    Products,
    ProductImage,
    ProductColor,
    Categories,
    Brands,
    SlideImage,
    CartItem,
    Order,
    OrderItem,
    BuyNow2,
    WishlistItem,
)


def superuser_required(view_func):
    @login_required
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_superuser:
            return render(request, 'forbidden.html')
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def login(request):
    error_message = None

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(username=username, password=password)

        if user is not None:
            if user.is_staff:
                auth_login(request, user)
                return redirect('dashboard')
            return redirect('index')

        error_message = 'Invalid username or password'

    return render(request, 'login.html', {'error_message': error_message})


def logout_view(request):
    logout(request)
    return redirect('login')


# =========================
# HOME / PRODUCT LISTING
# =========================
def _featured_products(flag_name, limit=10):
    return (
        Products.objects
        .filter(**{flag_name: True}, is_out_of_stock=False)
        .select_related("category", "brand")
        .prefetch_related("colors")
        .order_by("?")[:limit]
    )


def index(request):
    categories = Categories.objects.all()
    brands = Brands.objects.all()

    newproducts = (
        Products.objects
        .filter(is_out_of_stock=False)
        .select_related("category", "brand")
        .prefetch_related("colors")
        .order_by("-added_at")[:10]
    )

    topsales = _featured_products("topsales", 10)
    trending = _featured_products("trending", 10)
    dryskinproducts = _featured_products("dryskinproducts", 10)
    oilyskin = _featured_products("oilyskin", 10)
    acneprone = _featured_products("acneprone", 10)
    brightening = _featured_products("brightening", 10)
    antiaging = _featured_products("antiaging", 10)
    sunscreen = _featured_products("sunscreen", 10)
    lightening = _featured_products("lightening", 10)

    banners = SlideImage.objects.all()

    context = {
        "categories": categories,
        "brands": brands,
        "newproducts": newproducts,
        "topsales": topsales,
        "trending": trending,
        "dryskinproducts": dryskinproducts,
        "oilyskin": oilyskin,
        "acneprone": acneprone,
        "brightening": brightening,
        "antiaging": antiaging,
        "sunscreen": sunscreen,
        "lightening": lightening,
        "banners": banners,
    }

    return render(request, "index.html", context)


def product_section_list(request, section):
    section_map = {
        "newproducts": {
            "title": "New Arrivals",
            "description": "Freshly added beauty, skincare and wellness picks for your collection.",
            "queryset": Products.objects.filter(is_out_of_stock=False).order_by("-added_at"),
        },
        "topsales": {
            "title": "Top Sales Products",
            "description": "Best-selling customer favorites chosen again and again.",
            "queryset": Products.objects.filter(topsales=True, is_out_of_stock=False).order_by("-added_at"),
        },
        "trending": {
            "title": "Trending Products",
            "description": "What shoppers are currently loving across beauty and skincare.",
            "queryset": Products.objects.filter(trending=True, is_out_of_stock=False).order_by("?"),
        },
        "dryskinproducts": {
            "title": "Dry Skin Essentials",
            "description": "Hydrating formulas selected to nourish and comfort dry skin.",
            "queryset": Products.objects.filter(dryskinproducts=True, is_out_of_stock=False).order_by("?"),
        },
        "oilyskin": {
            "title": "Oily Skin Solutions",
            "description": "Lightweight and balancing picks made for oily skin routines.",
            "queryset": Products.objects.filter(oilyskin=True, is_out_of_stock=False).order_by("?"),
        },
        "acneprone": {
            "title": "Acne Prone Care",
            "description": "Gentle and targeted products designed for acne-prone skin needs.",
            "queryset": Products.objects.filter(acneprone=True, is_out_of_stock=False).order_by("?"),
        },
        "brightening": {
            "title": "Brightening Picks",
            "description": "Radiance-boosting products for a luminous and even-looking finish.",
            "queryset": Products.objects.filter(brightening=True, is_out_of_stock=False).order_by("?"),
        },
        "antiaging": {
            "title": "Anti-aging Products",
            "description": "Premium products selected for youthful-looking skincare routines.",
            "queryset": Products.objects.filter(antiaging=True, is_out_of_stock=False).order_by("?"),
        },
        "sunscreen": {
            "title": "SunScreen Products",
            "description": "Protective skincare picks for daily sun care routines.",
            "queryset": Products.objects.filter(sunscreen=True, is_out_of_stock=False).order_by("?"),
        },
        "lightening": {
            "title": "Lightening Products",
            "description": "Selected products for bright and even-looking skin routines.",
            "queryset": Products.objects.filter(lightening=True, is_out_of_stock=False).order_by("?"),
        },
    }

    config = section_map.get(section)

    if not config:
        return render(request, "404.html", status=404)

    products = (
        config["queryset"]
        .select_related("category", "brand")
        .prefetch_related("colors")
    )

    context = {
        "section_key": section,
        "section_title": config["title"],
        "section_description": config["description"],
        "products": products,
        "categories": Categories.objects.all(),
        "brands": Brands.objects.all(),
    }

    return render(request, "product_section_list.html", context)


def details(request, product_id):
    product = (
        Products.objects
        .select_related("category", "brand")
        .prefetch_related("colors")
        .get(pk=product_id)
    )

    product_images = ProductImage.objects.filter(product=product)

    similar_products = (
        Products.objects
        .filter(category=product.category, is_out_of_stock=False)
        .exclude(id=product.id)
        .select_related("category", "brand")
        .prefetch_related("colors")[:4]
    )

    context = {
        "product": product,
        "product_images": product_images,
        "similar_products": similar_products,
        "categories": Categories.objects.all(),
        "brands": Brands.objects.all(),
    }

    return render(request, "description.html", context)


# =========================
# COLOR HELPERS
# =========================
def _normalize_selected_colors(product, colors):
    """
    Receives selected colors from request.POST.getlist("selected_colors").
    Returns comma-separated valid colors, for example:
    "#000000,#ffffff,#c79652"

    If product has colors, at least one valid color is required.
    If product has no colors, returns empty string.
    """
    if not product.colors.exists():
        return ""

    clean_colors = []

    for color in colors:
        color = (color or "").strip().lower()

        if not color:
            continue

        if product.colors.filter(color_hex__iexact=color).exists():
            if color not in clean_colors:
                clean_colors.append(color)

    if not clean_colors:
        return None

    return ",".join(clean_colors)


# =========================
# CART HELPERS
# =========================
def _get_or_create_session_key(request):
    session_key = request.session.session_key

    if not session_key:
        request.session.create()
        session_key = request.session.session_key

    return session_key


def _get_product_unit_price(product):
    try:
        return product.discounted_price
    except Exception:
        return product.price


def _get_product_old_price(product):
    try:
        return product.old_price
    except Exception:
        return product.price


def _build_cart_data(request):
    session_key = _get_or_create_session_key(request)

    cart_items = (
        CartItem.objects
        .filter(session_key=session_key)
        .select_related("product", "product__category", "product__brand")
        .prefetch_related("product__colors")
    )

    out_of_stock_items = cart_items.filter(product__is_out_of_stock=True)

    if out_of_stock_items.exists():
        out_of_stock_items.delete()
        cart_items = (
            CartItem.objects
            .filter(session_key=session_key)
            .select_related("product", "product__category", "product__brand")
            .prefetch_related("product__colors")
        )

    subtotal = Decimal("0")
    shipping = Decimal("0")

    for item in cart_items:
        item.unit_price = _get_product_unit_price(item.product)
        item.old_unit_price = _get_product_old_price(item.product)
        item.total_price = item.unit_price * item.quantity
        subtotal += item.total_price

    total_price = subtotal + shipping
    cart_count = sum(item.quantity for item in cart_items)

    request.session["cart_items_count"] = cart_count

    return {
        "cart_items": cart_items,
        "subtotal": subtotal,
        "shipping": shipping,
        "total_price": total_price,
        "cart_count": cart_count,
    }


def get_cart_drawer(request):
    cart_data = _build_cart_data(request)
    html = render_to_string("partials/cart_drawer_content.html", cart_data, request=request)

    return JsonResponse({
        "status": "success",
        "html": html,
        "count": cart_data["cart_count"],
        "subtotal": str(cart_data["subtotal"]),
        "total_price": str(cart_data["total_price"]),
    })


def add_to_cart(request, product_id):
    if request.method != "POST":
        return JsonResponse({
            "message": "Invalid request method",
            "status": "error",
        }, status=405)

    product = (
        Products.objects
        .prefetch_related("colors")
        .get(pk=product_id)
    )

    if product.is_out_of_stock:
        return JsonResponse({
            "message": "This product is currently out of stock and cannot be added to cart",
            "status": "error",
        }, status=400)

    selected_colors = _normalize_selected_colors(
        product,
        request.POST.getlist("selected_colors")
    )

    if selected_colors is None:
        return JsonResponse({
            "message": "Please select at least one product color first",
            "status": "error",
        }, status=400)

    session_key = _get_or_create_session_key(request)

    cart_item, created = CartItem.objects.get_or_create(
        session_key=session_key,
        product=product,
        selected_colors=selected_colors or None,
    )

    if not created:
        cart_item.quantity += 1
        cart_item.save()

    cart_data = _build_cart_data(request)
    html = render_to_string("partials/cart_drawer_content.html", cart_data, request=request)

    return JsonResponse({
        "message": f"{product.product_name} added to cart successfully",
        "status": "success",
        "count": cart_data["cart_count"],
        "html": html,
    })


def get_cart_count(request):
    session_key = request.session.session_key

    if not session_key:
        return JsonResponse({"count": 0})

    cart_count = CartItem.objects.filter(session_key=session_key).count()

    return JsonResponse({"count": cart_count})


def cart(request):
    session_key = request.session.session_key

    if not session_key:
        return render(request, "cart.html", {
            "cart_items": [],
            "subtotal": 0,
            "shipping": 0,
            "total_price": 0,
            "categories": Categories.objects.all(),
            "brands": Brands.objects.all(),
        })

    cart_data = _build_cart_data(request)

    context = {
        "cart_items": cart_data["cart_items"],
        "subtotal": cart_data["subtotal"],
        "shipping": cart_data["shipping"],
        "total_price": cart_data["total_price"],
        "categories": Categories.objects.all(),
        "brands": Brands.objects.all(),
    }

    return render(request, "cart.html", context)


def checkout(request):
    session_key = request.session.session_key

    if not session_key:
        return render(request, "checkout.html", {
            "cart_items": [],
            "subtotal": 0,
            "shipping": 0,
            "total_price": 0,
            "categories": Categories.objects.all(),
            "brands": Brands.objects.all(),
        })

    cart_data = _build_cart_data(request)

    context = {
        "cart_items": cart_data["cart_items"],
        "subtotal": cart_data["subtotal"],
        "shipping": cart_data["shipping"],
        "total_price": cart_data["total_price"],
        "categories": Categories.objects.all(),
        "brands": Brands.objects.all(),
    }

    return render(request, "checkout.html", context)


def update_cart_item(request, item_id):
    if request.method != "POST":
        return JsonResponse({
            "status": "error",
            "message": "Invalid request method",
        }, status=405)

    session_key = _get_or_create_session_key(request)

    item = get_object_or_404(
        CartItem,
        pk=item_id,
        session_key=session_key,
    )

    action = request.POST.get("cart_action")

    if action == "increase":
        item.quantity += 1
        item.save()
    elif action == "decrease":
        if item.quantity > 1:
            item.quantity -= 1
            item.save()
        else:
            item.delete()
    else:
        return JsonResponse({
            "status": "error",
            "message": "Invalid action",
        }, status=400)

    cart_data = _build_cart_data(request)
    drawer_html = render_to_string("partials/cart_drawer_content.html", cart_data, request=request)
    page_html = render_to_string("partials/cart_page_content.html", cart_data, request=request)

    return JsonResponse({
        "status": "success",
        "drawer_html": drawer_html,
        "page_html": page_html,
        "count": cart_data["cart_count"],
        "subtotal": str(cart_data["subtotal"]),
        "total_price": str(cart_data["total_price"]),
    })


def delete_item(request, item_id):
    if request.method != "POST":
        return JsonResponse({
            "status": "error",
            "message": "Invalid request method",
        }, status=405)

    session_key = _get_or_create_session_key(request)

    item = get_object_or_404(
        CartItem,
        pk=item_id,
        session_key=session_key,
    )

    item.delete()

    cart_data = _build_cart_data(request)
    drawer_html = render_to_string("partials/cart_drawer_content.html", cart_data, request=request)
    page_html = render_to_string("partials/cart_page_content.html", cart_data, request=request)

    return JsonResponse({
        "status": "success",
        "message": "Item removed from cart",
        "drawer_html": drawer_html,
        "page_html": page_html,
        "count": cart_data["cart_count"],
        "subtotal": str(cart_data["subtotal"]),
        "total_price": str(cart_data["total_price"]),
    })


# =========================
# CHECKOUT ORDER
# =========================
def place_order(request):
    if request.method != "POST":
        return redirect("checkout")

    session_key = request.session.session_key

    if not session_key:
        messages.error(request, "Your cart is empty.")
        return redirect("cart")

    cart_items = (
        CartItem.objects
        .filter(session_key=session_key)
        .select_related("product")
    )

    if not cart_items.exists():
        messages.error(request, "Your cart is empty.")
        return redirect("cart")

    subtotal = Decimal("0")

    for item in cart_items:
        item.unit_price = item.product.discounted_price
        item.total_price = item.unit_price * item.quantity
        subtotal += item.total_price

    total_price = int(subtotal)

    order = Order.objects.create(
        first_name=request.POST.get("first_name"),
        last_name=request.POST.get("last_name"),
        email=request.POST.get("email"),
        phone=request.POST.get("phone"),
        address=request.POST.get("address"),
        city=request.POST.get("city"),
        country=request.POST.get("country"),
        total_price=total_price,
    )

    for cart_item in cart_items:
        OrderItem.objects.create(
            order=order,
            product=cart_item.product,
            quantity=cart_item.quantity,
            image=cart_item.product.image,
            price=int(cart_item.product.discounted_price),
            selected_colors=cart_item.selected_colors,
        )

    cart_items.delete()
    request.session["cart_items_count"] = 0

    html_content = render_to_string("order_email_template.html", {"order": order})
    text_content = strip_tags(html_content)

    subject = "New Order Created"
    from_email = settings.DEFAULT_FROM_EMAIL
    recipient_list = ["bionluxebusiness@gmail.com"]

    email = EmailMultiAlternatives(subject, text_content, from_email, recipient_list)
    email.attach_alternative(html_content, "text/html")
    email.send()

    messages.success(request, "Your Order has been received, We shall contact you soon")
    return redirect("index")


# =========================
# BUY NOW
# =========================
def buy_now(request):
    if request.method != "POST":
        return redirect("index")

    product_id = request.POST.get("product_id")

    product = (
        Products.objects
        .prefetch_related("colors")
        .get(pk=product_id)
    )

    if product.is_out_of_stock:
        messages.error(request, "This product is currently out of stock.")
        return redirect("product_detail", product_id=product.id)

    selected_colors = _normalize_selected_colors(
        product,
        request.POST.getlist("selected_colors")
    )

    if selected_colors is None:
        messages.error(request, "Please select at least one product color first.")
        return redirect("product_detail", product_id=product.id)

    order2 = BuyNow2.objects.create(
        name=request.POST.get("name"),
        phone_number=request.POST.get("phone_number"),
        product_name=product.product_name,
        product_price=product.discounted_price,
        product_id=str(product.id),
        product_category=product.category.name,
        selected_colors=selected_colors or None,
    )

    html_content = render_to_string("buy_now_email_template.html", {
        "order2": order2,
        "product": product,
    })
    text_content = strip_tags(html_content)

    subject = "New Order Created (Buy Now)"
    from_email = settings.DEFAULT_FROM_EMAIL
    recipient_list = ["bionluxebusiness@gmail.com"]

    email = EmailMultiAlternatives(subject, text_content, from_email, recipient_list)
    email.attach_alternative(html_content, "text/html")
    email.send()

    messages.success(request, "Your Order has been received, We shall contact you soon")
    return redirect("index")


# =========================
# CATEGORY / BRAND / SEARCH
# =========================
def category_products(request, category_id):
    category = get_object_or_404(Categories, pk=category_id)

    products = (
        Products.objects
        .filter(category=category)
        .select_related("category", "brand")
        .prefetch_related("colors")
    )

    context = {
        "category": category,
        "category2": category,
        "products": products,
        "categories": Categories.objects.all(),
        "brands": Brands.objects.all(),
    }

    return render(request, "category_products.html", context)


def brand_products(request, brand_id):
    brand = get_object_or_404(Brands, pk=brand_id)

    products = (
        Products.objects
        .filter(brand=brand)
        .select_related("category", "brand")
        .prefetch_related("colors")
    )

    context = {
        "products": products,
        "brand": brand,
        "categories": Categories.objects.all(),
        "brands": Brands.objects.all(),
    }

    return render(request, "brand_products.html", context)


def search(request):
    categories = Categories.objects.all()
    brands = Brands.objects.all()

    popular_searches = [
        "Oily Skin",
        "Lightening",
        "Dry skins",
        "Vaseline",
        "Moisturizer",
        "Serum",
        "Sunscreen",
        "Face Wash",
    ]

    context = {
        "categories": categories,
        "brands": brands,
        "popular_searches": popular_searches,
    }

    return render(request, "search.html", context)


def _normalize_search_text(value):
    value = (value or "").lower().strip()
    value = re.sub(r"[^a-z0-9\s]+", " ", value)
    value = re.sub(r"\s+", " ", value).strip()
    return value


def _tokenize_search_query(query):
    normalized = _normalize_search_text(query)
    return [token for token in normalized.split() if token]


def _score_product_match(product, normalized_query, tokens):
    searchable = " ".join([
        product.product_name or "",
        product.description or "",
        getattr(product.category, "name", "") or "",
        getattr(product.brand, "name", "") or "",
    ])

    searchable = _normalize_search_text(searchable)

    score = 0

    if searchable == normalized_query:
        score += 300

    if searchable.startswith(normalized_query):
        score += 180

    if normalized_query and normalized_query in searchable:
        score += 120

    name = _normalize_search_text(product.product_name or "")

    if name == normalized_query:
        score += 300
    elif name.startswith(normalized_query):
        score += 200
    elif normalized_query and normalized_query in name:
        score += 140

    for token in tokens:
        if token in name:
            score += 40
        elif token in searchable:
            score += 18

    ratio = SequenceMatcher(None, normalized_query, name).ratio()
    score += int(ratio * 100)

    return score


def product_search(request):
    query = request.GET.get("q", "").strip()

    categories = Categories.objects.all()
    brands = Brands.objects.all()

    products = Products.objects.none()
    suggestions = []

    if query:
        normalized_query = _normalize_search_text(query)
        tokens = _tokenize_search_query(query)

        base_q = (
            Q(product_name__icontains=query) |
            Q(description__icontains=query) |
            Q(category__name__icontains=query) |
            Q(brand__name__icontains=query)
        )

        for token in tokens:
            base_q |= (
                Q(product_name__icontains=token) |
                Q(description__icontains=token) |
                Q(category__name__icontains=token) |
                Q(brand__name__icontains=token)
            )

        queryset = (
            Products.objects
            .filter(base_q, is_out_of_stock=False)
            .select_related("category", "brand")
            .prefetch_related("colors")
            .distinct()
            .annotate(
                relevance=Case(
                    When(product_name__iexact=query, then=Value(100)),
                    When(product_name__istartswith=query, then=Value(90)),
                    When(product_name__icontains=query, then=Value(80)),
                    When(category__name__icontains=query, then=Value(70)),
                    When(brand__name__icontains=query, then=Value(60)),
                    When(description__icontains=query, then=Value(50)),
                    default=Value(10),
                    output_field=IntegerField(),
                )
            )
            .order_by("-relevance", "-added_at")
        )

        candidate_products = list(queryset[:120])

        if not candidate_products:
            fallback_pool = list(
                Products.objects
                .filter(is_out_of_stock=False)
                .select_related("category", "brand")
                .prefetch_related("colors")
            )

            scored = []

            for product in fallback_pool:
                score = _score_product_match(product, normalized_query, tokens)

                if score >= 45:
                    scored.append((score, product))

            scored.sort(key=lambda item: (-item[0], -item[1].id))
            candidate_products = [item[1] for item in scored[:60]]
        else:
            scored = []
            seen_ids = set()

            for product in candidate_products:
                score = _score_product_match(product, normalized_query, tokens)

                if product.id not in seen_ids:
                    seen_ids.add(product.id)
                    scored.append((score, product))

            scored.sort(key=lambda item: (-item[0], -item[1].id))
            candidate_products = [item[1] for item in scored]

        products = candidate_products

        if not products:
            all_products = list(
                Products.objects
                .filter(is_out_of_stock=False)
                .select_related("category", "brand")
                .prefetch_related("colors")
            )

            alt = []

            for product in all_products:
                score = _score_product_match(product, normalized_query, tokens)

                if score >= 35:
                    alt.append((score, product.product_name))

            alt.sort(key=lambda item: -item[0])

            suggestions = []
            seen_names = set()

            for _, name in alt:
                if name not in seen_names:
                    seen_names.add(name)
                    suggestions.append(name)

                if len(suggestions) == 6:
                    break

    context = {
        "products": products,
        "query": query,
        "categories": categories,
        "brands": brands,
        "suggestions": suggestions,
    }

    return render(request, "search-results.html", context)


# =========================
# WISHLIST
# =========================
def add_to_wishlist(request, product_id):
    product = get_object_or_404(Products, pk=product_id)
    session_key = request.session.session_key

    if not session_key:
        request.session.create()
        session_key = request.session.session_key

    wishlist_item, created = WishlistItem.objects.get_or_create(
        session_key=session_key,
        product=product
    )

    if not created:
        response_data = {
            "message": "Product is already in your wishlist",
            "status": "info",
        }
    else:
        response_data = {
            "message": "Product added to the wishlist successfully",
            "status": "success",
        }

    return JsonResponse(response_data)


def get_wishlist_count(request):
    session_key = request.session.session_key

    if not session_key:
        return JsonResponse({"count": 0})

    wishlist_count = WishlistItem.objects.filter(session_key=session_key).count()

    return JsonResponse({"count": wishlist_count})


def wishlist(request):
    session_key = request.session.session_key

    wishlist_items = WishlistItem.objects.none()

    if session_key:
        wishlist_items = (
            WishlistItem.objects
            .filter(session_key=session_key)
            .select_related("product")
        )

    context = {
        "wishlist_items": wishlist_items,
        "categories": Categories.objects.all(),
        "brands": Brands.objects.all(),
    }

    return render(request, "wishlist.html", context)


# =========================
# STOCK TOGGLE
# =========================
@login_required
def toggle_stock_status(request, product_id):
    product = get_object_or_404(Products, id=product_id)

    if request.method == "POST":
        product.is_out_of_stock = not product.is_out_of_stock
        product.save()
        messages.success(request, f"Stock status for {product.product_name} updated successfully!")

    return redirect("productList")


# =========================
# OPTIONAL SMS
# =========================
def send_sms_notification(order_type):
    client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)

    client.messages.create(
        body=f"Hello, a new {order_type} order has been created. Check the admin panel for details.",
        from_=settings.TWILIO_PHONE_NUMBER,
        to="+2567537925776",
    )