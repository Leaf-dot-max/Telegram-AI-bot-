import os
import sys
import traceback
import requests
from flask import Flask, request
import telebot

app = Flask(__name__)

# Load secrets
try:
    TELEGRAM_TOKEN = os.environ['TELEGRAM_TOKEN']
    HF_TOKEN = os.environ['HF_TOKEN']
except KeyError as e:
    print(f"MISSING ENV: {e}", file=sys.stderr)
    sys.exit(1)

bot = telebot.TeleBot(TELEGRAM_TOKEN)

# Use the Chat Completions endpoint with a free model
API_URL = "https://router.huggingface.co/v1/chat/completions"
MODEL = "katanemo/Arch-Router-1.5B:hf-inference"  # Free, no license needed

HEADERS = {
    "Authorization": f"Bearer {HF_TOKEN}",
    "Content-Type": "application/json"
}

def ask_ai(prompt):
    try:
        payload = {
            "model": MODEL,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 500
        }
        response = requests.post(API_URL, headers=HEADERS, json=payload)
        if response.ok:
            result = response.json()
            # Chat completions response has choices[0].message.content
            return result["choices"][0]["message"]["content"].strip()
        else:
            err_msg = f"HF error {response.status_code}: {response.text}"
            print(err_msg, flush=True)
            return err_msg
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