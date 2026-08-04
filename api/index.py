from flask import Flask, request, jsonify
from flask_cors import CORS
import google.generativeai as genai
import os
import requests

app = Flask(__name__)
CORS(app)

# جلب المفاتيح السرية من Vercel
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
SAMBANOVA_API_KEY = os.environ.get("SAMBANOVA_API_KEY")
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")

genai.configure(api_key=GEMINI_API_KEY)

# شخصية الذكاء الاصطناعي الثابتة لتناسب منصة بوصلة الطالب
SYSTEM_INSTRUCTION = """
أنت مرشد أكاديمي ورفيق طلابي مخصص لطلاب جامعة تعز - فرع التربة ضمن مشروع "بوصلة الطالب".
مهمتك مساعدة الطلاب في التوجيه الأكاديمي، واختيار التخصصات، والاستعداد لاختبارات القبول.
يجب أن يكون أسلوبك ودوداً، مبسطاً، وداعماً للطلاب، وتجنب التحدث بلسان الإدارة الجامعية.
"""

@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json()
        user_message = data.get("message", "")
        # تحديد المزود (الافتراضي هو gemini إذا لم يرسل التطبيق اسماً)
        provider = data.get("provider", "gemini") 
        
        if not user_message:
            return jsonify({"error": "الرسالة فارغة"}), 400

        reply = ""

        # 1. توجيه الطلب إلى Google Gemini
        if provider == "gemini":
            model = genai.GenerativeModel('gemini-1.5-flash', system_instruction=SYSTEM_INSTRUCTION)
            response = model.generate_content(user_message)
            reply = response.text

        # 2. توجيه الطلب إلى SambaNova (نموذج Llama-3 السريع)
        elif provider == "sambanova":
            headers = {
                "Authorization": f"Bearer {SAMBANOVA_API_KEY}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": "Meta-Llama-3-8B-Instruct",
                "messages": [
                    {"role": "system", "content": SYSTEM_INSTRUCTION},
                    {"role": "user", "content": user_message}
                ]
            }
            res = requests.post("https://api.sambanova.ai/v1/chat/completions", headers=headers, json=payload)
            res_json = res.json()
            reply = res_json['choices'][0]['message']['content']

        # 3. توجيه الطلب إلى OpenRouter (نموذج Llama-3 المجاني)
        elif provider == "openrouter":
            headers = {
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://student-compass.com", # رابط افتراضي للمشروع
                "X-Title": "Student Compass"
            }
            payload = {
                "model": "meta-llama/llama-3-8b-instruct:free",
                "messages": [
                    {"role": "system", "content": SYSTEM_INSTRUCTION},
                    {"role": "user", "content": user_message}
                ]
            }
            res = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload)
            res_json = res.json()
            reply = res_json['choices'][0]['message']['content']
            
        else:
            return jsonify({"error": "مزود الذكاء الاصطناعي غير معروف"}), 400

        return jsonify({"reply": reply})
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
