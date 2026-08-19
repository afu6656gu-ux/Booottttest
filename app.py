from flask import Flask, request, redirect, jsonify
import telebot
import requests
import re
import urllib.parse

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
        urls = re.findall(r'https?://[^\\"\' ]+\.(?:m3u8|mp4|mkv)[^\\"\' ]*', decoded, re.IGNORECASE)
        
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
    bot.reply_to(message, "👋 أهلاً بك! أرسل لي أي رابط وسأعطيك رابطاً ثابتاً ينتهي بـ mp4/mkv لوحة التحكم.")

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    text = message.text
    
    direct_match = re.search(r'(https?://[^\s]+\.(?:mp4|mkv|avi|mov)[^\s]*)', text, re.IGNORECASE)
    uqload_match = re.search(r'uqload\.(?:co|com|vc)/(?:embed-)?([a-zA-Z0-9]+)', text)
    
    if direct_match:
        raw_url = direct_match.group(1)
        # استخراج امتداد الملف الحقيقي (mp4 أو mkv) عشان نحطه في آخره
        ext = "mp4"
        if ".mkv" in raw_url.lower():
            ext = "mkv"
            
        encoded_url = urllib.parse.quote(raw_url, safe='')
        # الرابط دلوقتي هينتهي بـ .mp4 أو .mkv شكلاً وموضوعاً!
        static_link = f"{VERCEL_APP_URL}/stream/video.{ext}?url={encoded_url}"
        
        reply_text = f"✅ **الرابط الثابت (جاهز للوحة التحكم):**\n\n🔗 الرابط:\n`{static_link}`"
        bot.reply_to(message, reply_text, parse_mode="Markdown")
        
    elif uqload_match:
        video_code = uqload_match.group(1)
        # حتى Uqload هنخليه ينتهي بـ .mp4 في الرابط الثابت
        static_link = f"{VERCEL_APP_URL}/stream/{video_code}.mp4"
        
        reply_text = f"✅ **الرابط الثابت (جاهز للوحة التحكم):**\n\n🔗 الرابط:\n`{static_link}`"
        bot.reply_to(message, reply_text, parse_mode="Markdown")
    else:
        bot.reply_to(message, "⚠️ عذراً، أرسل رابط فيديو صحيح.")

# مسار الـ Stream الجديد اللي بيخليه ينتهي بـ mp4/mkv غصباً عن الكل
@app.route('/stream/<path:filename>')
def stream_proxy(filename):
    target_url = request.args.get('url')
    
    # لو جاي من Uqload (مش حاطين url في الـ query)
    if not target_url:
        video_code = filename.split('.')[0] # بنسحب الكود من اسم الملف زي m4lcmv5kcqs6
        target_url = get_uqload_direct_link(video_code)
        
    if target_url:
        return redirect(target_url, code=302)
        
    return jsonify({"error": "Link expired or invalid"}), 404

@app.route('/')
def index():
    return "✅ Arab Fleex Static Link API is running perfectly!"
