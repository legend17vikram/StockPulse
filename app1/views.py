from django.http import JsonResponse
from django.shortcuts import render, HttpResponse, redirect
from .models import users, Transaction
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
import requests as req
from .mdate import today
from django.core.paginator import Paginator

# Create your views here.
def home(request):
    return HttpResponse("Hello World!!")

def signup(request):
    data = {"isusername": "hidden", "isemail": "hidden"}
    return render(request, "login/signup.html", data)

def user_login(request):
    if request.method == "POST":
        uname = request.POST.get("username")
        pword = request.POST.get("password")

        try:
            # Query the user from the database
            user = users.objects.get(username=uname)
        except users.DoesNotExist:
            # Username does not exist
            data = {"isusername": "visible", "ispasswordcorrect": "hidden"}
            return render(request, "login/login.html", data)

        # Check password correctness:
        # 1. First attempt to check using Django's standard hashing verification (e.g. for terminal superusers)
        # 2. Fallback to direct plaintext string comparison (e.g. for frontend registered users)
        is_correct_password = False
        if user.check_password(pword):
            is_correct_password = True
        elif user.password == pword:
            is_correct_password = True

        if is_correct_password:
            # Successfully authenticated, log the user in and redirect to dashboard
            auth_login(request, user)
            return redirect("dashboard")
        else:
            # Password mismatch
            data = {"isusername": "hidden", "ispasswordcorrect": "visible"}
            return render(request, "login/login.html", data)

    data = {"isusername": "hidden", "ispasswordcorrect": "hidden"}
    return render(request, "login/login.html", data)

def createuser(request):
    if request.method == "POST":
        uname = request.POST.get("username")
        fname = request.POST.get("first_name")
        lname = request.POST.get("last_name")
        mail = request.POST.get("email")
        pword = request.POST.get("password")

        def checkusername(text):
            return users.objects.filter(username=text).count()

        def checkemail(text):
            return users.objects.filter(email=text).count()

        ucount = checkusername(uname)
        ecount = checkemail(mail)

        if ucount == 1 and ecount == 1:
            data = {"isusername": "visible", "isemail": "visible"}
            return render(request, "login/signup.html", data)
        if ucount == 1:
            data = {"isusername": "visible", "isemail": "hidden"}
            return render(request, "login/signup.html", data)
        elif ecount == 1:
            data = {"isusername": "hidden", "isemail": "visible"}
            return render(request, "login/signup.html", data)

        if ucount == 0 and ecount == 0:
            adduser = users(
                username=uname,
                firstname=fname,
                lastname=lname,
                email=mail,
                password=pword,
                watchlist={"symbol": ["SONY", "MSFT", "META", "GOOG", "AAPL"]}
            )
            adduser.save()
            return redirect("login")
    else:
        return redirect("login")

def logout(request):
    auth_logout(request)
    return HttpResponse("Logout!!")

def user_a(request):
    if request.user.is_authenticated:
        user = request.user
        stockname = user.stockbuy.keys()
        stock = []
        price = []
        for i in stockname:
            stock.append(i)
            price.append(user.stockbuy[i]["boughtat"] * user.stockbuy[i]["quantity"])
        watchlistsymbols = ",".join(user.watchlist["symbol"])
        data = {
            "username": user.username,
            "name": user.firstname,
            "email": user.email,
            "totalbalance": round(user.balance, 2),
            "watchlist": watchlistsymbols,
            "stocklist": user.watchlist["symbol"],
            "stock": list(stockname),
            "price": price,
            "start": today() - 457199,
            "end": today(),
            "currentlyholding": "hidden",
            "marketstatusclass" : "hidden",
        }
        return data

def dashboard(request):
    if request.user.is_authenticated:
        data = user_a(request)
        data["title"] = "Dashboard"
        return render(request, "main/dashboard.html", data)
    else:
        return redirect("login")

def stockdetails(request, query):
    if request.user.is_authenticated:
        # Check if the view is loaded as an embedded iframe
        is_embedded = request.GET.get("embed") == "true"
        base_template = "main/embed_base.html" if is_embedded else "main/dashboardbase.html"

        todayepoch = int(today())
        start = str(todayepoch - 457199)
        end = str(todayepoch)
        url = f"https://query2.finance.yahoo.com/v8/finance/chart/{query}?period1={start}&period2={end}&interval=5m&includePrePost=true&events=div%7Csplit%7Cearn&&lang=en-US&region=US"
        headers = {
            "User-Agent": "Mozilla/5.0 (iPad; CPU OS 12_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148"
        }
        store = {}
        previousclose = 0.0
        try:
            response = req.get(url, headers=headers, timeout=5)
            response.raise_for_status()
            data = response.json()
            
            chart_result = data.get("chart", {}).get("result")
            if not chart_result:
                raise ValueError("Empty or invalid chart data from Yahoo Finance API")
                
            meta_data = chart_result[0].get("meta", {})
            previousclose = meta_data.get("previousClose", 0.0)

            for i in meta_data.keys():
                if i in ("firstTradeDate", "regularMarketTime", "hasPrePostMarketData", "gmtoffset", "timezone", "instrumentType", "fullExchangeName", "regularMarketVolume", "previousClose", "regularMarketPrice"):
                    continue
                if i == "scale":
                    break
                store[i.capitalize()] = meta_data[i]
        except Exception as e:
            print(f"Error fetching stock details for {query}: {e}")
            return redirect("errorpage")

        user = request.user
        watchlistsymbols = ",".join(user.watchlist.get("symbol", []))
        data_context = {
            "username": user.username,
            "name": user.firstname,
            "email": user.email,
            "totalbalance": round(user.balance, 2),
            "watchlist": watchlistsymbols,
            "data": store,
            "query": query,
            "previousclose": previousclose,
            "start": start,
            "end": end,
            "title": query,
            "base_template": base_template,
            "is_embedded": is_embedded,
        }
        return render(request, "main/details.html", data_context)
    else:
        return redirect("login")

def removewatchlist(request, symbol):
    user = request.user
    watchlist_symbols = user.watchlist.get("symbol", [])

    if len(watchlist_symbols) > 1 and symbol in watchlist_symbols:
        watchlist_symbols.remove(symbol)
        user.watchlist["symbol"] = watchlist_symbols
        user.save()

    return redirect("dashboard")

def updatestocks(request):
    if request.method == "POST":
        quantity = int(request.POST.get("quantity-input") or 0)
        name = request.POST.get("symbolname")
        currentprice_raw = request.POST.get("currentprice")
        
        if currentprice_raw:
            try:
                currentprice = float(currentprice_raw)
            except ValueError:
                currentprice = 0.0
        else:
            currentprice = 0.0

        if currentprice <= 0.0 and name:
            from app1.apis import fetch_yahoo_quotes
            quotes = fetch_yahoo_quotes(name)
            if quotes and len(quotes) > 0:
                currentprice = float(quotes[0].get("price", 0.0))

        user = request.user

        if "buy" in request.POST:
            if quantity == 0 or currentprice * quantity > user.balance:
                return render(request, "main/error.html")

            # Add to watchlist automatically
            watchlist_symbols = user.watchlist.get("symbol", [])
            if name not in watchlist_symbols:
                watchlist_symbols.append(name)
                user.watchlist["symbol"] = watchlist_symbols

            if name in user.stockbuy:
                previousprice = user.stockbuy[name]["quantity"] * user.stockbuy[name]["boughtat"]
                currentshareprice = quantity * currentprice
                totalquantity = user.stockbuy[name]["quantity"] + quantity
                averageprice = (previousprice + currentshareprice) / totalquantity
                user.stockbuy[name] = {
                    "quantity": totalquantity,
                    "boughtat": currentprice,
                    "averageprice": averageprice,
                    "purchaseat": "date"
                }
            else:
                user.stockbuy[name] = {
                    "quantity": quantity,
                    "boughtat": currentprice,
                    "averageprice": currentprice,
                    "purchaseat": "date"
                }
            user.balance -= quantity * currentprice
            user.save()

            # Record Transaction History
            Transaction.objects.create(
                user=user,
                symbol=name,
                action='BUY',
                quantity=quantity,
                price=currentprice
            )

        if "sell" in request.POST:
            if name in user.stockbuy:
                if quantity > user.stockbuy[name]["quantity"]:
                    return render(request, "main/error.html")
                if user.stockbuy[name]["quantity"] == quantity:
                    user.stockbuy.pop(name)
                else:
                    user.stockbuy[name]["quantity"] -= quantity
                user.balance += quantity * currentprice
                user.save()

                # Record Transaction History
                Transaction.objects.create(
                    user=user,
                    symbol=name,
                    action='SELL',
                    quantity=quantity,
                    price=currentprice
                )

        return redirect("dashboard")
    else:
        return render(request, "login/login.html")

def user_portfolio(request):
    if request.user.is_authenticated:
        user = request.user
        stockname = user.stockbuy.keys()
        stock = []
        price = []
        for i in stockname:
            stock.append(i)
            price.append(user.stockbuy[i]["boughtat"] * user.stockbuy[i]["quantity"])
        watchlistsymbols = ",".join(user.watchlist["symbol"])
        
        print("--- USER PORTFOLIO DIAGNOSTIC LOG ---")
        print("User:", user.username)
        print("Stocks List:", stock)
        print("Prices List:", price)
        print("Start timestamp:", today() - 457199)
        print("End timestamp:", today())
        
        data = {
            "username": user.username,
            "name": user.firstname,
            "email": user.email,
            "totalbalance": round(user.balance, 2),
            "watchlist": watchlistsymbols,
            "stock": stock,
            "price": price,
            "start": today() - 457199,
            "end": today(),
            "currentlyholding": "hidden",
            "marketstatusclass" : "hidden",

        }
        return render(request, "main/portfolio.html", data)
    else:
        return redirect("login")

def errorpage(request):
    if request.user.is_authenticated:
        user = request.user
        stockname = user.stockbuy.keys()
        stock = []
        price = []
        for i in stockname:
            stock.append(i)
            price.append(user.stockbuy[i]["boughtat"] * user.stockbuy[i]["quantity"])
        watchlistsymbols = ",".join(user.watchlist["symbol"])
        data = {
            "username": user.username,
            "name": user.firstname,
            "email": user.email,
            "totalbalance": round(user.balance, 2),
            "watchlist": watchlistsymbols,
            "stock": stock,
            "price": price,
        }
        return render(request, "main/error.html", data)
    else:
        return redirect("login")

def settings(request):
    if request.user.is_authenticated:
        data = user_a(request)
        data["currentcheck"] = "hidden"
        data["matchcheck"] = "hidden"
        data["title"] = "Settings"
        if request.method == "POST":
            currentPass = request.POST.get("currentpassword")
            newpass = request.POST.get("newpassword")
            repeatpass = request.POST.get("repeat-password")
            user = request.user
            if user.password == currentPass:
                if newpass == repeatpass:
                    data["matchcheck"] = "hidden"
                    user.password = newpass
                    user.save()
                else:
                    data["matchcheck"] = "visible"
            else:
                data["currentcheck"] = "visible"
    return render(request, "main/settings.html", data)

from django.http import JsonResponse
from django.contrib.auth.decorators import login_required

from django.http import JsonResponse

from django.http import JsonResponse

def user_data_api(request):
    try:
        user = request.user
        
        # 1. Get watchlist symbols (from JSON array)
        watchlist_symbols = user.watchlist.get("symbol", []) if isinstance(user.watchlist, dict) else []
        
        # 2. Get stockbuy symbols (extract keys from JSON dict)
        stockbuy_symbols = list(user.stockbuy.keys()) if isinstance(user.stockbuy, dict) else []
        
        # 3. Merge and deduplicate (using Python set)
        unique_symbols = sorted(set(watchlist_symbols + stockbuy_symbols))
        
        # 4. Return only the merged unique symbols
        return JsonResponse({
            "symbols": unique_symbols  # Clean response with no duplicates
        })

    except Exception as e:
        print(f"\n❌ ERROR: {e}\n")
        return JsonResponse({"error": str(e)}, status=500)

def reset_db_view(request):
    if request.user.is_authenticated:
        user = request.user
        user.balance = 100000.0
        user.stockbuy = {}
        user.stocksold = {}
        user.save()
        
        # Clear transaction logs for this user to start fresh
        Transaction.objects.filter(user=user).delete()
        return HttpResponse(f"SUCCESS: Profile reset for user '{user.username}'. Balance restored to $100,000.00 and holdings cleared. <a href='/dashboard'>Go back to Dashboard</a>")
    else:
        return redirect("login")

def make_admin_view(request):
    # Check if 'admin' user already exists, or create a new one
    uname = "admin"
    email = "admin@example.com"
    pword = "adminpassword123"
    
    user, created = users.objects.get_or_create(username=uname)
    user.email = email
    user.firstname = "Admin"
    user.lastname = "User"
    user.set_password(pword)
    user.is_superuser = True
    user.is_staff = True
    user.save()
    
    return HttpResponse(f"SUCCESS: Superuser '{uname}' created/updated with password '{pword}'. Go to <a href='/admin/'>/admin/</a> and log in!")

def transaction_history(request):
    if request.user.is_authenticated:
        data = user_a(request)
        data["title"] = "Transaction History"
        transactions_list = Transaction.objects.filter(user=request.user).order_by('-timestamp')
        
        # Paginate results - 10 records per page
        paginator = Paginator(transactions_list, 10)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        data["transactions"] = page_obj
        return render(request, "main/transactions.html", data)
    else:
        return redirect("login")