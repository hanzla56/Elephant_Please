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
from .models import *
from .forms import *
from security.models import MyUser
from django.dispatch import Signal
from django.db.models import Avg, Count

payment_successful_signal = Signal()

# Create your views here.
User_Data = get_user_model()
stripe.api_key = settings.STRIPE_SECRET_KEY



def success_view(request,p_id):
    product = Item.objects.get(id = p_id)
    username = product.owner.username
    return render(request, 'camera/success.html',{'username':username})


# class SuccessView(TemplateView):
#     template_name = "camera/success.html"
    
    
    
@method_decorator(csrf_exempt, name='dispatch')
class CreateCheckoutSessionView(View):
    @method_decorator(login_required)
    def post(self, request, *args, **kwargs):
        YOUR_DOMAIN = 'http://127.0.0.1:8000/'  # Adjust this URL as needed
        p_id = kwargs.get('id')
        daterange = request.POST.get('daterange')
        print(daterange)
        price = request.POST.get('price')
        # price = int(price)
        price = 45
        user = request.user
        try:
            print(p_id)
            product = Item.objects.get(id = p_id)
         

            checkout_session = stripe.checkout.Session.create(
                customer_creation="always",
                line_items=[
                    {
                        'price_data':{
                            'currency':'usd',
                            'unit_amount':int(price * 100),
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
                    'user_id':user.id,
                    'date_range':daterange,
                    'price':price
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
            price = session['metadata'].get('price')
            daterange = session['metadata'].get('date_range')

            if not product_id or not user_id:
                logger.error(f"Missing product_id or user_id in session metadata: {session['metadata']}")
                return HttpResponse(status=400)

            fulfill_order(user_id, product_id,total_price=price,time=daterange)

            product = Item.objects.get(id=product_id)
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

def fulfill_order(user_id, p_id,*args,**kwargs):
    print('fulfill function runs')
    try:
        product = Item.objects.get(id=p_id)
        us = User_Data.objects.get(id=user_id)
        price = kwargs.get('total_price')
        span = kwargs.get('time')
        print(f'product span inside the database {span}')

        ord = Order.objects.create(
            product=product,
            user=us,
            quantity=1,
            total_price=price,
            time_span = span
            
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
    
    
    
    
    

def Home(request):
    current_user = request.user
    item_list = Item.objects.exclude(owner=current_user)
    count = item_list.count()
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

    return render(request, 'camera/home.html', {'items': items,'count':count})
    
# def Home(request):
#     item_list = Item.objects.all()
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
            items = Item.objects.filter(title__icontains=query)
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
    product = Item.objects.get(id=p_id)
    reviews = product.reviews.all()
    reviews_count = reviews.count()
    images = product.images.all()  # thanks to related_name="images"
    average_rating = reviews.aggregate(Avg('rating'))['rating__avg'] or 0
    star_range = range(1, 6) 
    
    return render(request,'camera/detail_page.html',{
        'images':images,
        'product': product,
        'reviews': reviews,
        'star_range': star_range,
        'reviews_count': reviews_count,
        'average_rating': round(average_rating, 1),
        })


@login_required
def add_review(request, product_id):
    print('Entering add_review view')
    product = get_object_or_404(Item, id=product_id)
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
    print(request.POST)
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
        print('save')

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

# def edit_item(request, product_id):
#     pd = get_object_or_404(item, id=product_id)
#     categories = category.objects.all()  # Fetch all categories
#     return render(request, 'camera/edit_item.html', {'pd': pd, 'categories': categories})


def edit_item(request):
    return render(request, 'camera/edit_item.html')

# from django.shortcuts import render, redirect
# from .models import Order  # Assuming you have an Order model

# def checkout(request):
#     date_range = request.GET.get('daterange')
#     print(date_range)
#     product_id = request.GET.get('product_id')
#     print(f' product id is{product_id}')
#     product = Item.objects.get(id=product_id)
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
#             product = Item.objects.get(id=product_id)
#             return render(request, 'camera/checkout.html', {'date_range': date_range, 'product': product})
#         else:
#             pass

#     return render(request, 'camera/checkout.html', {'product': product})


def checkout(request):
        date_range = request.GET.get('daterange')
        print(f'this is date range {date_range}')
        product_id = request.GET.get('product_id')
        print(f'product id is {product_id}')
        pd = Item.objects.get(id=product_id)
        if date_range and product_id:
            product = Item.objects.get(id=product_id)
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
#             item_obj = Item.objects.create(
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
        market_value = request.POST.get('MarketValue')
        quantity = request.POST.get('Quantity')
        period = request.POST.get('period')
        location = request.POST.get('Location')
        description = request.POST.get('description')
        uploaded_images = request.FILES.getlist('images')
        owner_data = request.user
        print(request.POST)
        print(f'this is owner name {owner_data}' )

        # Check for empty fields
        if not (title and category_id and daily_price  and market_value and quantity and period and location and description):
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
                item_obj.price = daily_price
                item_obj.MarketValue = market_value
                item_obj.quantity = quantity
                item_obj.min_rental_days = period
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
                item_obj = Item.objects.create(
                    title=title,
                    category=category_obj,
                    price=daily_price,
                    MarketValue=market_value,
                    quantity=quantity,
                    min_rental_days=period,
                    location=location,
                    description=description,
                    owner = owner_data
                )

                # Save Image objects and associate with the item
                for image in uploaded_images:
                    Image.objects.create(item=item_obj, url=image)
                    # img = Image.objects.create(url=image)
                    # item_obj.image.add(img)  # Associate image with item

                return HttpResponse('Product created successfully!', status=200)

        except category.DoesNotExist:
            print('this is except block')
            return HttpResponse('Invalid category ID!', status=400)
              

    return HttpResponse('Invalid request method!', status=405)


def index(request):
    return render(request,'camera/index.html')



def my_items(request):
    items = Item.objects.filter(owner=request.user)  # Only items for this user
    
    context = {
        'user_items': items
    }
    return render(request, 'camera/my_items.html',context )



# views.py
from django.shortcuts import render
from django.http import JsonResponse
from django.db.models import Q
from django.core.paginator import Paginator
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
from .models import Item

def search_page(request):
    """
    Render the search page template
    """
    return render(request, 'search/search_page.html')

def search_api(request):
    """
    API endpoint for search functionality with pagination
    Handles all search, filter, and pagination logic
    """
    try:
        # Get search parameters from request
        query = request.GET.get('q', '').strip()
        category = request.GET.get('category', '').strip()
        location = request.GET.get('location', '').strip()
        price_min = request.GET.get('price_min', '')
        price_max = request.GET.get('price_max', '')
        sort_by = request.GET.get('sort', 'relevance')
        
        # Get page number, default to 1
        try:
            page = int(request.GET.get('page', 1))
            if page < 1:
                page = 1
        except (ValueError, TypeError):
            page = 1
        
        # Start with base queryset - all active items
        items = Item.objects.filter(is_active=True)
        
        # Apply text search filter
        if query:
            items = items.filter(
                Q(title__icontains=query) | 
                Q(description__icontains=query) |
                Q(tags__icontains=query)
            )
        
        # Apply category filter
        if category:
            items = items.filter(category=category)
        
        # Apply location filter
        if location:
            items = items.filter(
                Q(location__icontains=location) |
                Q(owner__profile__city__icontains=location)
            )
        
        # Apply price filters
        if price_min:
            try:
                items = items.filter(price__gte=float(price_min))
            except ValueError:
                pass
        
        if price_max:
            try:
                items = items.filter(price__lte=float(price_max))
            except ValueError:
                pass
        
        # Apply sorting
        if sort_by == 'price-low':
            items = items.order_by('price', '-created_at')
        elif sort_by == 'price-high':
            items = items.order_by('-price', '-created_at')
        elif sort_by == 'newest':
            items = items.order_by('-created_at')
        elif sort_by == 'popular':
            items = items.order_by('-rating', '-review_count', '-created_at')
        elif sort_by == 'featured':
            items = items.order_by('-is_featured', '-created_at')
        else:  # relevance (default)
            if query:
                # If there's a search query, order by relevance
                items = items.order_by('-updated_at')
            else:
                # If no query, show newest first
                items = items.order_by('-created_at')
        
        # Get total count before pagination
        total_count = items.count()
        
        # Apply pagination
        items_per_page = 12
        paginator = Paginator(items, items_per_page)
        
        try:
            page_obj = paginator.get_page(page)
        except:
            page_obj = paginator.get_page(1)
        
        # Convert items to JSON format
        results = []
        for item in page_obj:
            # Calculate distance (simplified - you'd use actual geolocation)
            distance = f"{round(2.5 + (item.id % 10) * 0.5, 1)} km"
            
            first_image = item.images.first()
            image_url = first_image.url.url if first_image else None
            
            # Get image URL
            # Get image URL
            # if item.image:  # Single main image
            #     image_url = item.image.url
            # else:  # Fallback to first related image
           

            
            results.append({
                'id': item.id,
                'title': item.title,
                'description': item.description[:150] + '...' if len(item.description) > 150 else item.description,
                'price': float(item.price),
                'category': item.category,
                'image': image_url,
                'location': item.location,
                'distance': distance,
                'rating': float(item.rating) if item.rating else 0,
                'review_count': item.review_count,
                'owner': item.owner.username,
                'is_featured': item.is_featured if hasattr(item, 'is_featured') else False,
                'created_at': item.created_at.isoformat(),
                'updated_at': item.updated_at.isoformat()
            })
        
        # Prepare response data
        response_data = {
            'results': results,
            'total_count': total_count,
            'current_page': page_obj.number,
            'total_pages': paginator.num_pages,
            'has_next': page_obj.has_next(),
            'has_previous': page_obj.has_previous(),
            'next_page': page_obj.next_page_number() if page_obj.has_next() else None,
            'previous_page': page_obj.previous_page_number() if page_obj.has_previous() else None,
            'items_per_page': items_per_page,
            'search_params': {
                'query': query,
                'category': category,
                'location': location,
                'price_min': price_min,
                'price_max': price_max,
                'sort': sort_by
            }
        }
        
        return JsonResponse(response_data)
        
    except Exception as e:
        # Handle any errors
        print(f'the error is {e}')
        return JsonResponse({
            'error': 'Search failed',
            'message': str(e),
            'results': [],
            'total_count': 0,
            'has_next': False,
            'has_previous': False,
            'current_page': 1,
            'total_pages': 0
        }, status=500)

def get_search_suggestions(request):
    """
    API endpoint for search auto-complete suggestions
    """
    query = request.GET.get('q', '').strip()
    
    if len(query) < 2:
        return JsonResponse({'suggestions': []})
    
    try:
        # Get unique titles and tags that match the query
        items = Item.objects.filter(
            Q(title__icontains=query) | Q(tags__icontains=query),
            is_active=True
        )[:10]
        
        suggestions = []
        
        # Add matching titles
        for item in items:
            if item.title not in suggestions:
                suggestions.append(item.title)
        
        # Add popular search terms (you can store these in database)
        popular_terms = [
            'Camera', 'DSLR', 'Canon', 'Nikon', 'Photography',
            'Drill', 'Power Tools', 'DeWalt', 'Makita',
            'Laptop', 'MacBook', 'Dell', 'HP', 'Computer',
            'Bike', 'Bicycle', 'Mountain Bike', 'Road Bike',
            'Guitar', 'Piano', 'Keyboard', 'Microphone',
            'Tent', 'Camping', 'Hiking', 'Backpack'
        ]
        
        for term in popular_terms:
            if query.lower() in term.lower() and term not in suggestions:
                suggestions.append(term)
                if len(suggestions) >= 8:
                    break
        
        return JsonResponse({'suggestions': suggestions[:8]})
        
    except Exception as e:
        return JsonResponse({'suggestions': [], 'error': str(e)})

def item_detail(request, item_id):
    """
    Redirect to item detail page (called when rent now is clicked)
    """
    try:
        item = Item.objects.get(id=item_id, is_active=True)
        return render(request, 'items/item_detail.html', {'item': item})
    except Item.DoesNotExist:
        return render(request, '404.html', status=404)

# Additional utility views
def get_categories(request):
    """
    Get all available categories for filter dropdown
    """
    categories = Item.objects.filter(is_active=True).values_list('category', flat=True).distinct()
    
    category_choices = []
    for category in categories:
        category_choices.append({
            'value': category,
            'label': category.replace('_', ' ').title()
        })
    
    return JsonResponse({'categories': category_choices})

def get_locations(request):
    """
    Get all available locations for filter dropdown
    """
    locations = Item.objects.filter(is_active=True).values_list('location', flat=True).distinct()
    
    return JsonResponse({'locations': list(locations)})

def get_price_ranges(request):
    """
    Get price statistics for dynamic price filter
    """
    from django.db.models import Min, Max, Avg
    
    try:
        price_stats = Item.objects.filter(is_active=True).aggregate(
            min_price=Min('price'),
            max_price=Max('price'),
            avg_price=Avg('price')
        )
        
        return JsonResponse({
            'min_price': float(price_stats['min_price'] or 0),
            'max_price': float(price_stats['max_price'] or 0),
            'avg_price': float(price_stats['avg_price'] or 0)
        })
    except Exception as e:
        return JsonResponse({
            'min_price': 0,
            'max_price': 1000,
            'avg_price': 50,
            'error': str(e)
        })
        

