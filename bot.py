import requests, json, os
from datetime import datetime

BALANCE_FILE = "balance.json"
TAKE_PROFIT = 12  # Πουλάει 25% όταν έχει +12% κέρδος

def get_price(product):
    try:
        r = requests.get(f"https://api.exchange.coinbase.com/products/{product}/ticker", timeout=10).json()
        return float(r['price'])
    except:
        return None

def get_rsi(product, period=14):
    try:
        r = requests.get(f"https://api.exchange.coinbase.com/products/{product}/candles?granularity=3600", timeout=10).json()
        closes = [c[4] for c in r[:period+1]][::-1]
        gains = [max(closes[i]-closes[i-1],0) for i in range(1,len(closes))]
        losses = [abs(min(closes[i]-closes[i-1],0)) for i in range(1,len(closes))]
        avg_g = sum(gains[-period:])/period
        avg_l = sum(losses[-period:])/period
        if avg_l == 0: return 30
        rs = avg_g / avg_l
        return 100 - (100/(1+rs))
    except:
        return 50

def get_fear_greed():
    try:
        r = requests.get("https://api.alternative.me/fng/?limit=1", timeout=10).json()
        return int(r['data'][0]['value'])
    except:
        return 50

def load():
    if os.path.exists(BALANCE_FILE):
        return json.load(open(BALANCE_FILE))
    return {"EUR_locked": 0, "BTC": 0, "ETH": 0, "BTC_avg": 0, "ETH_avg": 0}

def save(s):
    json.dump(s, open(BALANCE_FILE, "w"), indent=2)

def score(rsi, fng):
    sc = 0
    if rsi < 30: sc += 50
    elif rsi < 40: sc += 30
    elif rsi < 50: sc += 10
    if fng < 20: sc += 40
    elif fng < 35: sc += 25
    elif fng < 50: sc += 10
    return sc

def main():
    fng = get_fear_greed()
    st = load()
    print(f"--- {datetime.now()} --- Fear&Greed: {fng}")

    for asset in ["BTC", "ETH"]:
        prod = f"{asset}-EUR"
        price = get_price(prod)
        rsi = get_rsi(prod)
        if not price:
            continue
        
        sc = score(rsi, fng)
        print(f"{prod}: {price:.2f} EUR | RSI {rsi:.1f} | Score {sc}/100")

        # TAKE PROFIT LOGIC
        if st[asset] > 0 and st[f"{asset}_avg"] > 0:
            pnl = (price - st[f"{asset}_avg"]) / st[f"{asset}_avg"] * 100
            print(f"  PnL {asset}: {pnl:.2f}%")
            if pnl >= TAKE_PROFIT:
                sell_amount = st[asset] * 0.25
                st[asset] -= sell_amount
                st["EUR_locked"] += sell_amount * price
                print(f"  >>> TAKE PROFIT! Sold 25% {asset}")

        # BUY LOGIC - Μόνο όταν αξίζει
        if sc >= 50:
            buy_eur = round(3 + sc/20, 2)  # 3€ έως 7€ ανάλογα το score
            amount = buy_eur / price
            prev_cost = st[f"{asset}_avg"] * (st[asset] - amount) if st[f"{asset}_avg"] else 0
            # Διόρθωση για σωστό μέσο όρο
            if st[asset] == 0:
                st[f"{asset}_avg"] = price
            else:
                # recalc με νέο buy
                old_total = st[f"{asset}_avg"] * (st[asset])
                new_total = old_total + buy_eur
                st[asset] += amount
                st[f"{asset}_avg"] = new_total / st[asset] if st[asset] else price
                # Αν ήταν η πρώτη αγορά, το παραπάνω double-counted, φτιάξτο:
                if old_total == 0:
                    st[asset] = amount
                    st[f"{asset}_avg"] = price
            if st[asset] == amount and old_total == 0:
                pass # ήδη μπήκε
            elif old_total != 0:
                pass
            else:
                st[asset] = amount

            # Απλοποιημένο σωστό:
            # Ξαναφόρτωσε για σιγουριά
            # Θα το κάνουμε clean:
            st = load()
            # Ξανα-κάνε buy clean
            # Για να μην μπερδευτείς, κράτα το απλό:
            print(f"  >>> BUY {buy_eur}€ -> {amount:.6f} {asset}")
            # Reload και apply
            st["EUR_locked"] = st.get("EUR_locked", 0)
            if st[f"{asset}_avg"] == 0:
                st[asset] = amount
                st[f"{asset}_avg"] = price
            else:
                total_cost = st[f"{asset}_avg"] * st[asset] + buy_eur
                st[asset] += amount
                st[f"{asset}_avg"] = total_cost / st[asset]
        else:
            print(f"  SKIP - Ακριβή αγορά, περιμένει καλύτερη ώρα")

    # Τελικό save με σωστή λογική (clean version για να μην έχεις bug)
    # Ξανατρέχουμε την λογική καθαρά για το save:
    st_final = load()
    for asset in ["BTC", "ETH"]:
        prod = f"{asset}-EUR"
        price = get_price(prod)
        rsi = get_rsi(prod)
        sc = score(rsi, get_fear_greed())
        if not price: continue
        if st_final[asset] > 0 and st_final[f"{asset}_avg"] > 0:
            pnl = (price - st_final[f"{asset}_avg"]) / st_final[f"{asset}_avg"] * 100
            if pnl >= TAKE_PROFIT:
                sell_amount = st_final[asset] * 0.25
                st_final[asset] -= sell_amount
                st_final["EUR_locked"] += sell_amount * price
        if sc >= 50:
            buy_eur = round(3 + sc/20, 2)
            amount = buy_eur / price
            if st_final[f"{asset}_avg"] == 0:
                st_final[asset] = amount
                st_final[f"{asset}_avg"] = price
            else:
                total = st_final[f"{asset}_avg"] * st_final[asset] + buy_eur
                st_final[asset] += amount
                st_final[f"{asset}_avg"] = total / st_final[asset]

    save(st_final)
    print(f"Saved state: {st_final}")

if __name__ == "__main__":
    main()
