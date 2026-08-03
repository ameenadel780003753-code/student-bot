from flask import Flask, request, jsonify
from flask_cors import CORS
import google.generativeai as genai
import os
import requests
import base64

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
مهمتك مساعدة الطلاب في التوجيه الأكاديمي، واختيار التخصصات، والاستعداد لاختبارات القبول، ومساعدة المطورين في حل الأخطاء البرمجية.
يجب أن يكون أسلوبك ودوداً، مبسطاً، وداعماً للطلاب، وتجنب التحدث بلسان الإدارة الجامعية.
"""

@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json()
        
        # استلام قائمة الرسائل كاملة (السجل) أو رسالة مفردة كاحتياط
        messages = data.get("messages", [])
        user_message = data.get("message", "")
        
        if not messages and user_message:
            messages = [{"role": "user", "content": user_message}]

        # تحديد المزود (الافتراضي هو gemini)
        provider = data.get("provider", "gemini") 
        # استقبال الصورة بصيغة Base64 إن وجدت
        base64_image = data.get("image", None)
        
        if not messages:
            return jsonify({"error": "الرسالة فارغة"}), 400

        reply = ""

        # 1. توجيه الطلب إلى Google Gemini (يدعم السجل والصور معاً)
        if provider == "gemini":
            model = genai.GenerativeModel('gemini-1.5-flash', system_instruction=SYSTEM_INSTRUCTION)
            
            gemini_history = []
            latest_message_content = ""

            for i, msg in enumerate(messages):
                role = msg.get('role')
                content = msg.get('content', '')
                
                # توحيد الأدوار لتتوافق مع متطلبات جمني ('user' أو 'model')
                gemini_role = 'user' if role in ['user', 'system'] else 'model'
                
                if i == len(messages) - 1:
                    latest_message_content = content
                else:
                    gemini_history.append({
                        'role': gemini_role,
                        'parts': [content]
                    })

            # تجهيز محتوى الرسالة الأخيرة مع إرفاق الصورة إن وجدت
            last_parts = [latest_message_content]
            if base64_image:
                image_parts = {
                    'mime_type': 'image/jpeg',
                    'data': base64.b64decode(base64_image)
                }
                last_parts.append(image_parts)

            chat_session = model.start_chat(history=gemini_history)
            response = chat_session.send_message(last_parts)
            reply = response.text

        # 2. توجيه الطلب إلى SambaNova
        elif provider == "sambanova":
            headers = {
                "Authorization": f"Bearer {SAMBANOVA_API_KEY}",
                "Content-Type": "application/json"
            }
            
            formatted_messages = [{"role": "system", "content": SYSTEM_INSTRUCTION}]
            for msg in messages:
                formatted_messages.append({
                    "role": msg.get("role"),
                    "content": msg.get("content")
                })

            payload = {
                "model": "Meta-Llama-3-8B-Instruct",
                "messages": formatted_messages
            }
            res = requests.post("https://api.sambanova.ai/v1/chat/completions", headers=headers, json=payload)
            res_json = res.json()
            reply = res_json['choices'][0]['message']['content']

        # 3. توجيه الطلب إلى OpenRouter
        elif provider == "openrouter":
            headers = {
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://student-compass.com",
                "X-Title": "Student Compass"
            }
            
            formatted_messages = [{"role": "system", "content": SYSTEM_INSTRUCTION}]
            for msg in messages:
                formatted_messages.append({
                    "role": msg.get("role"),
                    "content": msg.get("content")
                })

            payload = {
                "model": "meta-llama/llama-3-8b-instruct:free",
                "messages": formatted_messages
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
