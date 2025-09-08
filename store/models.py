from django.db import models
from django.urls import reverse
from shop.settings import AUTH_USER_MODEL
from django.utils import timezone



class Product(models.Model):
    name = models.CharField(max_length=128)
    slug = models.SlugField(max_length=128)
    price = models.FloatField(default=0.0)
    stock = models.IntegerField(default=0)
    description = models.TextField(blank=True)
    thumbnail = models.ImageField(upload_to="products", blank=True, null=True)
    date_added = models.DateTimeField(auto_now=True)


    class Meta:
         ordering = ['date_added']

    def __str__(self):
        return f"{self.name} ({self.stock})"
    
    def get_absolute_url(self):
        return reverse("product", kwargs={"slug": self.slug})
    

    # Article (Order)
class Order(models.Model):
        user = models.ForeignKey(AUTH_USER_MODEL, on_delete=models.CASCADE)
        product = models.ForeignKey(Product, on_delete=models.CASCADE)
        quantity = models.IntegerField(default=1)
        ordered = models.BooleanField(default=False)
        ordered_date = models.DateTimeField(blank=True, null=True)
        shipping_adress = models.TextField(blank=True, null=True)
        phone_number = models.CharField(max_length=20, blank=True, null=True)


        def __str__(self):
             return f"{self.product.name} ({self.quantity})"
    # Panier (Cart)
class Cart(models.Model):
     user = models.OneToOneField(AUTH_USER_MODEL, on_delete=models.CASCADE)
     orders = models.ManyToManyField(Order)

     def __str__(self):
          return self.user.username
     

     def delete(self, *args, **kwargs):
          for order in self.orders.all():
               order.ordered = True
               order.ordered_date = timezone.now()
               order.save()
          
          
          self.orders.clear()
          super().delete(*args, **kwargs)
    
     def get_total(self):
      return sum(order.product.price * order.quantity for order in self.orders.all())


class Payment(models.Model):
     PAYMENT_CHOICES = [
          ("cash", "Paiement à la livraison"),
          ("stripe", "Paiement en ligne (Stripe)")
     ]

     user = models.ForeignKey(AUTH_USER_MODEL, on_delete=models.CASCADE)
     cart = models.ForeignKey('Cart', on_delete= models.CASCADE)
     method = models.CharField(max_length=20, choices=PAYMENT_CHOICES)
     amount =models.FloatField()
     successful = models.BooleanField(default=False)
     created_at =models.DateTimeField(auto_now_add=True)

     def __str__(self):
          return f"{self.user.username} - {self.method} - {self.amount} $"