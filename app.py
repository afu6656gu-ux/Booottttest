from flask import Flask, request, redirect, jsonify
import telebot
import requests
import re

app = Flask(__name__)

TOKEN = "8644563315:AAGShENEmjbM9IeEPbGmJWJOh7RjPwGGdFw"
VERCEL_APP_URL = "https://porjectnew.vercel.app"
UQLOAD_DOMAIN = "uqload.vc"
COMMON_USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'

bot = telebot.TeleBot(TOKEN, threaded=False)

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

@app.route('/api/webhook', methods=['POST'])
def telegram_webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return '', 200
    return 'Forbidden', 403

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "👋 أهلاً بك! أرسل لي أي رابط مباشر (.mp4) أو رابط Uqload وسأحوله لك لرابط ثابت.")

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    text = message.text
    
    # 1. فحص إذا كان الرابط مباشر ينتهي بـ .mp4 أو يحتوي على صيغة فيديو مباشرة
    direct_match = re.search(r'(https?://[^\s]+\.mp4[^\s]*)', text, re.IGNORECASE)
    # 2. فحص إذا كان رابط Uqload
    uqload_match = re.search(r'uqload\.(?:co|com|vc)/(?:embed-)?([a-zA-Z0-9]+)', text)
    
    if direct_match:
        # إذا كان رابط mp4 مباشر، نقوم بترميزه أو حفظه لنحوله لرابط ثابت عبر سيرفرنا
        raw_url = direct_match.group(1)
        # ننشئ مسار مشفر أو مسار يعيد التوجيه للرابط المباشر
        # لتبسيطها، سنقوم بتمرير الرابط المباشر عبر الـ API الخاص بنا
        import urllib.parse
        encoded_url = urllib.parse.quote(raw_url, safe='')
        static_link = f"{VERCEL_APP_URL}/direct?url={encoded_url}"
        
        reply_text = f"✅ **تم إنشاء الرابط الثابت للرابط المباشر!**\n\n🔗 الرابط:\n`{static_link}`"
        bot.reply_to(message, reply_text, parse_mode="Markdown")
        
    elif uqload_match:
        video_code = uqload_match.group(1)
        static_link = f"{VERCEL_APP_URL}/play/{video_code}"
        reply_text = f"✅ **تم إنشاء الرابط الثابت لـ Uqload!**\n\n🔗 الرابط:\n`{static_link}`"
        bot.reply_to(message, reply_text, parse_mode="Markdown")
    else:
        bot.reply_to(message, "⚠️ عذراً، يرجى إرسال رابط مباشر ينتهي بـ .mp4 أو رابط Uqload صحيح.")

# مسار خاص بالروابط المباشرة (يقوم بإعادة التوجيه فورا للرابط الأصلي)
@app.route('/direct')
def direct_proxy():
    target_url = request.args.get('url')
    if target_url:
        return redirect(target_url, code=302)
    return jsonify({"error": "No url provided"}), 400

@app.route('/play/<video_code>')
def play_video(video_code):
    direct_link = get_uqload_direct_link(video_code)
    if direct_link:
        return redirect(direct_link, code=302)
    return jsonify({"error": "Failed to fetch direct link"}), 404

@app.route('/')
def index():
    app_name = "Arab Fleex Static Link API"
    return f"✅ {app_name} is running perfectly!"
