import os
import requests
import schedule
import time
from datetime import datetime

# ── NASTAVENIA ──────────────────────────────────────────────
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "SEM_VLOZ_SVOJ_TOKEN")
CHAT_ID        = os.environ.get("CHAT_ID",        "SEM_VLOZ_SVOJE_CHAT_ID")

# Časy kedy chceš dostávať notifikácie (24h formát)
NOTIFY_TIMES = [
    "06:30",
    "18:30",
]
# ────────────────────────────────────────────────────────────


def get_prices():
    """Stiahne ceny z KuCoin + EUR kurz z Frankfurter."""
    try:
        btc_resp = requests.get(
            "https://api.kucoin.com/api/v1/market/stats?symbol=BTC-USDT",
            timeout=15, headers={"User-Agent": "Mozilla/5.0"}
        ).json()["data"]

        sol_resp = requests.get(
            "https://api.kucoin.com/api/v1/market/stats?symbol=SOL-USDT",
            timeout=15, headers={"User-Agent": "Mozilla/5.0"}
        ).json()["data"]

        eur_rate = requests.get(
            "https://api.frankfurter.app/latest?from=USD&to=EUR",
            timeout=15
        ).json()["rates"]["EUR"]

        btc_usd = float(btc_resp["last"])
        sol_usd = float(sol_resp["last"])
        btc_24h = float(btc_resp["changeRate"]) * 100
        sol_24h = float(sol_resp["changeRate"]) * 100

        return {
            "btc_usd": btc_usd,
            "btc_eur": btc_usd * eur_rate,
            "btc_24h": btc_24h,
            "sol_usd": sol_usd,
            "sol_eur": sol_usd * eur_rate,
            "sol_24h": sol_24h,
        }
    except Exception as e:
        print(f"Chyba pri načítaní cien: {e}")
        return None


def format_change(pct):
    arrow = "📈" if pct >= 0 else "📉"
    sign  = "+" if pct >= 0 else ""
    return f"{arrow} {sign}{pct:.2f}%"


def send_notification():
    """Stiahne ceny a pošle správu cez Telegram."""
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Posielam notifikáciu...")
    prices = get_prices()

    if not prices:
        msg = "⚠️ CryptoAlert: Nepodarilo sa načítať ceny."
    else:
        now = datetime.now().strftime("%d.%m.%Y %H:%M")
        msg = (
            f"📊 *CryptoAlert* — {now}\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"\n"
            f"◎ *Solana*\n"
            f"  💶 `€{prices['sol_eur']:.2f}`\n"
            f"  💵 `${prices['sol_usd']:.2f}`\n"
            f"  {format_change(prices['sol_24h'])} za 24h\n"
            f"\n"
            f"₿ *Bitcoin*\n"
            f"  💶 `€{prices['btc_eur']:,.0f}`\n"
            f"  💵 `${prices['btc_usd']:,.0f}`\n"
            f"  {format_change(prices['btc_24h'])} za 24h\n"
        )

    try:
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            json={
                "chat_id": CHAT_ID,
                "text": msg,
                "parse_mode": "Markdown",
            },
            timeout=10,
        )
        print("✅ Správa odoslaná!")
    except Exception as e:
        print(f"❌ Chyba pri odosielaní: {e}")


def main():
    print("🤖 CryptoAlert bot štartuje...")
    print(f"📅 Naplánované časy: {', '.join(NOTIFY_TIMES)}")

    # Naplánuj všetky časy
    for t in NOTIFY_TIMES:
        schedule.every().day.at(t).do(send_notification)
        print(f"   ⏰ {t}")

    print("✅ Bot beží. Čakám na naplánované časy...\n")

    # Pošli testovaciu správu pri štarte
    send_notification()

    while True:
        schedule.run_pending()
        time.sleep(30)


if __name__ == "__main__":
    main()
