from django.urls import path

from mainApp.admin_views import *
from . import views

urlpatterns = [
    path('login/', views.login, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('', views.index, name='index'),
    path('product/<int:product_id>/', views.details, name='product_detail'),
    path('cart', views.cart, name='cart'),
    path('checkout', views.checkout, name='checkout'),
    path('get_cart_count/', views.get_cart_count, name='get_cart_count'),
    path('add-to-cart/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('place_order/', views.place_order, name='place_order'),
    path('cart-drawer/', views.get_cart_drawer, name='cart_drawer'),
    path('category/<int:category_id>/', views.category_products, name='category_products'),
    path('buy-now/', views.buy_now, name='buy_now'),
    path('cart/item/<int:item_id>/delete/', views.delete_item, name='delete_item'),
    path('search/', views.search, name='search'),
    path('search-results/', views.product_search, name='product_search'),
    path('add_to_wishlist/<int:product_id>/', views.add_to_wishlist, name='add_to_wishlist'),
    path('get_wishlist_count/', views.get_wishlist_count, name='get_wishlist_count'),
    path('wishlist/', views.wishlist, name='wishlist'),
    path('category/<int:category_id>/', views.category_products, name='category_products'),
    path('brand/<int:brand_id>/', views.brand_products, name='brand_products'),
    path('toggle-stock-status/<int:product_id>/', views.toggle_stock_status, name='toggle_stock_status'),
    path('cart/item/<int:item_id>/update/', views.update_cart_item, name='update_cart_item'),
    path('products/section/<str:section>/', views.product_section_list, name='product_section_list'),

    # =========================
    # DASHBOARD
    # =========================
    path("dashboard/", dashboard, name="dashboard"),

    # Products
    path("dashboard/products/", admin_products, name="admin_products"),
    path("dashboard/products/add/", admin_add_product, name="admin_add_product"),
    path("dashboard/products/<int:pk>/edit/", admin_edit_product, name="admin_edit_product"),
    path("dashboard/products/<int:pk>/delete/", admin_delete_product, name="admin_delete_product"),
    path("dashboard/product-images/<int:pk>/delete/", admin_delete_product_image, name="admin_delete_product_image"),

    # Categories
    path("dashboard/categories/", admin_categories, name="admin_categories"),
    path("dashboard/categories/add/", admin_add_category, name="admin_add_category"),
    path("dashboard/categories/<int:pk>/edit/", admin_edit_category, name="admin_edit_category"),
    path("dashboard/categories/<int:pk>/delete/", admin_delete_category, name="admin_delete_category"),

    # Brands
    path("dashboard/brands/",admin_brands, name="admin_brands"),
    path("dashboard/brands/add/", admin_add_brand, name="admin_add_brand"),
    path("dashboard/brands/<int:pk>/edit/", admin_edit_brand, name="admin_edit_brand"),
    path("dashboard/brands/<int:pk>/delete/", admin_delete_brand, name="admin_delete_brand"),

    # Slides
    path("dashboard/slides/", admin_slides, name="admin_slides"),
    path("dashboard/slides/add/", admin_add_slide, name="admin_add_slide"),
    path("dashboard/slides/<int:pk>/edit/", admin_edit_slide, name="admin_edit_slide"),
    path("dashboard/slides/<int:pk>/delete/", admin_delete_slide, name="admin_delete_slide"),

    # Orders
    path("dashboard/orders/", admin_orders, name="admin_orders"),
    path("dashboard/orders/<int:pk>/", admin_order_detail, name="admin_order_detail"),
    path("dashboard/orders/<int:pk>/delete/", admin_delete_order, name="admin_delete_order"),

    # Buy Now Orders
    path("dashboard/buy-now/", admin_buy_now, name="admin_buy_now"),
    path("dashboard/buy-now/<int:pk>/delete/", admin_delete_buy_now, name="admin_delete_buy_now"),

    # =========================
    # CUSTOMERS
    # =========================
    path("dashboard/customers/", admin_customers, name="admin_customers"),


    # =========================
    # ANALYTICS
    # =========================
    path("dashboard/analytics/", admin_analytics, name="admin_analytics"),


    # =========================
    # SETTINGS
    # =========================
    path("dashboard/settings/", admin_settings, name="admin_settings"),
]