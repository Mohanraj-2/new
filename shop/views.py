from django.http import JsonResponse
from django.shortcuts import redirect, render
from .form import CustomUserForm
from .models import *
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
import json
from django.conf import settings
import stripe
from .models import Product
from django.shortcuts import get_object_or_404, render
from django.http import HttpResponse

stripe.api_key = settings.STRIPE_SECRET_KEY

# Home view
def home(request):
    products = Product.objects.filter(trending=1)
    return render(request, "shop/index.html", {"products": products})

# Favorites
def favviewpage(request):
    if request.user.is_authenticated:
        fav = Favourite.objects.filter(user=request.user)
        return render(request, "shop/fav.html", {"fav": fav})
    else:
        return redirect("/")

def remove_fav(request, fid):
    item = Favourite.objects.get(id=fid)
    item.delete()
    return redirect("/favviewpage")

def fav_page(request):
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        if request.user.is_authenticated:
            data = json.load(request)
            product_id = data['pid']
            product_status = Product.objects.get(id=product_id)
            if product_status:
                if Favourite.objects.filter(user=request.user.id, product_id=product_id):
                    return JsonResponse({'status': 'Product Already in Favourite'}, status=200)
                else:
                    Favourite.objects.create(user=request.user, product_id=product_id)
                    return JsonResponse({'status': 'Product Added to Favourite'}, status=200)
        else:
            return JsonResponse({'status': 'Login to Add Favourite'}, status=200)
    else:
        return JsonResponse({'status': 'Invalid Access'}, status=200)

# Cart
def cart_page(request):
    if request.user.is_authenticated:
        cart = Cart.objects.filter(user=request.user)
        return render(request, "shop/cart.html", {"cart": cart})
    else:
        return redirect("/")

def remove_cart(request, cid):
    cartitem = Cart.objects.get(id=cid)
    cartitem.delete()
    
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        updated_count = Cart.objects.filter(user=request.user).count()
        return JsonResponse({'status': 'Cart Item Removed', 'updated_count': updated_count})
    else:
        return redirect("/cart")

def add_to_cart(request):
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        if request.user.is_authenticated:
            data = json.load(request)
            product_qty = data['product_qty']
            product_id = data['pid']
            product_status = Product.objects.get(id=product_id)
            if product_status:
                if Cart.objects.filter(user=request.user.id, product_id=product_id):
                    return JsonResponse({'status': 'Product Already in Cart'}, status=200)
                else:
                    if product_status.quantity >= product_qty:
                        Cart.objects.create(user=request.user, product_id=product_id, product_qty=product_qty)
                        updated_count = Cart.objects.filter(user=request.user).count()
                        return JsonResponse({'status': 'Product Added to Cart', 'updated_count': updated_count}, status=200)
                    else:
                        return JsonResponse({'status': 'Product Stock Not Available'}, status=200)
        else:
            return JsonResponse({'status': 'Login to Add Cart'}, status=200)
    else:
        return JsonResponse({'status': 'Invalid Access'}, status=200)

@login_required
def cart_item_count(request):
    user_cart = request.user.cart  # Assuming you have a Cart model linked to the user
    item_count = user_cart.items.count()  # Replace `.items.count()` based on your model structure
    return JsonResponse({'count': item_count})

# Other Views (Login, Logout, Register, etc.)
# (No changes to these)

def logout_page(request):
  if request.user.is_authenticated:
    logout(request)
    messages.success(request,"Logged out Successfully")
  return redirect("/")
 
 
def login_page(request):
  if request.user.is_authenticated:
    return redirect("/")
  else:
    if request.method=='POST':
      name=request.POST.get('username')
      pwd=request.POST.get('password')
      print ("name",name,pwd)
      user=authenticate(request,username=name,password=pwd)
      if user is not None:
        login(request,user)
        messages.success(request,"Logged in Successfully")
        return redirect("/")
      else:
        messages.error(request,"Invalid User Name or Password")
        return redirect("/login")
    return render(request,"shop/login.html")
 
def register(request):
  form=CustomUserForm()
  if request.method=='POST':
    form=CustomUserForm(request.POST)
    if form.is_valid():
      form.save()
      messages.success(request,"Registration Success You can Login Now..!")
      return redirect('/login')
  return render(request,"shop/register.html",{'form':form})
 
 
def collections(request):
  catagory=Catagory.objects.filter(status=0)
  return render(request,"shop/collections.html",{"catagory":catagory})
 
def collectionsview(request,name):
  if(Catagory.objects.filter(name=name,status=0)):
      products=Product.objects.filter(category__name=name)
      return render(request,"shop/products/index.html",{"products":products,"category_name":name})
  else:
    messages.warning(request,"No Such Catagory Found")
    return redirect('collections')
 
 
def product_details(request,cname,pname):
    if(Catagory.objects.filter(name=cname,status=0)):
      if(Product.objects.filter(name=pname,status=0)):
        products=Product.objects.filter(name=pname,status=0).first()
        return render(request,"shop/products/product_details.html",{"products":products})
      else:
        messages.error(request,"No Such Produtct Found")
        return redirect('collections')
    else:
      messages.error(request,"No Such Catagory Found")
      return redirect('collections')
    

    


def checkout(request):
    if request.method == 'POST':
        try:
            print("Creating payment intent")
            intent = stripe.PaymentIntent.create(
                amount=1000,  # Amount in cents
                currency='inr',
                payment_method_types=['card'],
            )
            print("Payment intent created successfully")
            return JsonResponse({'clientSecret': intent['client_secret']})
        except Exception as e:
            print(f"Error: {e}")
            return JsonResponse({'error': str(e)})

    return render(request, 'checkout.html')

from django.http import HttpResponse

def payment_view(request):
    if request.method == "POST":
        product_id = request.POST.get("product_id")
        amount = request.POST.get("amount")

        # Fetch the product details
        product = get_object_or_404(Product, id=product_id)

        # Payment integration logic goes here
        # Example: Redirect to a payment gateway or process payment here
        return HttpResponse(f"Processing payment for {product.name} of amount ₹{amount}")
    return HttpResponse("Invalid Request", status=400)
