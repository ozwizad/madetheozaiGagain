import os, json, datetime, urllib.request
import xml.etree.ElementTree as ET

FEEDS = [
    ("GPU/CPU", "https://www.techpowerup.com/rss/news"),
    ("Donanım", "https://www.tomshardware.com/feeds/all"),
    ("Linux/CPU", "https://www.phoronix.com/rss.php"),
    ("Teknoloji ekonomisi", "https://webrazzi.com/feed/"),
    ("Veri", "https://www.kdnuggets.com/feed"),
]

# 0 = Pazartesi
LESSONS = [
    "SQL: SELECT ve WHERE ile tablodan satır seçmek. Örnek: SELECT ad FROM urunler WHERE fiyat > 100;",
    "Python/Pandas: df.head() ile veriye ilk bakış. Veriyi açmadan analiz yapma.",
    "Mülakat sorusu: 'Ortalama mı medyan mı?' Aykırı değer varsa neden medyan daha sağlıklı?",
    "Ekonomi: Enflasyon nedir, faiz artışı neden enflasyonu düşürmeye çalışır?",
    "SQL: GROUP BY ile kategori bazında toplam almak. Örnek: SELECT sehir, SUM(satis) FROM siparisler GROUP BY sehir;",
    "Veri kaynağı: TCMB EVDS'te enflasyon ve döviz serilerini nasıl bulursun?",
    "Hafta sonu görevi: Bir veri setinde en yüksek 3 satış kalemini bul ve nedenini düşün.",
]


def fetch_items(url, n=3):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=20) as r:
        root = ET.fromstring(r.read())
    out = []
    for item in root.findall(".//item")[:n]:
        out.append(f"- {item.findtext('title', '')}: {item.findtext('link', '')}")
    return out


def summarize(text):
    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        return text
    body = json.dumps({
        "model": "claude-haiku-5-5",
        "max_tokens": 800,
        "messages": [{"role": "user", "content":
            "Aşağıdaki haber başlıklarından en önemli 5 tanesini seç. "
            "Her biri için Türkçe 1-2 cümle yaz, teknik terimi kısaca açıkla.\n\n" + text}],
    }).encode()
    req = urllib.request.Request("https://api.anthropic.com/v1/messages", data=body, headers={
        "x-api-key": key, "anthropic-version": "2023-06-01", "content-type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.load(r)["content"][0]["text"]
    except Exception:
        return text


def get_chat_id(token):
    # TELEGRAM_CHAT_ID verilmediyse, bota en son mesaj atan kişinin id'sini bul
    with urllib.request.urlopen(f"https://api.telegram.org/bot{token}/getUpdates", timeout=20) as r:
        updates = json.load(r).get("result", [])
    for u in reversed(updates):
        chat = (u.get("message") or {}).get("chat")
        if chat:
            return chat["id"]
    raise SystemExit("Chat id bulunamadı: önce Telegram'dan botuna bir mesaj at.")


def send(text):
    token = os.environ["TELEGRAM_TOKEN"]
    chat_id = os.environ.get("TELEGRAM_CHAT_ID") or get_chat_id(token)
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    body = json.dumps({"chat_id": chat_id, "text": text[:4000],
                       "disable_web_page_preview": True}).encode()
    urllib.request.urlopen(urllib.request.Request(
        url, data=body, headers={"content-type": "application/json"}), timeout=20)


def main():
    today = datetime.date.today()
    lines = []
    for name, url in FEEDS:
        lines.append(f"[{name}]")
        try:
            lines += fetch_items(url)
        except Exception as e:
            lines.append(f"okunamadı: {e}")
    news = summarize("\n".join(lines))
    lesson = LESSONS[today.weekday()]
    send(f"Günaydın! {today:%d.%m.%Y}\n\nHABERLER\n{news}\n\nBUGÜNÜN DERSİ\n{lesson}")


if __name__ == "__main__":
    main()
