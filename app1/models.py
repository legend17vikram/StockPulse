from django.db import models
from django.contrib.auth.models import AbstractUser

class users(AbstractUser):
    username = models.CharField(max_length=52, primary_key=True)
    firstname = models.CharField(max_length=52)
    lastname = models.CharField(max_length=52)
    email = models.EmailField(unique=True)

    datejoined = models.DateTimeField(auto_now_add=True) 
    balance = models.FloatField(default=100000.0)

    stockbuy = models.JSONField(default=dict)
    stocksold = models.JSONField(default=dict)
    watchlist = models.JSONField(default=list)
    cache = models.JSONField(default=list)

    def __str__(self):
        return self.username

class Transaction(models.Model):
    TRANSACTION_TYPES = (
        ('BUY', 'Buy'),
        ('SELL', 'Sell'),
    )
    user = models.ForeignKey(users, on_delete=models.CASCADE, related_name='transactions')
    symbol = models.CharField(max_length=15)
    action = models.CharField(max_length=4, choices=TRANSACTION_TYPES)
    quantity = models.PositiveIntegerField()
    price = models.FloatField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.action} {self.quantity} {self.symbol} @ {self.price}"

    @property
    def total_amount(self):
        return self.quantity * self.price