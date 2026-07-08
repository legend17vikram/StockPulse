import finnhub

def test_finnhub():
    api_key = "d1of599r01qjadrjodh0d1of599r01qjadrjodhg"
    client = finnhub.Client(api_key=api_key)
    try:
        quote = client.quote('AAPL')
        print("Finnhub AAPL Quote:", quote)
    except Exception as e:
        print("Finnhub Error:", e)

test_finnhub()
