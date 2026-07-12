import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'demostocks.settings')
django.setup()

from app1.models import users, Transaction

def reset_user_profile(username):
    try:
        user = users.objects.get(username=username)
        user.balance = 100000.0
        user.stockbuy = {}
        user.stocksold = {}
        user.save()
        
        # Clear transaction logs for this user to start fresh
        Transaction.objects.filter(user=user).delete()
        print(f"SUCCESS: Profile reset for user '{username}'. Balance restored to $100,000.00 and holdings cleared.")
    except users.DoesNotExist:
        print(f"ERROR: User '{username}' not found.")

if __name__ == "__main__":
    import sys
    uname = sys.argv[1] if len(sys.argv) > 1 else "rajvikram"
    reset_user_profile(uname)
