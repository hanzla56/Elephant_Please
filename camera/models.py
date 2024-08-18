from django.db import models
from django.conf import settings

# Create your models here.
class category(models.Model):
      name = models.CharField(max_length=30)
      image = models.ImageField(null=True,blank=True)

      def __str__(self):
            return self.name
      
class Image(models.Model):
      url = models.ImageField()

class item(models.Model):
      title = models.CharField(max_length=40)
      category = models.ForeignKey(category,on_delete=models.CASCADE)
      image = models.ManyToManyField(Image)
      Daily_price = models.IntegerField()
      Weekly_price = models.IntegerField()
      Monthly_price = models.IntegerField()
      MarketValue = models.CharField(max_length=20)
      quantity = models.IntegerField()
      period = models.CharField(max_length=20)
      location = models.CharField(max_length=20)
      description = models.CharField(max_length=200)
      
      # Foreign key relationship with User model, automatically set to currently logged-in user
      owner = models.ForeignKey(settings.AUTH_USER_MODEL, null=True,blank=True, on_delete=models.CASCADE, related_name='items')

      def __str__(self):
            return self.title


class Review(models.Model):
    product = models.ForeignKey(item, on_delete=models.CASCADE, related_name='reviews')
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
    product = models.ForeignKey(item, null=True, blank=True, on_delete=models.CASCADE)
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
  
  
   


