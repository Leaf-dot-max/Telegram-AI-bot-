import os
import requests
from flask import Flask, request
import telebot

app = Flask(__name__)

# Load secrets from environment variables
TELEGRAM_TOKEN = os.environ['TELEGRAM_TOKEN']
HF_TOKEN = os.environ['HF_TOKEN']

bot = telebot.TeleBot(TELEGRAM_TOKEN)

# Hugging Face model settings
API_URL = "https://api-inference.huggingface.co/models/microsoft/Phi-3-mini-4k-instruct"
HEADERS = {"Authorization": f"Bearer {HF_TOKEN}"}

def ask_ai(prompt):
    """Send the user's message to the AI model and return the reply."""
    payload = {
        "inputs": f"<|user|>\n{prompt}<|end|>\n<|assistant|>",
        "parameters": {"max_new_tokens": 500}
    }
    response = requests.post(API_URL, headers=HEADERS, json=payload)
    if response.ok:
        result = response.json()
        # Extract generated text properly
        return result[0]["generated_text"].split("<|assistant|>")[-1].strip()
    else:
        return "Sorry, I'm having trouble thinking right now."

@app.route(f"/{TELEGRAM_TOKEN}", methods=["POST"])
def webhook():
    """Receive updates from Telegram."""
    if request.headers.get("content-type") == "application/json":
        json_string = request.get_data().decode("utf-8")
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return "", 200
    return "Bad request", 400

@bot.message_handler(commands=["start"])
def send_welcome(message):
    bot.reply_to(message, "Hello! I'm your personal AI assistant. Ask me anything!")

@bot.message_handler(func=lambda msg: True)
def handle_text(message):
    # typing indicator
    bot.send_chat_action(message.chat.id, "typing")
    reply = ask_ai(message.text)
    bot.reply_to(message, reply, parse_mode="Markdown")

# Required for Render to detect the web service port
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
