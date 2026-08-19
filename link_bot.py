import telebot
import re

# توكن البوت الخاص بك
TOKEN = "8644563315:AAGShENEmjbM9IeEPbGmJWJOh7RjPwGGdFw"

# رابط Vercel الخاص بك
VERCEL_APP_URL = "https://porjectnew-m321rfwlh-chayshd39-5241s-projects.vercel.app"

bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "👋 أهلاً بك! ابعتلي أي رابط من Uqload وسأقوم بتحويله لرابط مباشر ثابت.")

@bot.message_handler(func=lambda message: True)
def generate_static_link(message):
    text = message.text
    # استخراج كود الفيديو من رابط Uqload
    match = re.search(r'uqload\.(?:co|com|vc)/(?:embed-)?([a-zA-Z0-9]+)', text)
    
    if match:
        video_code = match.group(1)
        # تكوين الرابط الثابت بتاع Vercel
        static_link = f"{VERCEL_APP_URL}/play/{video_code}"
        
        reply_text = f"✅ **تم إنشاء الرابط الثابت بنجاح!**\n\n🔗 الرابط:\n`{static_link}`\n\n💡 (هذا الرابط لن يتغير ويمكنك استخدامه في موقعك)"
        bot.reply_to(message, reply_text, parse_mode="Markdown")
    else:
        bot.reply_to(message, "⚠️ عذراً، لم أتمكن من العثور على كود Uqload صحيح في رسالتك.")

print("🤖 البوت المولد للروابط يعمل الآن...")
bot.infinity_polling()
