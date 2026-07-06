from flask import Flask, request, jsonify
from flask_cors import CORS
import google.generativeai as genai
import os

app = Flask(__name__)
CORS(app)

# جلب المفتاح السري من إعدادات الاستضافة (وليس مكتوباً هنا لحمايته)
API_KEY = os.environ.get("GEMINI_API_KEY")
genai.configure(api_key=API_KEY)

# برمجة شخصية الذكاء الاصطناعي ليتوافق مع أهداف مشروع بوصلة الطالب
SYSTEM_INSTRUCTION = """
أنت مرشد أكاديمي ورفيق طلابي مخصص لطلاب جامعة تعز - فرع التربة ضمن مشروع "بوصلة الطالب".
مهمتك:
1. مساعدة الطلاب في اختيار التخصصات الجامعية المناسبة.
2. تقديم نصائح للاستعداد لاختبارات القبول.
3. توجيه الطلاب الوافدين حول خيارات السكن والخدمات الطلابية.
يجب أن يكون أسلوبك ودوداً، مبسطاً، وداعماً للطلاب. إياك أن تتحدث بلسان الإدارة الجامعية أو تستخدم أسلوباً إدارياً صارماً.
"""

# تجهيز النموذج
model = genai.GenerativeModel('gemini-1.5-flash', system_instruction=SYSTEM_INSTRUCTION)

@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json()
        user_message = data.get("message", "")
        
        if not user_message:
            return jsonify({"error": "الرسالة فارغة"}), 400
            
        # إرسال الرسالة إلى Gemini واستلام الرد
        response = model.generate_content(user_message)
        
        return jsonify({"reply": response.text})
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
