from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import users, Transaction

class CustomUserAdmin(UserAdmin):
    model = users
    list_display = ['username', 'email', 'firstname', 'lastname', 'balance', 'is_staff']
    fieldsets = UserAdmin.fieldsets + (
        ('Trading Portfolio', {'fields': ('balance', 'stockbuy', 'stocksold', 'watchlist', 'cache')}),
    )

class TransactionAdmin(admin.ModelAdmin):
    list_display = ['user', 'symbol', 'action', 'quantity', 'price', 'timestamp']
    list_filter = ['action', 'symbol', 'timestamp']
    search_fields = ['user__username', 'symbol']

admin.site.register(users, CustomUserAdmin)
admin.site.register(Transaction, TransactionAdmin)