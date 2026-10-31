import os, json, requests

# Διαβάζει τα κλειδιά από τα Secrets (ασφαλώς)
API_KEY = os.getenv("COINBASE_API_KEY")
API_SECRET = os.getenv("COINBASE_API_SECRET")

# Τσεκάρει τιμή BTC/ETH
def get_price(coin):
    r = requests.get(f"https://api.coinbase.com/v2/prices/{coin}-EUR/spot")
    return float(r.json()['data']['amount'])

btc = get_price("BTC")
eth = get_price("ETH")
print(f"BTC: {btc} EUR, ETH: {eth} EUR")

# Φορτώνει το πορτοφόλι
try:
    with open("balance.json") as f:
        bal = json.load(f)
except:
    bal = {"EUR_locked": 1000, "BTC": 0, "ETH": 0}

print(f"Balance: {bal}")

# Εδώ είναι η στρατηγική - προς το παρόν κάνει μόνο PAPER trading για ασφάλεια
# Για REAL trading θα βάλουμε μετά εντολή αγοράς

# Save
with open("balance.json", "w") as f:
    json.dump(bal, f, indent=2)

print("Bot finished OK")
