from django.shortcuts import render,HttpResponse,get_object_or_404
from .models import category,item,Image

# Create your views here.
def Home(request):
      return render(request,'camera/home.html')

def detail(request):
      return render(request,'camera/detail_page.html')


def category_page(request):
    data = category.objects.all()
    data_list = [{"data": obj} for obj in data]
    # Split data into chunks of 5
    rows = [data_list[i:i + 5] for i in range(0, len(data_list), 5)]
    
    return render(request, 'camera/category.html', {'data': data})


def add_item(request):
    categories = category.objects.all()
    return render(request, 'camera/add_item.html', {'categories': categories})

def edit_item(request,product_id):
    pd = get_object_or_404(item, id=product_id)
    return render(request,'camera/edit_item.html' ,{'pd': pd})



def submission(request):
    if request.method == 'POST':
        # Get form data
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

        # Check for empty fields
        if not (title and category_id and daily_price and weekly_price and monthly_price and market_value and quantity and period and location and description and uploaded_images):
            return HttpResponse('One or more fields are empty!', status=400)

        try:
            # Get category object
            category_obj = category.objects.get(pk=category_id)

            # Save Item object
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
                description=description
            )

            # Save Image objects and associate with the item
            for image in uploaded_images:
                img = Image.objects.create(url=image)
                item_obj.image.add(img)  # Associate image with item

            return HttpResponse('Data saved successfully!', status=200)
        except category.DoesNotExist:
            return HttpResponse('Invalid category ID!', status=400)

    return HttpResponse('Invalid request method!', status=405)

