from django.db import models

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
      Daily_price = models.CharField(max_length=20)
      Weekly_price = models.CharField(max_length=20)
      Monthly_price = models.CharField(max_length=20)
      MarketValue = models.CharField(max_length=20)
      quantity = models.IntegerField()
      period = models.CharField(max_length=20)
      location = models.CharField(max_length=20)
      description = models.CharField(max_length=200)

      def __str__(self):
            return self.title