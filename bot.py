import requests, json, os
from datetime import datetime

BALANCE_FILE = "balance.json"
TAKE_PROFIT = 12

def get_price(p):
    try:
        r = requests.get(f"https://api.exchange.coinbase.com/products/{p}/ticker", timeout=10).json()
        return float(r['price'])
    except:
        return None

def get_rsi(p):
    try:
        r = requests.get(f"https://api.exchange.coinbase.com/products/{p}/candles?granularity=3600", timeout=10).json()
        closes = [c[4] for c in r[:15]][::-1]
        gains = [max(closes[i]-closes[i-1],0) for i in range(1,len(closes))]
        losses = [abs(min(closes[i]-closes[i-1],0)) for i in range(1,len(closes))]
        avg_g = sum(gains[-14:])/14
        avg_l = sum(losses[-14:])/14
        if avg_l==0:
            return 30
        rs = avg_g/avg_l
        return 100-(100/(1+rs))
    except:
        return 50

def get_fng():
    try:
        return int(requests.get("https://api.alternative.me/fng/?limit=1", timeout=10).json()['data'][0]['value'])
    except:
        return 50

def load():
    if os.path.exists(BALANCE_FILE):
        return json.load(open(BALANCE_FILE))
    return {"EUR_locked":0, "BTC":0, "ETH":0, "BTC_avg":0, "ETH_avg":0}

def save(s):
    json.dump(s, open(BALANCE_FILE,"w"), indent=2)

st = load()
fng = get_fng()
print(f"RUN FNG:{fng} BALANCE:{st}")

for asset in ["BTC","ETH"]:
    price = get_price(f"{asset}-EUR")
    rsi = get_rsi(f"{asset}-EUR")
    if not price:
        continue
    score = 0
    if rsi < 30: score+=50
    elif rsi < 40: score+=30
    elif rsi < 50: score+=10
    if fng < 20: score+=40
    elif fng < 35: score+=25
    elif fng < 50: score+=10
    print(f"{asset} {price} RSI:{rsi:.1f} SCORE:{score}")
    if st[asset]>0 and st[f"{asset}_avg"]>0:
        pnl = (price - st[f"{asset}_avg"])/st[f"{asset}_avg"]*100
        if pnl >= TAKE_PROFIT:
            sell = st[asset]*0.25
            st[asset]-=sell
            st["EUR_locked"]+=sell*price
            print(f"SOLD 25%")
    if score >= 50:
        buy_eur = round(3 + score/20, 2)
        amount = buy_eur/price
        if st[f"{asset}_avg"]==0:
            st[asset]=amount
            st[f"{asset}_avg"]=price
        else:
            total = st[f"{asset}_avg"]*st[asset] + buy_eur
            st[asset]+=amount
            st[f"{asset}_avg"]=total/st[asset]
        print(f"BUY {buy_eur} EUR")
    else:
        print(f"SKIP")

save(st)
print(f"FINAL: {st}")
