from django.contrib import admin
from . import models

admin.site.register(models.Warehouse)
admin.site.register(models.Carrier)
admin.site.register(models.Customer)
admin.site.register(models.Product)
admin.site.register(models.SalesOrder)
admin.site.register(models.OrderItem)
admin.site.register(models.Shipment)
admin.site.register(models.ProductReturn)