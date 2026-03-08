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
    "07:30",
    "19:30",
]
# ────────────────────────────────────────────────────────────


def get_prices():
    """Stiahne ceny z CoinGecko (funguje zo serverov bez obmedzení)."""
    try:
        resp = requests.get(
            "https://api.coingecko.com/api/v3/simple/price"
            "?ids=bitcoin,solana&vs_currencies=eur,usd&include_24hr_change=true",
            timeout=15,
            headers={"User-Agent": "CryptoAlertBot/1.0"}
        ).json()

        return {
            "btc_usd": resp["bitcoin"]["usd"],
            "btc_eur": resp["bitcoin"]["eur"],
            "btc_24h": resp["bitcoin"]["usd_24h_change"],
            "sol_usd": resp["solana"]["usd"],
            "sol_eur": resp["solana"]["eur"],
            "sol_24h": resp["solana"]["usd_24h_change"],
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
