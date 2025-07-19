from django.db import models
from django.conf import settings


from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.urls import reverse

      
class Image(models.Model):
      url = models.ImageField()
      
class Item(models.Model):
    """
    Model for rental Items
    """
    CATEGORY_CHOICES = [
        ('electronics', 'Electronics'),
        ('tools', 'Tools & Equipment'),
        ('sports', 'Sports & Outdoor'),
        ('home', 'Home & Garden'),
        ('automotive', 'Automotive'),
        ('music', 'Music & Events'),
        ('photography', 'Photography'),
        ('fitness', 'Fitness'),
        ('books', 'Books & Media'),
        ('clothing', 'Clothing & Accessories'),
        ('toys', 'Toys & Games'),
        ('furniture', 'Furniture'),
    ]
    
    CONDITION_CHOICES = [
        ('new', 'New'),
        ('like_new', 'Like New'),
        ('good', 'Good'),
        ('fair', 'Fair'),
        ('poor', 'Poor'),
    ]
    
    # Basic Information
    title = models.CharField(max_length=200, db_index=True)
    description = models.TextField()
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, db_index=True)
    condition = models.CharField(max_length=10, choices=CONDITION_CHOICES, default='good')
    
    # Pricing
    price = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(0.01)],
        help_text="Price per day",
        null=True,
        blank=True
    )
    MarketValue = models.CharField(max_length=20,blank=True, null=True)

    
    # Media
    image = models.ImageField(upload_to='Items/', blank=True, null=True)
    images = models.ManyToManyField(Image)
    
    # Location
    location = models.CharField(max_length=100, db_index=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    
    # Ownership
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='Items',null=True,blank=True)
    
    # Status
    is_active = models.BooleanField(default=True, db_index=True)
    is_featured = models.BooleanField(default=False, db_index=True)
    is_available = models.BooleanField(default=True)
    
    # Ratings and Reviews
    rating = models.DecimalField(
        max_digits=3, 
        decimal_places=2, 
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(5)]
    )
    review_count = models.IntegerField(default=0)
    
    # SEO and Search
    tags = models.CharField(
        max_length=500, 
        blank=True,
        help_text="Comma-separated tags for search"
    )
    
    # Rental Options
    min_rental_days = models.IntegerField(default=1)
    max_rental_days = models.IntegerField(default=30)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, null=True,blank=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True,null=True,blank=True, db_index=True)
    
    # View count for popularity
    view_count = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['category', 'is_active']),
            models.Index(fields=['price', 'is_active']),
            models.Index(fields=['location', 'is_active']),
            models.Index(fields=['rating', 'is_active']),
            models.Index(fields=['created_at', 'is_active']),
        ]
    
    def __str__(self):
        return self.title
    
    def get_absolute_url(self):
        return reverse('search:Item_detail', kwargs={'Item_id': self.id})
    
    def get_category_display_name(self):
        return dict(self.CATEGORY_CHOICES).get(self.category, self.category)
    
    def get_condition_display_name(self):
        return dict(self.CONDITION_CHOICES).get(self.condition, self.condition)
    
    def increment_view_count(self):
        """Increment view count when Item is viewed"""
        self.view_count += 1
        self.save(update_fields=['view_count'])
    
    def get_average_rating(self):
        """Calculate average rating from reviews"""
        reviews = self.reviews.filter(is_active=True)
        if reviews.exists():
            return reviews.aggregate(avg_rating=models.Avg('rating'))['avg_rating']
        return 0
    
    def update_rating(self):
        """Update rating and review count based on reviews"""
        reviews = self.reviews.filter(is_active=True)
        if reviews.exists():
            self.rating = reviews.aggregate(avg_rating=models.Avg('rating'))['avg_rating']
            self.review_count = reviews.count()
        else:
            self.rating = 0
            self.review_count = 0
        self.save(update_fields=['rating', 'review_count'])



# Create your models here.
class category(models.Model):
      name = models.CharField(max_length=30)
      image = models.ImageField(null=True,blank=True)

      def __str__(self):
            return self.name


# class Item(models.Model):
#       title = models.CharField(max_length=40)
#       category = models.ForeignKey(category,on_delete=models.CASCADE)
#       image = models.ManyToManyField(Image)
#       Daily_price = models.IntegerField()
#       Weekly_price = models.IntegerField()
#       Monthly_price = models.IntegerField()
#       MarketValue = models.CharField(max_length=20)
#       quantity = models.IntegerField()
#       period = models.CharField(max_length=20)
#       location = models.CharField(max_length=20)
#       description = models.CharField(max_length=200)
      
#       # Foreign key relationship with User model, automatically set to currently logged-in user
#       owner = models.ForeignKey(settings.AUTH_USER_MODEL, null=True,blank=True, on_delete=models.CASCADE, related_name='Items')

#       def __str__(self):
#             return self.title


class Review(models.Model):
    product = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)])
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str(self):
        return f'Review for {self.product.name} by {self.user.username}'
      
class Order(models.Model):
    PAYMENT_STATUS_CHOICES = [
        ('p', 'pending'),
        ('s', 'successful')
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.CASCADE)
    product = models.ForeignKey(Item, null=True, blank=True, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)  # Ensure quantity is positive
    total_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    time_span = models.CharField(max_length=40, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    first_name = models.CharField(max_length=30, null=True,blank=True)
    last_name = models.CharField(max_length=30 ,null=True,blank=True)
    email = models.EmailField(null=True,blank=True)
    mobile_no = models.CharField(max_length=20, null=True,blank=True)  # Consider using CharField for phone numbers
    address = models.CharField(max_length=60, null=True,blank=True)
    note = models.CharField(max_length=100, null=True,blank=True)
    payment_status = models.CharField(max_length=1, null=True,blank=True, choices=PAYMENT_STATUS_CHOICES, default='s')

    
    def __str__(self) -> str:
        return self.product.title
  
  
   


