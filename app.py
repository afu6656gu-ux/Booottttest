from flask import Flask, request, redirect, jsonify
import telebot
import requests
import re

app = Flask(__name__)

# بياناتك
TOKEN = "8644563315:AAGShENEmjbM9IeEPbGmJWJOh7RjPwGGdFw"
VERCEL_APP_URL = "https://porjectnew-m321rfwlh-chayshd39-5241s-projects.vercel.app"
UQLOAD_DOMAIN = "uqload.vc"
COMMON_USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'

bot = telebot.TeleBot(TOKEN, threaded=False)

# دالة فك حماية Uqload
def get_uqload_direct_link(video_code):
    try:
        url = f"https://{UQLOAD_DOMAIN}/embed-{video_code}.html"
        headers = {'User-Agent': COMMON_USER_AGENT, 'Referer': f'https://{UQLOAD_DOMAIN}/'}
        r = requests.get(url, headers=headers, timeout=15, verify=False)
        
        packed = re.search(r"eval\(function\(p,a,c,k,e,d\)\{.*?\}\('(.*?)',(\d+),(\d+),'(.*?)'\.split\('\|'\)\)\)", r.text, re.DOTALL)
        if not packed:
            return None
            
        p, a, c, k = packed.group(1), int(packed.group(2)), int(packed.group(3)), packed.group(4).split('|')
        
        def replace(m):
            word = m.group(0)
            try:
                n = int(word, a)
                return k[n] if n < len(k) and k[n] else word
            except Exception:
                return word
                
        decoded = re.sub(r'\b\w+\b', replace, p)
        urls = re.findall(r'https?://[^\\"\' ]+\.m3u8[^\\"\' ]*', decoded)
        
        if urls:
            return urls[0]
        return None
    except Exception:
        return None

# مسار استقبال رسائل التيليجرام (Webhook)
@app.route('/api/webhook', methods=['POST'])
def telegram_webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return '', 200
    return 'Forbidden', 403

# معالجة أوامر ورسائل البوت
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "👋 أهلاً بك! أرسل لي أي رابط من Uqload وسأقوم بتحويله فوراً إلى رابط تشغيل مباشر وثابت.")

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    text = message.text
    match = re.search(r'uqload\.(?:co|com|vc)/(?:embed-)?([a-zA-Z0-9]+)', text)
    
    if match:
        video_code = match.group(1)
        static_link = f"{VERCEL_APP_URL}/play/{video_code}"
        reply_text = f"✅ **تم إنشاء الرابط الثابت بنجاح!**\n\n🔗 الرابط:\n`{static_link}`\n\n💡 (هذا الرابط لن يتغير ويمكنك استخدامه في موقعك أو مشغلك مباشرة)"
        bot.reply_to(message, reply_text, parse_mode="Markdown")
    else:
        bot.reply_to(message, "⚠️ عذراً، لم أتمكن من العثور على كود Uqload صحيح في رسالتك.")

# مسار تشغيل الفيديو (فك الحماية وإعادة التوجيه)
@app.route('/play/<video_code>')
def play_video(video_code):
    direct_link = get_uqload_direct_link(video_code)
    if direct_link:
        return redirect(direct_link, code=302)
    return jsonify({"error": "Failed to fetch direct link or video not found"}), 404

# صفحة رئيسية للتأكد من عمل السيرفر
@app.route('/')
def index():
    return "Server is Running on Vercel 🚀"
