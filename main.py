# ✅ Fixed version of your script with corrected button handling

import os
import json
import discord
import requests
from dotenv import load_dotenv
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup, Update, ParseMode
from telegram.ext import Updater, CallbackQueryHandler, CommandHandler, MessageHandler, Filters, CallbackContext
import threading

# Load environment variables
load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = int(os.getenv("TELEGRAM_CHAT_ID"))

CONFIG_FILE = "config.json"

if not os.path.exists(CONFIG_FILE):
    with open(CONFIG_FILE, "w") as f:
        json.dump({}, f)

with open(CONFIG_FILE, "r") as f:
    category_config = json.load(f)

def save_config():
    with open(CONFIG_FILE, "w") as f:
        json.dump(category_config, f, indent=4)

client = discord.Client(self_bot=True)
bot = Bot(token=TELEGRAM_TOKEN)
updater = Updater(token=TELEGRAM_TOKEN, use_context=True)
dispatcher = updater.dispatcher

def start(update: Update, context: CallbackContext):
    keyboard = [
        [InlineKeyboardButton("➕ Add Category", callback_data="admin:add_category")],
        [InlineKeyboardButton("📝 Set Response", callback_data="admin:set_response")],
        [InlineKeyboardButton("📢 Set TG Message", callback_data="admin:set_tg_msg")],
        [InlineKeyboardButton("📂 List Categories", callback_data="admin:list_categories")],
        [InlineKeyboardButton("🗑 Delete Category", callback_data="admin:delete_category")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text("🤖 Welcome to the Discord-TG Manager:\nChoose an option below:", reply_markup=reply_markup)

def handle_admin_buttons(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    action = query.data.replace("admin:", "")

    if action == "list_categories":
        if not category_config:
            query.edit_message_text("No categories configured.")
            return
        text = "*Configured Categories:*\n"
        for cat_id, data in category_config.items():
            text += f"- `{cat_id}`: {data.get('type', 'N/A')}\n"
        query.edit_message_text(text, parse_mode=ParseMode.MARKDOWN)

    elif action == "add_category":
        query.edit_message_text("Send category ID and type:\nFormat:\n`<category_id> <type>`", parse_mode="Markdown")
        context.user_data["awaiting"] = "add_category"

    elif action == "set_response":
        query.edit_message_text("Send category ID and response:\nFormat:\n`<category_id> <response text>`", parse_mode="Markdown")
        context.user_data["awaiting"] = "set_response"

    elif action == "set_tg_msg":
        query.edit_message_text("Send category ID and telegram message:\nFormat:\n`<category_id> <message text>`", parse_mode="Markdown")
        context.user_data["awaiting"] = "set_tg_msg"

    elif action == "delete_category":
        query.edit_message_text("Send category ID to delete:\nFormat:\n`<category_id>`", parse_mode="Markdown")
        context.user_data["awaiting"] = "delete_category"

def handle_text(update: Update, context: CallbackContext):
    text = update.message.text.strip()
    waiting_for = context.user_data.get("awaiting")

    if waiting_for == "add_category":
        try:
            cat_id, cat_type = text.split(maxsplit=1)
            category_config[cat_id] = {
                "type": cat_type,
                "telegram_msg": f"New {cat_type} ticket: *{{name}}*",
                "response": "Default response"
            }
            save_config()
            update.message.reply_text(f"✅ Category `{cat_id}` added as `{cat_type}`", parse_mode="Markdown")
        except:
            update.message.reply_text("❌ Invalid format. Use:\n`<category_id> <type>`", parse_mode="Markdown")

    elif waiting_for == "set_response":
        try:
            cat_id, response = text.split(maxsplit=1)
            if cat_id in category_config:
                category_config[cat_id]["response"] = response
                save_config()
                update.message.reply_text("✅ Response updated.")
            else:
                update.message.reply_text("❌ Category ID not found.")
        except:
            update.message.reply_text("❌ Invalid format. Use:\n`<category_id> <response text>`", parse_mode="Markdown")

    elif waiting_for == "set_tg_msg":
        try:
            cat_id, tg_msg = text.split(maxsplit=1)
            if cat_id in category_config:
                category_config[cat_id]["telegram_msg"] = tg_msg
                save_config()
                update.message.reply_text("✅ Telegram message updated.")
            else:
                update.message.reply_text("❌ Category ID not found.")
        except:
            update.message.reply_text("❌ Invalid format. Use:\n`<category_id> <message text>`", parse_mode="Markdown")

    elif waiting_for == "delete_category":
        cat_id = text
        if cat_id in category_config:
            del category_config[cat_id]
            save_config()
            update.message.reply_text(f"🗑️ Category `{cat_id}` deleted.", parse_mode="Markdown")
        else:
            update.message.reply_text("❌ Category ID not found.")

    context.user_data["awaiting"] = None

dispatcher.add_handler(CommandHandler("start", start))
dispatcher.add_handler(CallbackQueryHandler(handle_admin_buttons, pattern="^admin:"))
dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_text))

def send_ticket_message(channel_id, channel_name, category_id):
    config = category_config.get(str(category_id))
    if not config:
        return
    keyboard = [
        [
            InlineKeyboardButton("✅ Yes", callback_data=f"reply:{channel_id}:{category_id}"),
            InlineKeyboardButton("❌ No", callback_data=f"ignore:{channel_id}")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    bot.send_message(
        chat_id=TELEGRAM_CHAT_ID,
        text=config["telegram_msg"].format(name=channel_name),
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

def handle_reply_buttons(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    parts = query.data.split(":")
    action = parts[0]
    channel_id = int(parts[1])
    category_id = parts[2]
    config = category_config.get(str(category_id), {})

    if action == "reply":
        channel = client.get_channel(channel_id)
        if channel:
            response = config.get("response", "Hello! How can I help you?")
            client.loop.create_task(channel.send(response))
            query.edit_message_text(
    text=f"✅ Response sent to channel *{channel.name}* (`{channel.id}`)",
    parse_mode="Markdown"
)
        else:
            query.edit_message_text(text="❌ Channel not found.")
    elif action == "ignore":
        query.edit_message_text(text="⏭️ Response skipped.")

dispatcher.add_handler(CallbackQueryHandler(handle_reply_buttons, pattern="^(reply|ignore):"))

@client.event
async def on_ready():
    print(f"✅ Logged in as {client.user}")
    threading.Thread(target=updater.start_polling, daemon=True).start()

@client.event
async def on_guild_channel_create(channel):
    if str(channel.category_id) in category_config:
        print(f"🎫 New ticket: {channel.name}")
        send_ticket_message(channel.id, channel.name, channel.category_id)

client.run(DISCORD_TOKEN)
