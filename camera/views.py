import stripe
import logging
from django.conf import settings
from django.shortcuts import render,HttpResponse,get_object_or_404,redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import  method_decorator
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.core.paginator import Paginator,PageNotAnInteger,EmptyPage
from django.views.generic import View,TemplateView
from .models import category,item,Image,Order,Review
from .forms import *
from accounts.models import MyUser
from django.dispatch import Signal
from django.db.models import Avg, Count

payment_successful_signal = Signal()

# Create your views here.
User_Data = get_user_model()
stripe.api_key = settings.STRIPE_SECRET_KEY



def success_view(request,p_id):
    product = item.objects.get(id = p_id)
    username = product.owner.username
    return render(request, 'camera/success.html',{'username':username})


# class SuccessView(TemplateView):
#     template_name = "camera/success.html"
    
    
    
@method_decorator(csrf_exempt, name='dispatch')
class CreateCheckoutSessionView(View):
    @method_decorator(login_required)
    def post(self, request, *args, **kwargs):
        print(f"this is request dictionary {request}")
        YOUR_DOMAIN = 'http://127.0.0.1:8000/'  # Adjust this URL as needed
        print(f'this is dict {kwargs}')
        p_id = kwargs.get('id')
        address = kwargs.get('address')
        user = request.user
        try:
            print(p_id)
            product = item.objects.get(id = p_id)
         

            checkout_session = stripe.checkout.Session.create(
                customer_creation="always",
                line_items=[
                    {
                        'price_data':{
                            'currency':'usd',
                            'unit_amount':int(product.Weekly_price * 100),
                            'product_data':{
                                'name':product.title,
                                # 'images':[product.main_img],
                            }
                        },
                        'quantity':1,
                        # Provide the exact Price ID (for example, pr_1234) of the product you want to sell
                        # 'price': "price_1PGKQBHdyG3oyik5wzb6ml6J",
                        # 'quantity': 1,
                    },
                ],
                metadata={
                    'product_id':product.id,
                    'user_id':user.id
                },
                
                mode='payment',
                # success_url=YOUR_DOMAIN + '/success/',
                success_url= f"{YOUR_DOMAIN}success/{product.id}",
                cancel_url=YOUR_DOMAIN + 'cancel.html',
                automatic_tax={'enabled': True},
            )
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

        # Redirect to the checkout session URL
        return redirect(checkout_session.url, status=303)
    
logger = logging.getLogger(__name__)

@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE', '')
    event = None

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET,
        )
    except ValueError as e:
        logger.error(f"Invalid payload: {e}")
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError as e:
        logger.error(f"Invalid signature: {e}")
        return HttpResponse(status=400)

    if event['type'] == 'checkout.session.completed':
        session_id = event['data']['object']['id']
        
        try:
            session = stripe.checkout.Session.retrieve(
                session_id,
                expand=['line_items'],
            )
            print(session)
            logger.info(f"Session retrieved: {session_id}")

            customer_email = session['customer_details']['email']
            product_id = session['metadata'].get('product_id')
            user_id = session['metadata'].get('user_id')

            if not product_id or not user_id:
                logger.error(f"Missing product_id or user_id in session metadata: {session['metadata']}")
                return HttpResponse(status=400)

            fulfill_order(user_id, product_id)

            product = item.objects.get(id=product_id)
            payment_successful_signal.send(sender=__name__, user_id=user_id, product=product)
            print('signal is sent')
            send_mail(
                subject=f'Here is your product {product.title}',
                message='Thanks for buying this product',
                recipient_list=[customer_email],
                from_email="matt@test.com",
            )

            line_items = session.line_items
            logger.info(f"Line items: {line_items}")
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error: {e}")
            return HttpResponse(status=400)
        except item.DoesNotExist:
            logger.error(f"Laptop not found: {product_id}")
            return HttpResponse(status=400)
        except Exception as e:
            logger.error(f"An error occurred: {e}")
            return HttpResponse(status=500)

    return HttpResponse(status=200)

def fulfill_order(user_id, p_id):
    print('fulfill function runs')
    try:
        product = item.objects.get(id=p_id)
        us = User_Data.objects.get(id=user_id)

        ord = Order.objects.create(
            product=product,
            user=us,
            quantity=1,
            total_price=product.Daily_price
        )
        ord.save()
        logger.info(f"Order fulfilled for user: {user_id}, product: {p_id}")
    except item.DoesNotExist:
        logger.error(f"Laptop not found: {p_id}")
        raise
    except User_Data.DoesNotExist:
        logger.error(f"User not found: {user_id}")
        raise
    except Exception as e:
        logger.error(f"Error fulfilling order: {e}")
        raise   
    
    
    
    
    
@login_required
def Home(request):
    current_user = request.user
    item_list = item.objects.exclude(owner=current_user)
    print(current_user)
    print(item_list)
    paginator = Paginator(item_list, 4)  # Adjust the number of items per page as needed

    page = request.GET.get('page')
    try:
        items = paginator.page(page)
    except PageNotAnInteger:
        items = paginator.page(1)
    except EmptyPage:
        items = paginator.page(paginator.num_pages)

    return render(request, 'camera/home.html', {'items': items})
    
# def Home(request):
#     item_list = item.objects.all()
#     paginator = Paginator(item_list, 3)  # Adjust the number of items per page as needed

#     page = request.GET.get('page')
#     try:
#         items = paginator.page(page)
#     except PageNotAnInteger:
#         items = paginator.page(1)
#     except EmptyPage:
#         items = paginator.page(paginator.num_pages)

#     return render(request, 'camera/home.html', {'items': items})

@csrf_exempt
def search_items(request):
    if request.method == 'GET':
        query = request.GET.get('q', '')
        if query:
            items = item.objects.filter(title__icontains=query)
            print('the product is fetched')
            print(items)
            items_list = []
            for itm in items:
                images = [img.url.url for img in itm.image.all()]
                items_list.append({
                    'id': itm.id,
                    'title': itm.title,
                    'location': itm.location,
                    'Daily_price': itm.Daily_price,
                    'images': images
                })
            return JsonResponse({'items': items_list}, safe=False)
        else:
            return JsonResponse({'items': []}, safe=False)


def detail(request,p_id):
    product = item.objects.get(id=p_id)
    reviews = product.reviews.all()
    reviews_count = reviews.count()
    average_rating = reviews.aggregate(Avg('rating'))['rating__avg'] or 0
    star_range = range(1, 6) 
    return render(request,'camera/detail_page.html',{
        'product': product,
        'reviews': reviews,
        'star_range': star_range,
        'reviews_count': reviews_count,
        'average_rating': round(average_rating, 1),
        })


@login_required
def add_review(request, product_id):
    print('Entering add_review view')
    product = get_object_or_404(item, id=product_id)
    if request.method == 'POST':
        print('Handling POST request')
        form = ReviewForm(request.POST)
        if form.is_valid():
            print('Form is valid')
            print(form.cleaned_data)
            review = form.save(commit=False)
            review.product = product
            review.user = request.user
            review.save()
            print('Review saved successfully')
            return redirect('camera:detail', p_id=product.id)
        else:
            print('Form is not valid')
            print(form.errors)
            print(form.cleaned_data)
    else:
        form = ReviewForm()
    return render(request, 'camera/detail_page.html', {'form': form, 'product': product})

def profile(request):
    user_ID = request.user.id
    print(user_ID)
    user_profile = MyUser.objects.get(id=user_ID)
    print(user_profile)
    return render(request,'camera/user_profile.html',{'user_profile':user_profile})


def edit_profile(request):
    user_ID = request.user.id
    user_profile = MyUser.objects.get(id=user_ID)
    print('outside if')

    if request.method == 'POST':
        print('inside if')
        user_profile.username = request.POST.get('firstName')
        user_profile.email = request.POST.get('emailAddress')
        user_profile.location = request.POST.get('location')
        user_profile.last_name = request.POST.get('lastName')
        user_profile.mobile_number = request.POST.get('phoneNumber')
        user_profile.about_me = request.POST.get('profileDescription')
        print(user_profile.location)

        if 'profile_img' in request.FILES:
            user_profile.profile_img = request.FILES['profile_img']

        user_profile.save()

        return redirect('camera:profile')
    
    else:
        return render(request, 'camera/edit_profile.html', {'user_profile': user_profile})
    
    
# def edit_profile(request,user_id):
#     user_profile = MyUser.objects.get(id=user_id)
#     print(user_profile)
#     return render(request,'camera/edit_profile.html',{'user_profile':user_profile})

def category_page(request):
    data = category.objects.all()
    data_list = [{"data": obj} for obj in data]
    # Split data into chunks of 5
    rows = [data_list[i:i + 5] for i in range(0, len(data_list), 5)]
    
    return render(request, 'camera/category.html', {'data': data})


def add_item(request):
    categories = category.objects.all()
    return render(request, 'camera/add_item.html', {'categories': categories})

def edit_item(request, product_id):
    pd = get_object_or_404(item, id=product_id)
    categories = category.objects.all()  # Fetch all categories
    return render(request, 'camera/edit_item.html', {'pd': pd, 'categories': categories})


# from django.shortcuts import render, redirect
# from .models import Order  # Assuming you have an Order model

# def checkout(request):
#     date_range = request.GET.get('daterange')
#     print(date_range)
#     product_id = request.GET.get('product_id')
#     print(f' product id is{product_id}')
#     product = item.objects.get(id=product_id)
#     print('enter in the checkout view')

#     if request.method == 'POST':
#         # Access form data directly from request.POST
#         order = Order.objects.create(
#             product=product,
#             user = request.user,
#             first_name=request.POST.get('username'),
#             last_name=request.POST.get('Last_Name'),
#             email=request.POST.get('Email'),
#             mobile_no=request.POST.get('Mobile_NUmber'),
#             address=request.POST.get('address'),
#             country=request.POST.get('country'),
#             note=request.POST.get('note_to_lender'),
#             # other fields and logic
#             payment_status='pending'
#         ) 

#         # Redirect to success page or payment gateway
#         return redirect('create-checkout-session',id=product_id, order_id=order.id)
#     else:
        
        
#         if date_range and product_id:
#             product = item.objects.get(id=product_id)
#             return render(request, 'camera/checkout.html', {'date_range': date_range, 'product': product})
#         else:
#             pass

#     return render(request, 'camera/checkout.html', {'product': product})


def checkout(request):
        date_range = request.GET.get('daterange')
        print(f'this is date range {date_range}')
        product_id = request.GET.get('product_id')
        print(f'product id is {product_id}')
        pd = item.objects.get(id=product_id)
        if date_range and product_id:
            product = item.objects.get(id=product_id)
        # Do something with the date range and product ID
            return render(request, 'camera/checkout.html', {'date_range': date_range, 'product': product,'pd':pd})
        else:
        # Handle scenario where date range or product ID is not provided
            pass

        return render(request,'camera/detail_page.html')

# def submission(request):
#     if request.method == 'POST':
#         # Get form data
#         title = request.POST.get('title')
#         category_id = request.POST.get('category')
#         daily_price = request.POST.get('Daily')
#         weekly_price = request.POST.get('Weekly')
#         monthly_price = request.POST.get('Monthly')
#         market_value = request.POST.get('MarketValue')
#         quantity = request.POST.get('Quantity')
#         period = request.POST.get('period')
#         location = request.POST.get('Location')
#         description = request.POST.get('description')
#         uploaded_images = request.FILES.getlist('images')

#         # Check for empty fields
#         if not (title and category_id and daily_price and weekly_price and monthly_price and market_value and quantity and period and location and description and uploaded_images):
#             return HttpResponse('One or more fields are empty!', status=400)

#         try:
#             # Get category object
#             category_obj = category.objects.get(pk=category_id)

#             # Save Item object
#             item_obj = item.objects.create(
#                 title=title,
#                 category=category_obj,
#                 Daily_price=daily_price,
#                 Weekly_price=weekly_price,
#                 Monthly_price=monthly_price,
#                 MarketValue=market_value,
#                 quantity=quantity,
#                 period=period,
#                 location=location,
#                 description=description
#             )

#             # Save Image objects and associate with the item
#             for image in uploaded_images:
#                 img = Image.objects.create(url=image)
#                 item_obj.image.add(img)  # Associate image with item

#             return HttpResponse('Data saved successfully!', status=200)
#         except category.DoesNotExist:
#             return HttpResponse('Invalid category ID!', status=400)

#     return HttpResponse('Invalid request method!', status=405)



#This view is used for both new product submission and for editing existing product 
@login_required
def submission(request):
    print('view start here')
    if request.method == 'POST':
        # Get form data
        print('if block')
        product_id = request.POST.get('product_id')
        title = request.POST.get('title')
        category_id = request.POST.get('category')
        daily_price = request.POST.get('Daily')
        weekly_price = request.POST.get('Weekly')
        monthly_price = request.POST.get('Monthly')
        market_value = request.POST.get('MarketValue')
        quantity = request.POST.get('Quantity')
        period = request.POST.get('period')
        location = request.POST.get('Location')
        description = request.POST.get('description')
        uploaded_images = request.FILES.getlist('images')
        owner_data = request.user
        print(request)
        print(f'this is owner name {owner_data}' )

        # Check for empty fields
        if not (title and category_id and daily_price and weekly_price and monthly_price and market_value and quantity and period and location and description):
            print('field checkup')
            return HttpResponse('One or more fields are empty!', status=400)

        try:
            print('try block start here')
            # Get category object
            category_obj = category.objects.get(pk=category_id)
            print('category object')

            if product_id:
                # Update existing product
                item_obj = get_object_or_404(item, pk=product_id)
                item_obj.title = title
                item_obj.category = category_obj
                item_obj.Daily_price = daily_price
                item_obj.Weekly_price = weekly_price
                item_obj.Monthly_price = monthly_price
                item_obj.MarketValue = market_value
                item_obj.quantity = quantity
                item_obj.period = period
                item_obj.location = location
                item_obj.description = description
                item_obj.owner = request.user
                item_obj.save()

                # Update Image objects
                if uploaded_images:
                    item_obj.image.clear()  # Clear existing images
                    for image in uploaded_images:
                        img = Image.objects.create(url=image)
                        item_obj.image.add(img)  # Associate image with item

                return HttpResponse('Product updated successfully!', status=200)
            else:
                # Create new product
                item_obj = item.objects.create(
                    title=title,
                    category=category_obj,
                    Daily_price=daily_price,
                    Weekly_price=weekly_price,
                    Monthly_price=monthly_price,
                    MarketValue=market_value,
                    quantity=quantity,
                    period=period,
                    location=location,
                    description=description,
                    owner = owner_data
                )

                # Save Image objects and associate with the item
                for image in uploaded_images:
                    img = Image.objects.create(url=image)
                    item_obj.image.add(img)  # Associate image with item

                return HttpResponse('Product created successfully!', status=200)

        except category.DoesNotExist:
            print('this is except block')
            return HttpResponse('Invalid category ID!', status=400)
              

    return HttpResponse('Invalid request method!', status=405)