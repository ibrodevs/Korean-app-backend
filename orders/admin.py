from django.contrib import admin
from .models import Order, OrderItem, OrderStatusHistory, PickupLocation

# Register your models here.

admin.site.register(Order)
admin.site.register(OrderItem)
admin.site.register(OrderStatusHistory)
admin.site.register(PickupLocation)