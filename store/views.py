from django.conf import settings
from django.shortcuts import redirect, render, get_object_or_404
from django.urls import reverse
from store.models import Product, Order, Cart
from django.contrib import messages
from django.utils import timezone
from django.core.paginator import Paginator

import stripe


stripe.api_key = settings.STRIPE_SECRET_KEY


# Create your views here.
def index(request):
    products  = Product.objects.all()
    item_name = request.GET.get('item-name')

    #pour activer la barre de recherche
    if item_name:
        products = products.filter(name__icontains=item_name) 
    #gestion de la pagination
    paginator = Paginator(products, 8)
    page = request.GET.get('page')
    products = paginator.get_page(page)
    return render(request, 'store/index.html', context={"products": products})

def home(request):
    featured_products = Product.objects.all()[:4]
    popular_products = Product.objects.all()[4:7]

    context = {
        "featured_products": featured_products,
        "popular_products": popular_products,
    }
    return render(request, "store/home.html", context)

def contact(request):
    return render(request, "store/contact.html")

def about(request):
    return render(request, "store/about.html")

def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug)
    return render(request, 'store/detail.html', context={"product": product})

def add_to_cart(request, slug):
    user = request.user
    product = get_object_or_404(Product, slug=slug)
    cart, _ = Cart.objects.get_or_create(user=user)
    order, created = Order.objects.get_or_create(user=user,
                                                 ordered=False,
                                                 product=product)
    
    if created:
        cart.orders.add(order)
        cart.save()
    else:
        order.quantity += 1
        order.save()

    return redirect(reverse("product", kwargs={"slug": slug}))

def cart(request):
    if not request.user.is_authenticated:
        messages.error(request, "Vous devez être connecté pour accéder à votre panier.")
        return redirect("login")
    
    cart = Cart.objects.filter(user=request.user).first()
    if not cart:
        messages.info(request, "Votre panier est vide 🛒")
        return render(request, "store/cart.html", context={"orders": []})
    return render(request, 'store/cart.html', context={"orders": cart.orders.all()})

def delete_cart(request):
    if cart := request.user.cart:
        cart.delete()

    return redirect('index')


def checkout(request):
    cart = get_object_or_404(Cart, user=request.user)
    total_amount = sum(order.product.price * order.quantity for order in cart.orders.all())

    if request.method == "POST":
        payment_method = request.POST.get("payment_method")
        shipping_address = request.POST.get("shipping_address")
        phone_number = request.POST.get("phone_number")

        if payment_method == "cod":
            for order in cart.orders.all():
                order.ordered = True
                order.ordered_date = timezone.now()
                order.shipping_address = shipping_address
                order.phone_number = phone_number
                order.save()

            cart.orders.clear()
            return redirect("payment_success")

        elif payment_method == "stripe":
            # Sauvegarde en session (sera utilisé après paiement réussi)
            request.session["shipping_address"] = shipping_address
            request.session["phone_number"] = phone_number

            try:
                checkout_session = stripe.checkout.Session.create(
                    payment_method_types=["card"],
                    line_items=[
                        {
                            "price_data": {
                                "currency": "usd",
                                "product_data": {"name": "Commande AthletiQ"},
                                "unit_amount": int(total_amount * 100),
                            },
                            "quantity": 1,
                        }
                    ],
                    mode="payment",
                    success_url=request.build_absolute_uri("/payment-success/"),
                    cancel_url=request.build_absolute_uri("/checkout/"),
                )
                return redirect(checkout_session.url)
            except Exception as e:
                return render(request, "store/checkout.html", {
                    "error": str(e),
                    "cart": cart,
                    "total_amount": total_amount,
                    "STRIPE_PUBLISHABLE_KEY": settings.STRIPE_PUBLISHABLE_KEY,
                })

    return render(request, "store/checkout.html", {
        "cart": cart,
        "total_amount": total_amount,
        "STRIPE_PUBLISHABLE_KEY": settings.STRIPE_PUBLISHABLE_KEY,
    })

def payment_success(request):
    cart = get_object_or_404(Cart, user=request.user)
    orders = cart.orders.filter(ordered=False)
    shipping_address = request.session.get("shipping_address", "Adresse non fournie")
    phone_number = request.session.get("phone_number", "Téléphone non fourni")

    for order in cart.orders.all():
        order.ordered = True
        order.ordered_date = timezone.now()
        order.shipping_address = shipping_address
        order.phone_number = phone_number
        order.save()

    cart.orders.clear()

    # Supprime l'adresse de la session
    request.session.pop("shipping_address", None)
    request.session.pop("phone_number", None)

    return render(request, "store/payment_success.html", {
        "message": f"✅ Paiement réussi. Votre commande sera livrée à : {shipping_address}"
    })

def payment_cancel(request):
    return render(request, 'store/payment_cancel.html')


def my_orders(request):
    orders = Order.objects.filter(user=request.user, ordered=True).order_by("-ordered_date")
    return render(request, "store/my_orders.html", {"orders": orders})