import requests
import json
import os
from bs4 import BeautifulSoup

# Pobieramy token i chat_id z ENV
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# URL z OLX dla mieszkań na wynajem w Opolu
OLX_URL = "https://www.olx.pl/nieruchomosci/mieszkania/wynajem/opole/"

HISTORY_FILE = "history.json"

def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }
    resp = requests.post(url, data=data)
    return resp.ok

def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r") as f:
            return json.load(f)
    return []

def save_history(history):
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f)

def scrape_offers():
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"
    }
    resp = requests.get(OLX_URL, headers=headers)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")
    offers = []

    # Znajdź wszystkie ogłoszenia na stronie
    # OLX zmienia strukturę, więc robimy to na podstawie aktualnej klasy linków
    for item in soup.select("div.offer-wrapper a.link"):
        title = item.get_text(strip=True)
        link = item['href']
        if link.startswith("/"):
            link = "https://www.olx.pl" + link
        offers.append({"title": title, "link": link})
    return offers

def main():
    print("Scraper startuje...")
    try:
        offers = scrape_offers()
        print(f"Znaleziono {len(offers)} ofert")
    except Exception as e:
        send_telegram_message(f"❌ Błąd scrapowania OLX: {e}")
        return

    history = load_history()
    history_links = {offer['link'] for offer in history}

    new_offers = [offer for offer in offers if offer['link'] not in history_links]

    if not new_offers:
        print("Brak nowych ofert.")
        return

    for offer in new_offers:
        msg = f"🏠 <b>{offer['title']}</b>\n{offer['link']}"
        success = send_telegram_message(msg)
        if success:
            print(f"Wysłano powiadomienie: {offer['title']}")
        else:
            print(f"Błąd wysyłania powiadomienia: {offer['title']}")

    # Uaktualniamy historię tylko po udanym wysłaniu
    save_history(offers)

if __name__ == "__main__":
    main()
