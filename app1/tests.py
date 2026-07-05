from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from .models import Transaction

User = get_user_model()

class StockPulseTests(TestCase):
    
    def test_user_registration_and_login(self):
        """
        Verify that a user can successfully register via the signup view
        and subsequently log in via the login view.
        """
        # 1. Register a new user account via the registration view (POST)
        response_signup = self.client.post(reverse('createuser'), {
            'username': 'testuser',
            'first_name': 'Test',
            'last_name': 'User',
            'email': 'testuser@example.com',
            'password': 'testpassword123'
        })
        # Check that registration redirects successfully (302 Redirect to Login)
        self.assertEqual(response_signup.status_code, 302)
        self.assertRedirects(response_signup, reverse('login'))
        
        # Verify the user record exists in the local database
        self.assertTrue(User.objects.filter(username='testuser').exists())

        # 2. Log in using the registered credentials
        response_login = self.client.post(reverse('login'), {
            'username': 'testuser',
            'password': 'testpassword123'
        })
        # Check that login redirects to the dashboard (302 Redirect to Dashboard)
        self.assertEqual(response_login.status_code, 302)
        self.assertRedirects(response_login, reverse('dashboard'))

    def test_hashed_password_user_login(self):
        """
        Verify that a user created with a standard hashed password (like terminal superusers)
        can successfully log in via the login view.
        """
        # Create a user with a standard hashed password using helper create_user
        user = User.objects.create_user(
            username='hasheduser',
            email='hashed@example.com',
            password='securepassword123',
            firstname='Hashed',
            lastname='User',
            balance=100000.0,
            watchlist={"symbol": ["AAPL"]}
        )
        
        # Verify the password is hashed in the database
        self.assertTrue(user.password.startswith('pbkdf2_sha256$'))

        # Log in via the standard login form POST
        response = self.client.post(reverse('login'), {
            'username': 'hasheduser',
            'password': 'securepassword123'
        })
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('dashboard'))

    def test_transaction_balance_deduction(self):
        """
        Verify that when a stock purchase transaction occurs, the purchase cost
        is correctly deducted from the user's cash balance.
        """
        # Create a user model record directly in the test database
        user = User.objects.create(
            username='buyer',
            firstname='Buyer',
            lastname='User',
            email='buyer@example.com',
            password='buyerpassword',
            balance=100000.0,
            watchlist={"symbol": ["AAPL"]}
        )
        # Log in the user to mock the authenticated session
        self.client.force_login(user)

        # Simulate buying 5 shares of AAPL at $150.00 each (Total cost = $750.00)
        response_trade = self.client.post(reverse('updatestocks'), {
            'quantity-input': '5',
            'symbolname': 'AAPL',
            'currentprice': '150.00',
            'buy': 'buy'
        })
        
        # Verify the trade redirects back to the dashboard
        self.assertEqual(response_trade.status_code, 302)
        self.assertRedirects(response_trade, reverse('dashboard'))

        # Reload user from the database to obtain updated balance
        user.refresh_from_db()
        
        # Assert balance is correctly deducted: $100,000.00 - $750.00 = $99,250.00
        self.assertEqual(user.balance, 99250.0)

    def test_transaction_history_pagination(self):
        """
        Verify that the transaction history page renders correctly and paginates
        results, showing exactly 10 records per page.
        """
        # Create a user model record
        user = User.objects.create(
            username='history_user',
            firstname='History',
            lastname='User',
            email='history@example.com',
            password='historypassword',
            balance=100000.0,
            watchlist={"symbol": ["AAPL"]}
        )
        self.client.force_login(user)

        # Create 12 transactions in the database for this user
        for i in range(12):
            Transaction.objects.create(
                user=user,
                symbol='AAPL',
                action='BUY',
                quantity=1,
                price=100.0 + i
            )

        # Request page 1
        response = self.client.get(reverse('transaction_history'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'main/transactions.html')
        
        # Check that page 1 has exactly 10 transactions
        transactions_on_page = response.context['transactions']
        self.assertEqual(len(transactions_on_page), 10)
        self.assertTrue(transactions_on_page.has_next())
        self.assertFalse(transactions_on_page.has_previous())

        # Request page 2
        response_page2 = self.client.get(reverse('transaction_history') + '?page=2')
        self.assertEqual(response_page2.status_code, 200)
        
        # Check that page 2 has exactly 2 transactions
        transactions_on_page2 = response_page2.context['transactions']
        self.assertEqual(len(transactions_on_page2), 2)
        self.assertFalse(transactions_on_page2.has_next())
        self.assertTrue(transactions_on_page2.has_previous())

    def test_portfolio_and_income_endpoints(self):
        """
        Verify that the /api/portfolio and /api/incomecalculate endpoints
        execute successfully without throwing JSONDecodeError, resolving
        from direct python data retrieval.
        """
        user = User.objects.create(
            username='api_test_user',
            firstname='API',
            lastname='Tester',
            email='apitester@example.com',
            password='apitesterpassword',
            balance=100000.0,
            watchlist={"symbol": ["AAPL"]}
        )
        self.client.force_login(user)

        # Mock stock holdings in user.stockbuy
        user.stockbuy = {
            "AAPL": {"quantity": 5, "boughtat": 150.0, "averageprice": 150.0}
        }
        user.save()

        # Call /api/portfolio
        response = self.client.get(reverse('portfolio'))
        self.assertEqual(response.status_code, 200)
        
        # Verify JSON list contains the mock stock item details
        data = response.json()
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['symbol'], 'AAPL')
        self.assertEqual(data[0]['quantity'], 5)

        # Call /api/incomecalculate
        response_income = self.client.get(reverse('income'))
        self.assertEqual(response_income.status_code, 200)
        # Should return a numeric value string representing profit/loss
        income_val = float(response_income.content.decode('utf-8'))
        self.assertIsInstance(income_val, float)
