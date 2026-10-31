import os, re, sys, json, html, datetime, urllib.request, urllib.error
import xml.etree.ElementTree as ET

# ---------- Haber kaynakları ----------
FEEDS = [
    ("🖥 GPU / İşlemci", "https://www.techpowerup.com/rss/news"),
    ("🖥 GPU / İşlemci", "https://www.tomshardware.com/feeds/all"),
    ("🐧 Donanım & Linux", "https://www.phoronix.com/rss.php"),
    ("💹 Teknoloji ekonomisi", "https://webrazzi.com/feed/"),
    ("📊 Veri analizi", "https://www.kdnuggets.com/feed"),
    ("🤖 AI", "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml"),
    ("🤖 AI", "https://www.technologyreview.com/topic/artificial-intelligence/feed/"),
    ("🤖 AI", "https://blog.google/innovation-and-ai/technology/ai/rss/"),
    ("🤖 AI", "https://openai.com/news/rss.xml"),
    ("🤖 AI", "https://importai.substack.com/feed"),
]
MAX_NEWS = 6
MAX_PHOTOS = 3

# ---------- Sabah dersi (0 = Pazartesi) ----------
LESSONS = [
    "SQL: SELECT ve WHERE\n"
    "SELECT, hangi sütunları görmek istediğini söyler. WHERE sadece şartı sağlayan satırları getirir.\n"
    "Örnek: SELECT ad, fiyat FROM urunler WHERE fiyat > 100; → fiyatı 100'ün üstündeki ürünler.\n"
    "Metin şartlarında tırnak kullanılır: WHERE sehir = 'Ankara'.",
    "Python/Pandas: df.head()\n"
    "df.head() ilk 5 satırı gösterir. Yanına df.info() (sütun tipleri, boş değerler) ve df.describe() "
    "(ortalama, min, max) eklemek iyi bir alışkanlıktır. Analize başlamadan önce veriyi tanı.",
    "İstatistik: Ortalama ve medyan\n"
    "Maaşlar 20, 22, 25, 27 ve 300 (bin TL) olsun. Ortalama 78,8, medyan 25 çıkar. Aykırı değer ortalamayı "
    "kaydırır, medyan ise etkilenmez. Gelir ve fiyat gibi çarpık veride medyan genelde daha gerçekçidir.",
    "Ekonomi: Enflasyon ve faiz\n"
    "Merkez Bankası faizi yükseltince borçlanma pahalanır, talep düşer, enflasyon yavaşlar. Faiz indirilince "
    "büyüme canlanır ama enflasyon riski artar. 'Faiz kararı' haberinde bu dengeyi düşün.",
    "SQL: GROUP BY\n"
    "GROUP BY satırları bir sütuna göre gruplar, her grup için toplam ve ortalama alınır.\n"
    "Örnek: SELECT sehir, SUM(satis) FROM siparisler GROUP BY sehir; → şehir bazında toplam satış.\n"
    "Grupları filtrelemek için WHERE yerine HAVING kullanılır.",
    "Veri kaynağı: TCMB EVDS\n"
    "Merkez Bankası'nın EVDS sisteminde enflasyon, döviz, faiz ve kredi serileri ücretsiz. Excel/CSV olarak "
    "indirebilir ya da API anahtarıyla Python'dan çekebilirsin. Resmi enflasyon verisi için TÜİK'e de bak.",
    "Mini analiz: En çok satan 3 ürün\n"
    "df.groupby('urun')['satis'].sum().sort_values(ascending=False).head(3)\n"
    "Sonra sor: bu ürünler neden öne çıktı? Fiyat, kampanya, mevsim ya da stok çoğu zaman cevabı verir.",
]

# ---------- Genel kültür (her gün öğlen) ----------
GENEL_KULTUR = [
    "Bileşik faiz\nYüzde 10 getiriyle 100 TL, 10 yılda yaklaşık 259 TL olur. Her yıl faiz, bir önceki yılın "
    "sonundaki tutar üzerinden hesaplanır. Kredi kartı borcu da aynı mantıkla büyür; asgari ödemede kalmak pahalıdır.",
    "Hayatta kalanlar yanlılığı\nII. Dünya Savaşı'nda uçaklara zırh eklenecekti. Abraham Wald, kurşun izi olan "
    "bölgelere değil, izi olmayan bölgelere zırh konmasını önerdi, çünkü dönemeyen uçaklar görünmüyordu. "
    "İş yerinde 'sadece başarılı müşterileri analiz ediyoruz' hatası aynı yanılgıdır.",
    "Netflix iş modeli\nAbonelik gelirinde üç metrik birlikte okunur: kullanıcı sayısı, kullanıcı başına gelir "
    "(ARPU) ve kayıp oranı (churn). Sadece kullanıcı sayısına bakmak şirketin sağlığını göstermez.",
    "Enflasyon ve maaş\nEnflasyon yüzde 40, maaş zammı yüzde 30 ise gerçek alım gücü düşer. 'Maaş arttı' haberi tek "
    "başına bir şey söylemez. Doğru soru: zam enflasyonun üstünde mi altında mı?",
    "Korelasyon, nedensellik değildir\nDondurma satışı ve boğulma vakaları yazın birlikte artar. İkisini "
    "de sıcak hava etkiler, birbirlerine neden olmazlar. Bu ayrımı yapamayan rapor yanlış karar verdirir.",
    "Simpson paradoksu\nBir üniversitenin genel kabul oranı kadınlar için düşük görünebilir, ama her bölümde "
    "kadınların oranı yüksek olabilir. Sebep, kadınların daha rekabetçi bölümlere başvurmasıdır. Toplamda "
    "bakmadan önce gruplara ayırmak gerekir.",
    "Goodhart yasası\n'Bir ölçü hedef hâline gelince iyi bir ölçü olmaktan çıkar.' Çağrı merkezinde süreyi "
    "kısaltma hedefi, müşteri memnuniyetini düşürebilir. Hedef koyarken yan etkisini de ölç.",
    "Fırsat maliyeti\nBir şeye ayırdığın zaman ya da parayla vazgeçtiğin en iyi alternatifin değeridir. "
    "Bir kursa yatırım yaparken sadece ücretine değil, o saatte yapabileceğin işe de bak.",
    "Moore yasası nedir, değil midir?\nTransistör sayısının yaklaşık her iki yılda bir iki katına çıkması bir "
    "gözlemdir, fizik yasası değildir. GPU haberlerinde 'hız arttı' derken bu gözlemin hâlâ geçerli olup "
    "olmadığına bakmak iyi bir alışkanlıktır.",
    "Reel kur\nNominal kur, doların TL karşılığıdır. Reel kur, bunu iki ülkenin enflasyon farkına göre düzeltir. "
    "Dolar bir yıl sabit kalsa bile Türkiye'de fiyatlar arttıysa reel olarak ihracatçı kazancı değişir.",
    "KVKK ve kişisel veri\nKişisel veri, kimliği belirli ya da belirlenebilir bir kişiye ait her türlü bilgidir. "
    "Bir analiz tablosunda isim yerine kullanıcı kodu olsa bile, o kodu kimlikle eşleştirebiliyorsan hâlâ kişisel "
    "veridir.",
    "Paydaş (stakeholder)\nBir analizden etkilenen ya da karar veren herkestir: yönetici, satış ekibi, müşteri. "
    "İyi bir analist, her paydaşın hangi soruya cevap aradığını önce sorar, sonra veriye bakar.",
    "Kâr ve nakit akışı farkı\nBir şirket kârlı görünebilir ama nakdi bitebilir. Satılan ürünün parası henüz "
    "tahsil edilmemişse kâr defterde vardır, cüzdanda yoktur. Şirket analizinde ikisine birlikte bak.",
    "Ücretsiz ürünlerin modeli\nGoogle Arama ücretsiz, ama asıl müşteri reklam veren şirketlerdir. Kullanıcı, "
    "ürünün kendisi değil, dikkatini satan bir kaynaktır. Bir ürün bedavaysa, parasını kimin ödediğini sor.",
]

# ---------- AI ve araç terimleri (Salı, Cuma) ----------
TERIMLER = [
    "MCP (Model Context Protocol)\nAnthropic'in 2024'te açık kaynak yaptığı standart. Yapay zekâ uygulamasını dış "
    "araç ve verilere tek bir ortak dille bağlar. Her servis için ayrı entegrasyon yerine bir kez MCP sunucusu yazılır.",
    "RAG (Retrieval-Augmented Generation)\nModelin cevap vermeden önce ilgili belgeleri arayıp bağlama eklemesi. "
    "Eğitim verisinde olmayan şirket dokümanlarına cevap verebilmenin en yaygın yolu. Uydurmayı azaltır, ama bitirmez.",
    "GEO (Generative Engine Optimization)\nSEO'nun yapay zekâ arama cevaplarına uyarlanmış hali. Amaç, ChatGPT, "
    "Gemini veya Claude gibi araçların cevabında kaynak olarak gösterilmek. Net, kaynaklı, yapılandırılmış içerik öne çıkar.",
    "Agent (yapay zekâ ajanı)\nBir hedefe adım adım çalışan sistem: araç seçer, komut çalıştırır, sonucu okur, "
    "sonraki adıma karar verir. Her adımın hatası birikebilir, bu yüzden çıktıyı doğrulamak hâlâ insanın işi.",
    "Context window (bağlam penceresi)\nModelin tek seferde işleyebildiği metin miktarı, token cinsinden. "
    "Büyük bir veri dosyasını tek seferde yapıştırmak bu sınıra çarpabilir. Veriyi özetle ya da kodla işle.",
    "Token\nModelin metni işlediği parçalar. İngilizcede kabaca 4 karakter bir token. Türkçe ekli olduğu için aynı "
    "cümle daha fazla token tutar, yani maliyeti artar. Çıktı token'ı genelde girdiden pahalıdır.",
    "Prompt caching\nAynı başlangıç metni (talimatlar, uzun doküman) tekrar gönderiliyorsa önbellekten daha ucuza "
    "işlenebilir. Pratik kural: sabit talimatları başa, değişen soruyu sona koy.",
    "Skill\nBelirli bir iş için hazırlanmış talimat paketi. Genelde adı, ne zaman kullanılacağı ve adımları yazan "
    "bir SKILL.md dosyası içerir. Model sadece görev uyduğunda yükler. Tekrarlayan rapor işleri için idealdir.",
    "Tool use (araç kullanımı)\nModel dosya okuyamaz ya da veritabanına bağlanamaz. Uygulamanın tanımladığı aracı "
    "parametrelerle çağırır, uygulama çalıştırıp sonucu modele verir. Aracın açıklaması kötü yazılırsa model yanlış "
    "aracı seçer. MCP sunucuları bu araçları standart şekilde sağlar.",
]

# ---------- Ücretsiz araç önerisi (Çarşamba) ----------
ARACLAR = [
    "Looker Studio (Google)\nVeri kaynağı bağla, grafik ve tablolardan dashboard kur. Üçüncü taraf kaynaklara göre "
    "ücretsiz ve sınırsız rapor/kullanıcı sunuyor. Veri analisti portföyü için ilk denenecek araç.\n"
    "Güncel limitleri kendi sayfasından kontrol et.",
    "DuckDB\nSunucu gerektirmeyen, MIT lisanslı bir veritabanı. CSV dosyasının üzerinde doğrudan SQL çalıştırırsın:\n"
    "duckdb -c \"SELECT sehir, SUM(satis) FROM 'satis.csv' GROUP BY sehir\"\n"
    "SQL öğrenirken kurulum derdi olmadan pratik yapmak için ideal.",
]

NS = {"media": "http://search.yahoo.com/mrss/",
      "content": "http://purl.org/rss/1.0/modules/content/"}
AYLAR = ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz",
         "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"]
GUNLER = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]


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
        out.append({"label": label, "title": title, "link": link,
                    "desc": clean(item.findtext("description", "")),
                    "image": find_image(item), "summary": "", "term": ""})
    return out


def call_llm(prompt):
    """GEMINI_API_KEY varsa Gemini, yoksa ANTHROPIC_API_KEY varsa Claude."""
    gem = os.environ.get("GEMINI_API_KEY")
    if gem:
        model = os.environ.get("GEMINI_MODEL") or "gemini-3.5-flash-lite"
        body = json.dumps({"contents": [{"parts": [{"text": prompt}]}],
                           "generationConfig": {"responseMimeType": "application/json"}}).encode()
        req = urllib.request.Request(
            f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
            data=body, headers={"x-goog-api-key": gem, "content-type": "application/json"})
        with urllib.request.urlopen(req, timeout=90) as r:
            return json.load(r)["candidates"][0]["content"]["parts"][0]["text"]
    key = os.environ.get("ANTHROPIC_API_KEY")
    if key:
        body = json.dumps({"model": "claude-haiku-5-5", "max_tokens": 1500,
                           "messages": [{"role": "user", "content": prompt}]}).encode()
        req = urllib.request.Request("https://api.anthropic.com/v1/messages", data=body, headers={
            "x-api-key": key, "anthropic-version": "2023-06-01", "content-type": "application/json"})
        with urllib.request.urlopen(req, timeout=90) as r:
            return json.load(r)["content"][0]["text"]
    return None


def pick_with_ai(items):
    if not items or not (os.environ.get("GEMINI_API_KEY") or os.environ.get("ANTHROPIC_API_KEY")):
        return None
    listing = "\n".join(f"{i} | {it['label']} | {it['title']} | {truncate(it['desc'], 300)}"
                        for i, it in enumerate(items))
    prompt = (
        f"Below are numbered news items (number | category | title | description). "
        f"Pick the {MAX_NEWS} most important ones for a reader who is learning about tech, "
        f"AI, economics and data analysis. Keep the categories balanced. "
        f"For each, write a short clear headline and a 1-2 sentence summary in English. "
        f"No ads, repetition or unnecessary detail. If a technical term needs explaining, "
        f"put a short 'Term: explanation' in the 'terim' field, otherwise leave it empty.\n"
        f"Return only a JSON list in this format, nothing else:\n"
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
    s += f'\n<a href="{esc(it["link"])}">Read more →</a>'
    return s


def get_chat_id(token):
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
        req = urllib.request.Request(f"https://api.telegram.org/bot{self.token}/{method}",
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
        return self.call("sendMessage", {"text": t, "parse_mode": "HTML", "disable_web_page_preview": True})

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


def split_card(card):
    """'Başlık\\nGövde' → (başlık, gövde)"""
    head, _, body = card.partition("\n")
    return head, body


def morning(tg, today):
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
        tg.text("Bugün haber kaynaklarına ulaşılamadı.")
    else:
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
        order = []
        for it in rest:
            if it["label"] not in order:
                order.append(it["label"])
        sections = [f"<b>{esc(label)}</b>\n\n" + "\n\n".join(render(it) for it in rest if it["label"] == label)
                    for label in order]
        for msg in chunk_sections(sections):
            tg.text(msg)

    lesson = LESSONS[today.weekday()]
    extra = [f"📚 <b>Bugünün dersi</b>\n\n{esc(lesson)}"] + extra_cards(today)
    for msg in chunk_sections(extra):
        tg.text(msg)


def extra_cards(today):
    """Sabah mesajının sonuna eklenen genel kültür, terim ve araç kartları (HTML metin listesi)."""
    out = []
    gk = GENEL_KULTUR[today.toordinal() % len(GENEL_KULTUR)]
    head, body = split_card(gk)
    out.append(f"🧠 <b>Genel kültür</b>\n\n<b>{esc(head)}</b>\n{esc(body)}")

    wd = today.weekday()
    if wd in (1, 4):  # Salı, Cuma
        t = TERIMLER[today.toordinal() % len(TERIMLER)]
        head, body = split_card(t)
        out.append(f"🤖 <b>Terim</b>\n\n<b>{esc(head)}</b>\n{esc(body)}")
    if wd == 2:  # Çarşamba
        a = ARACLAR[(today.toordinal() // 7) % len(ARACLAR)]
        head, body = split_card(a)
        out.append(f"🧰 <b>Bu hafta denenecek araç</b>\n\n<b>{esc(head)}</b>\n{esc(body)}\n\n"
                   f"<i>Ücretsiz katman şartları değişebilir, kullanmadan önce güncel sayfayı kontrol et.</i>")
    return out


def main():
    tg = Telegram()
    morning(tg, datetime.date.today())


if __name__ == "__main__":
    main()
