from django.db import models
from django.db.models import F, Q
from django.utils import timezone


class Warehouse(models.Model):
    code = models.CharField("código", max_length=20, unique=True)
    name = models.CharField("nombre", max_length=100)
    region = models.CharField("región", max_length=100)

    class Meta:
        verbose_name = "Bodega"
        verbose_name_plural = "Bodegas"
        ordering = ["code"]

    def __str__(self):
        return f"{self.code} - {self.name}"


class Carrier(models.Model):
    name = models.CharField("nombre", max_length=100, unique=True)

    class Meta:
        verbose_name = "Transportista"
        verbose_name_plural = "Transportistas"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Customer(models.Model):
    external_id = models.CharField(max_length=50, unique=True)
    name = models.CharField("nombre", max_length=100)
    email = models.EmailField(max_length=100, null=True, blank=True)
    region = models.CharField("región", max_length=100)
    comuna = models.CharField(max_length=100)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"

    def __str__(self):
        return self.name


class Product(models.Model):
    sku = models.CharField(max_length=40, unique=True)
    name = models.CharField("nombre", max_length=100)
    category = models.CharField("categoría", max_length=80)
    unit_cost = models.PositiveBigIntegerField("costo unitario (CLP)")
    unit_price = models.PositiveBigIntegerField("precio unitario (CLP)")
    active = models.BooleanField("activo", default=True)

    class Meta:
        verbose_name = "Producto"
        verbose_name_plural = "Productos"
        ordering = ["sku"]

    def __str__(self):
        return f"{self.sku} - {self.name}"


class SalesOrder(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pendiente"
        PAID = "paid", "Pagada"
        SHIPPED = "shipped", "Enviada"
        DELIVERED = "delivered", "Entregada"
        CANCELLED = "cancelled", "Cancelada"

    external_id = models.CharField(max_length=50, unique=True)
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField(default=timezone.now, db_index=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    destination_region = models.CharField("región de destino", max_length=100)

    class Meta:
        verbose_name = "Orden de venta"
        verbose_name_plural = "Órdenes de venta"

    def __str__(self):
        return self.external_id


class OrderItem(models.Model):
    external_id = models.CharField(max_length=60, unique=True)
    order = models.ForeignKey(SalesOrder, on_delete=models.PROTECT)
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    warehouse = models.ForeignKey(Warehouse, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField("cantidad")
    unit_price = models.PositiveBigIntegerField("precio unitario (CLP)")
    unit_cost = models.PositiveBigIntegerField("costo unitario (CLP)")

    class Meta:
        verbose_name = "Ítem de orden"
        verbose_name_plural = "Ítems de orden"
        constraints = [
            models.CheckConstraint(
                condition=Q(quantity__gt=0), name="order_item_quantity_gt_0"
            ),
        ]

    def __str__(self):
        return f"{self.order} - {self.product}"

class Shipment(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pendiente"
        SHIPPED = "shipped", "Enviado"
        DELIVERED = "delivered", "Entregado"
        CANCELLED = "cancelled", "Cancelado"

    order = models.ForeignKey(SalesOrder, on_delete=models.PROTECT)
    warehouse = models.ForeignKey(Warehouse, on_delete=models.PROTECT)
    carrier = models.ForeignKey(Carrier, on_delete=models.PROTECT)
    shipped_at = models.DateTimeField(null=True, blank=True)
    promised_at = models.DateTimeField("fecha prometida")
    delivered_at = models.DateTimeField(null=True, blank=True, db_index=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)

    class Meta:
        verbose_name = "Envío"
        verbose_name_plural = "Envíos"
        constraints = [
            models.UniqueConstraint(
                fields=["order", "warehouse"], name="shipment_unique_order_warehouse"
            ),
            models.CheckConstraint(
                condition=Q(shipped_at__isnull=True)
                | Q(delivered_at__isnull=True)
                | Q(delivered_at__gte=F("shipped_at")),
                name="shipment_delivered_after_shipped",
            ),
        ]

    def __str__(self):
        return f"{self.order} - {self.warehouse}"


class ProductReturn(models.Model):
    external_id = models.CharField(max_length=50, unique=True)
    order_item = models.ForeignKey(OrderItem, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField("cantidad")
    reason = models.CharField("motivo", max_length=50)
    refund_amount = models.PositiveBigIntegerField("monto de reembolso (CLP)")
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name = "Devolución de producto"
        verbose_name_plural = "Devoluciones de productos"
        constraints = [
            models.CheckConstraint(
                condition=Q(quantity__gt=0), name="product_return_quantity_gt_0"
            ),
        ]

    def __str__(self):
        return f"{self.order_item} - {self.reason}"