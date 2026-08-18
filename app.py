from flask import Flask, redirect, jsonify
import requests
import re
import urllib3

# تجاهل تحذيرات الـ SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# تهيئة تطبيق الويب السريع
app = Flask(__name__)
COMMON_USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'

def get_uqload_direct(video_id):
    """دالة تقوم بالدخول لموقع Uqload واستخراج الرابط المباشر (التوكن الجديد)"""
    url = f"https://uqload.vc/{video_id}"
    headers = {'User-Agent': COMMON_USER_AGENT, 'Referer': 'https://uqload.vc/'}
    
    try:
        r = requests.get(url, headers=headers, timeout=20, verify=False)
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
        # البحث عن رابط الـ mp4 أو m3u8
        urls = re.findall(r'https?://[^\\"\' ]+\.(?:mp4|m3u8)[^\\"\' ]*', decoded)
        
        if urls:
            return urls[0]
        return None
    except Exception:
        return None

@app.route('/play/uqload/<video_id>')
def play_uqload(video_id):
    """
    هذا هو مسار الرابط الثابت. 
    عندما يزوره شخص، سيجلب التوكن الجديد ويوجهه فوراً (302 Redirect).
    """
    direct_link = get_uqload_direct(video_id)
    if direct_link:
        # إعادة توجيه المشاهد فوراً إلى الرابط المباشر الحقيقي
        return redirect(direct_link, code=302)
    else:
        return jsonify({"error": "Failed to extract direct link or video deleted."}), 404

@app.route('/')
def index():
    return "✅ Arab Fleex Static Link API is running perfectly!"

if __name__ == '__main__':
    # تشغيل السيرفر
    app.run(host='0.0.0.0', port=5000)
