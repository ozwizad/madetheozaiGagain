import os, re, json, html, datetime, urllib.request, urllib.error
import xml.etree.ElementTree as ET

# (başlık, RSS adresi). Aynı başlığı kullanan kaynaklar tek bölümde toplanır.
FEEDS = [
    ("🖥 GPU / İşlemci", "https://www.techpowerup.com/rss/news"),
    ("🖥 GPU / İşlemci", "https://www.tomshardware.com/feeds/all"),
    ("🐧 Donanım & Linux", "https://www.phoronix.com/rss.php"),
    ("💹 Teknoloji ekonomisi", "https://webrazzi.com/feed/"),
    ("📊 Veri analizi", "https://www.kdnuggets.com/feed"),
]

MAX_NEWS = 6      # Yapay zekâ ile seçilecek haber sayısı
MAX_PHOTOS = 3    # Görselli gönderilecek haber sayısı

# 0 = Pazartesi
LESSONS = [
    # Pazartesi
    "SQL: SELECT ve WHERE\n"
    "SELECT, tablodan hangi sütunları görmek istediğini söyler. WHERE ise sadece şartı sağlayan satırları getirir.\n"
    "Örnek: SELECT ad, fiyat FROM urunler WHERE fiyat > 100; → fiyatı 100'ün üstündeki ürünlerin adı ve fiyatı.\n"
    "Not: Metin şartlarında tırnak kullanılır, örneğin WHERE sehir = 'Ankara'.",
    # Salı
    "Python/Pandas: df.head()\n"
    "Pandas'ta tablo verisine DataFrame (df) denir. df.head() ilk 5 satırı gösterir, böylece veriyi açtığında sütunlara ve değerlere hızlıca bakarsın.\n"
    "Yanına df.info() (sütun tipleri ve boş değerler) ve df.describe() (ortalama, en küçük/en büyük değer gibi özet istatistikler) eklemek iyi bir alışkanlıktır. Analize başlamadan önce veriyi tanımanın ilk adımı budur.",
    # Çarşamba
    "İstatistik: Ortalama ve medyan\n"
    "Ortalama, tüm değerlerin toplamının sayıya bölünmesidir. Medyan ise sıralanmış verinin ortadaki değeridir. Aykırı değer (diğerlerinden çok kopuk bir değer) varsa ortalama kolayca kayar, medyan ise çok az etkilenir.\n"
    "Örnek: maaşlar 20, 22, 25, 27 ve 300 (bin TL) olsun. Ortalama 78,8 çıkar, medyan 25. Gelir ve fiyat gibi çarpık dağılan verilerde medyan genelde daha gerçekçi tabloyu verir. Mülakatlarda bu farkı örnekle anlatabilmek artı puandır.",
    # Perşembe
    "Ekonomi: Enflasyon ve faiz\n"
    "Enflasyon, mal ve hizmet fiyatlarının genel olarak artması, yani paranın alım gücünün düşmesidir. Merkez Bankası faizi yükseltince borçlanma pahalanır, insanlar harcama yerine tasarrufa yönelir, talep azalır ve fiyat artışı yavaşlar.\n"
    "Faiz indirilince tersi olur: borçlanma ucuzlar, harcama ve büyüme canlanır ama enflasyon riski artar. Haberlerde 'faiz kararı' gördüğünde bu dengeyi düşün: enflasyonu düşürmek ile büyümeyi desteklemek arasındaki tercih.",
    # Cuma
    "SQL: GROUP BY\n"
    "GROUP BY, satırları bir sütuna göre gruplar ve her grup için toplam, ortalama, adet gibi hesaplar yapmanı sağlar.\n"
    "Örnek: SELECT sehir, SUM(satis) FROM siparisler GROUP BY sehir; → her şehrin toplam satışı.\n"
    "Sık kullanılan fonksiyonlar: COUNT (adet), SUM (toplam), AVG (ortalama), MIN, MAX. Grupları filtrelemek için WHERE yerine HAVING kullanılır.",
    # Cumartesi
    "Veri kaynağı: TCMB EVDS\n"
    "EVDS, Türkiye Cumhuriyet Merkez Bankası'nın Elektronik Veri Dağıtım Sistemi'dir. Enflasyon, döviz kurları, faiz ve kredi gibi binlerce ekonomik seriye ücretsiz erişim sağlar.\n"
    "Üye olunca seri ve tarih aralığı seçip Excel/CSV olarak indirebilir, API anahtarıyla Python'dan da çekebilirsin. Enflasyonun resmi kaynağı ise TÜİK'tir. Bu iki kaynağı bilmek, portföy projeleri için çok işe yarar.",
    # Pazar
    "Mini analiz tarifi: En çok satan 3 ürün\n"
    "Elinde ürün ve satış sütunları olan bir tablo varsa şu tek satır işi görür:\n"
    "df.groupby('urun')['satis'].sum().sort_values(ascending=False).head(3)\n"
    "groupby ürünleri gruplar, sum her ürünün toplam satışını hesaplar, sort_values büyükten küçüğe dizer, head(3) ilk üçü alır.\n"
    "Sonraki adım, bu üç ürünün neden öne çıktığına bakmaktır: fiyat, kampanya, mevsim ya da stok durumu gibi nedenler çoğu zaman cevabı verir.",
]

AYLAR = ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz",
         "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"]
GUNLER = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]

NS = {"media": "http://search.yahoo.com/mrss/",
      "content": "http://purl.org/rss/1.0/modules/content/"}


def esc(t):
    return html.escape(str(t or ""), quote=True)


def clean(t):
    t = re.sub(r"<[^>]+>", " ", html.unescape(t or ""))
    return re.sub(r"\s+", " ", t).strip()


def truncate(t, n):
    if len(t) <= n:
        return t
    return t[:n].rsplit(" ", 1)[0].rstrip(",.;:") + "…"


def find_image(item):
    for tag in ("media:content", "media:thumbnail"):
        for el in item.findall(tag, NS):
            u = el.get("url")
            if u and u.startswith("http") and (
                    el.get("medium") in (None, "image") or re.search(r"\.(jpe?g|png|webp)", u, re.I)):
                return u
    enc = item.find("enclosure")
    if enc is not None and (enc.get("type") or "").startswith("image") and enc.get("url"):
        return enc.get("url")
    raw = (item.findtext("content:encoded", "", NS) or "") + (item.findtext("description", "") or "")
    m = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', raw)
    if m and m.group(1).startswith("http"):
        return m.group(1)
    return None


def fetch_items(label, url, n=4):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=20) as r:
        root = ET.fromstring(r.read())
    out = []
    for item in root.findall(".//item")[:n]:
        title = clean(item.findtext("title", ""))
        link = (item.findtext("link", "") or "").strip()
        if not title or not link:
            continue
        out.append({
            "label": label,
            "title": title,
            "link": link,
            "desc": clean(item.findtext("description", "")),
            "image": find_image(item),
            "summary": "",
            "term": "",
        })
    return out


def call_llm(prompt):
    """GEMINI_API_KEY varsa Gemini, yoksa ANTHROPIC_API_KEY varsa Claude kullanılır."""
    gem = os.environ.get("GEMINI_API_KEY")
    if gem:
        model = os.environ.get("GEMINI_MODEL") or "gemini-3.5-flash-lite"
        body = json.dumps({
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"responseMimeType": "application/json"},
        }).encode()
        req = urllib.request.Request(
            f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
            data=body, headers={"x-goog-api-key": gem, "content-type": "application/json"})
        with urllib.request.urlopen(req, timeout=90) as r:
            return json.load(r)["candidates"][0]["content"]["parts"][0]["text"]
    key = os.environ.get("ANTHROPIC_API_KEY")
    if key:
        body = json.dumps({
            "model": "claude-haiku-5-5",
            "max_tokens": 1500,
            "messages": [{"role": "user", "content": prompt}],
        }).encode()
        req = urllib.request.Request("https://api.anthropic.com/v1/messages", data=body, headers={
            "x-api-key": key, "anthropic-version": "2023-06-01", "content-type": "application/json"})
        with urllib.request.urlopen(req, timeout=90) as r:
            return json.load(r)["content"][0]["text"]
    return None


def pick_with_ai(items):
    if not items or not (os.environ.get("GEMINI_API_KEY") or os.environ.get("ANTHROPIC_API_KEY")):
        return None
    listing = "\n".join(
        f"{i} | {it['label']} | {it['title']} | {truncate(it['desc'], 300)}"
        for i, it in enumerate(items))
    prompt = (
        f"Aşağıda numaralı haberler var (numara | kategori | başlık | açıklama). "
        f"Veri analisti olmak isteyen, teknoloji ve ekonomiyi yeni öğrenen bir okur için "
        f"en önemli {MAX_NEWS} haberi seç, kategoriler dengeli olsun. "
        f"Her biri için Türkçe, sade bir başlık ve 1-2 cümlelik özet yaz. Özetlerde reklam, "
        f"tekrar ve gereksiz detay olmasın. Anlaşılması zor bir teknik terim varsa 'terim' alanına "
        f"'Terim: kısa açıklama' biçiminde ekle, yoksa boş bırak.\n"
        f"Sadece şu biçimde bir JSON listesi döndür, başka hiçbir şey yazma:\n"
        f'[{{"id": 0, "baslik": "...", "ozet": "...", "terim": ""}}]\n\n{listing}')
    try:
        text = call_llm(prompt)
        if not text:
            return None
        data = json.loads(text[text.index("["): text.rindex("]") + 1])
        out = []
        for d in data:
            it = dict(items[int(d["id"])])
            it["title"] = clean(d.get("baslik") or it["title"])
            it["summary"] = clean(d.get("ozet") or "")
            it["term"] = clean(d.get("terim") or "")
            out.append(it)
        return out or None
    except Exception as e:
        print("Özetleme başarısız, ham liste kullanılacak:", e)
        return None


def fallback_pick(items):
    seen, out = {}, []
    for it in items:
        if seen.get(it["link"]):
            continue
        seen[it["link"]] = True
        if sum(1 for o in out if o["label"] == it["label"]) >= 2:
            continue
        it = dict(it)
        it["summary"] = truncate(it["desc"], 160)
        out.append(it)
    return out


def render(it, summary_len=400):
    s = f"<b>{esc(it['title'])}</b>"
    if it["summary"]:
        s += f"\n{esc(truncate(it['summary'], summary_len))}"
    if it["term"]:
        s += f"\n💡 <i>{esc(truncate(it['term'], 250))}</i>"
    s += f'\n<a href="{esc(it["link"])}">Habere git →</a>'
    return s


def get_chat_id(token):
    # TELEGRAM_CHAT_ID verilmediyse, bota en son mesaj atan kişinin id'sini bul
    with urllib.request.urlopen(f"https://api.telegram.org/bot{token}/getUpdates", timeout=20) as r:
        updates = json.load(r).get("result", [])
    for u in reversed(updates):
        chat = (u.get("message") or {}).get("chat")
        if chat:
            return chat["id"]
    raise SystemExit("Chat id bulunamadı: TELEGRAM_CHAT_ID secret'ını ekle.")


class Telegram:
    def __init__(self):
        self.token = os.environ["TELEGRAM_TOKEN"]
        self.chat_id = os.environ.get("TELEGRAM_CHAT_ID") or get_chat_id(self.token)

    def call(self, method, payload):
        payload = dict(payload, chat_id=self.chat_id)
        req = urllib.request.Request(
            f"https://api.telegram.org/bot{self.token}/{method}",
            data=json.dumps(payload).encode(),
            headers={"content-type": "application/json"})
        try:
            urllib.request.urlopen(req, timeout=30)
            return True
        except urllib.error.HTTPError as e:
            print(method, "hata:", e.code, e.read().decode(errors="ignore")[:300])
        except Exception as e:
            print(method, "hata:", e)
        return False

    def text(self, t):
        return self.call("sendMessage", {"text": t, "parse_mode": "HTML",
                                         "disable_web_page_preview": True})

    def photo(self, url, caption):
        return self.call("sendPhoto", {"photo": url, "caption": caption, "parse_mode": "HTML"})


def chunk_sections(sections, limit=3800):
    msgs, cur = [], ""
    for sec in sections:
        if cur and len(cur) + len(sec) + 2 > limit:
            msgs.append(cur)
            cur = ""
        cur = f"{cur}\n\n{sec}" if cur else sec
    if cur:
        msgs.append(cur)
    return msgs


def main():
    tg = Telegram()
    today = datetime.date.today()

    items = []
    for label, url in FEEDS:
        try:
            items += fetch_items(label, url)
        except Exception as e:
            print(f"{url} okunamadı: {e}")
    picked = pick_with_ai(items) or fallback_pick(items)

    header = (f"☀️ <b>Günaydın!</b>\n"
              f"{today.day} {AYLAR[today.month - 1]} {today.year}, {GUNLER[today.weekday()]}")
    if not tg.text(header):
        raise SystemExit(1)

    if not picked:
        tg.text("Bugün haber kaynaklarına ulaşılamadı. Yarın tekrar denerim.")
    else:
        # Görseli olan ilk haberler fotoğraf olarak gider, geri kalanlar metin olarak.
        rest, photos_sent = [], 0
        for it in picked:
            if it["image"] and photos_sent < MAX_PHOTOS:
                cap = render(it)
                if len(cap) > 1000:
                    cap = render(it, summary_len=250)
                if tg.photo(it["image"], cap):
                    photos_sent += 1
                    continue
            rest.append(it)

        sections, order = [], []
        for it in rest:
            if it["label"] not in order:
                order.append(it["label"])
        for label in order:
            body = "\n\n".join(render(it) for it in rest if it["label"] == label)
            sections.append(f"<b>{esc(label)}</b>\n\n{body}")
        for msg in chunk_sections(sections):
            tg.text(msg)

    lesson = LESSONS[today.weekday()]
    tg.text(f"📚 <b>Bugünün dersi</b>\n\n{esc(lesson)}")


if __name__ == "__main__":
    main()
