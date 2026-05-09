import os
import sys
import traceback
import requests
from flask import Flask, request
import telebot

app = Flask(__name__)

try:
    TELEGRAM_TOKEN = os.environ['TELEGRAM_TOKEN']
    HF_TOKEN = os.environ['HF_TOKEN']
except KeyError as e:
    print(f"MISSING ENV: {e}", file=sys.stderr)
    sys.exit(1)

bot = telebot.TeleBot(TELEGRAM_TOKEN)

# Works with fine‑grained tokens + the new Router
API_URL = API_URL = "https://router.huggingface.co/hf-inference/models/google/flan-t5-large"
HEADERS = {"Authorization": f"Bearer {HF_TOKEN}"}

def ask_ai(prompt):
    try:
        payload = {"inputs": prompt, "parameters": {"max_new_tokens": 150}}
        response = requests.post(API_URL, headers=HEADERS, json=payload)
        if response.ok:
            result = response.json()
            # Handle the response format (list or dict)
            if isinstance(result, list) and len(result) > 0:
                return result[0]["generated_text"].strip()
            elif isinstance(result, dict) and "generated_text" in result:
                return result["generated_text"].strip()
            else:
                return str(result).strip()
        else:
            error_msg = f"HF error {response.status_code}: {response.text}"
            print(error_msg, flush=True)
            return error_msg
    except Exception as e:
        print(traceback.format_exc(), flush=True)
        return f"Exception: {str(e)}"

@app.route(f"/{TELEGRAM_TOKEN}", methods=["POST"])
def webhook():
    if request.headers.get("content-type") == "application/json":
        json_string = request.get_data().decode("utf-8")
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return "", 200
    return "Bad request", 400

@bot.message_handler(commands=["start"])
def send_welcome(message):
    print("Got /start", flush=True)
    bot.reply_to(message, "Hello! I'm your personal AI assistant. Ask me anything!")

@bot.message_handler(func=lambda msg: True)
def handle_text(message):
    print(f"Message: {message.text}", flush=True)
    bot.send_chat_action(message.chat.id, "typing")
    reply = ask_ai(message.text)
    bot.reply_to(message, reply)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))