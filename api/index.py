
import os
import google.generativeai as genai
from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# تهيئة مفتاح API الخاص بـ Gemini من متغيرات البيئة
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
if GEMINI_API_KEY:
  genai.configure(api_key=GEMINI_API_KEY)


@app.route("/api/chat", methods=["POST"])
def chat():
  try:
    data = request.get_json()
    if not data:
      return jsonify({"error": "Invalid JSON data"}), 400

    user_message = data.get("message", "")
    history = data.get("history", [])
    image_base64 = data.get("image", None)

    model = genai.GenerativeModel("gemini-1.5-flash")

    formatted_history = []
    for h in history:
      role = "user" if h.get("role") == "user" else "model"
      formatted_history.append(
          {"role": role, "parts": [h.get("text", "")]}
      )

    chat_session = model.start_chat(history=formatted_history)

    content_parts = [user_message]
    if image_base64:
      import base64

      image_parts = {
          "mime_type": "image/jpeg",
          "data": base64.b64decode(image_base64),
      }
      content_parts.append(image_parts)

    response = chat_session.send_message(content_parts)
    return jsonify({"response": response.text})

  except Exception as e:
    return jsonify({"error": str(e)}), 500


@app.route("/", methods=["GET"])
def home():
  return jsonify(
      {"status": "Student Bot API is running successfully on Vercel!"}
  )


if __name__ == "__main__":
  app.run(debug=True)
