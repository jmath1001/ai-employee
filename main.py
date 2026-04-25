import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
from brain import ask_ai

load_dotenv()
TOKEN = os.getenv("TELEGRAM_TOKEN")


async def scheduled_callback(context: ContextTypes.DEFAULT_TYPE):
    job = context.job
    result = ask_ai(f"SYSTEM: Timer is up. Action: {job.data['desc']}")
    await context.bot.send_message(chat_id=job.chat_id, text=f"⏰ Update: {result}")


async def send_file_to_telegram(chat_id, filepath, context):
    try:
        with open(filepath, 'rb') as f:
            await context.bot.send_document(chat_id=chat_id, document=f)
    except Exception as e:
        await context.bot.send_message(chat_id=chat_id, text=f"Couldn't send file: {e}")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None or not update.message.text:
        return

    user_text = update.message.text
    user_id = str(update.effective_user.id)
    print(f"--- User said: {user_text} ---")

    ai_response = ask_ai(user_text, user_id)

    if ai_response.startswith("MULTI_FILE_SIGNAL|"):
        # Multiple files — send them all
        paths = ai_response.split("|")[1:]
        for path in paths:
            if os.path.exists(path):
                await send_file_to_telegram(update.effective_chat.id, path, context)
            else:
                await update.message.reply_text(f"⚠️ File not found: {path}")

    elif ai_response.startswith("FILE_SIGNAL|"):
        filepath = ai_response.split("|")[1]
        await send_file_to_telegram(update.effective_chat.id, filepath, context)

    elif "SCHEDULE_SIGNAL" in ai_response:
        parts = ai_response.split("|")
        if len(parts) < 3:
            await update.message.reply_text("I couldn't schedule that because the timer payload was invalid.")
            return

        try:
            mins = float(parts[1])
            if mins <= 0:
                raise ValueError("minutes must be positive")
        except Exception:
            await update.message.reply_text("Please provide a valid positive number of minutes.")
            return

        task_desc = parts[2]
        context.job_queue.run_once(
            scheduled_callback,
            when=mins * 60,
            chat_id=update.effective_chat.id,
            data={'desc': task_desc}
        )
        await update.message.reply_text(f"✅ Okay, I've scheduled that for {mins} minutes from now.")

    else:
        await update.message.reply_text(ai_response)


if __name__ == '__main__':
    if not TOKEN:
        raise RuntimeError("Missing TELEGRAM_TOKEN in environment.")

    print("Bot is starting with Scheduler...")
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    print("Bot is now listening (and can schedule tasks)!")
    app.run_polling()