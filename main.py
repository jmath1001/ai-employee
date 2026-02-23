import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
from brain import ask_ai

# 1. Load your keys
load_dotenv()
TOKEN = os.getenv("TELEGRAM_TOKEN")


# 2. This is the 'Alarm Clock' function
# It runs when the timer hits zero
async def scheduled_callback(context: ContextTypes.DEFAULT_TYPE):
    job = context.job
    # The bot talks to itself to finish the task
    result = ask_ai(f"SYSTEM: Timer is up. Action: {job.data['desc']}")
    await context.bot.send_message(chat_id=job.chat_id, text=f"⏰ Update: {result}")

async def send_file_to_telegram(chat_id, filepath, context):
    try:
        with open(filepath, 'rb') as f:
            await context.bot.send_document(chat_id=chat_id, document=f)
    except Exception as e:
        await context.bot.send_message(chat_id=chat_id, text=f"Couldn't send file: {e}")
# 3. This handles your live messages
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    user_id = str(update.effective_user.id)
    print(f"--- User said: {user_text} ---")

    # Send message to OpenAI brain
    ai_response = ask_ai(user_text, user_id)
    if ai_response.startswith("FILE_SIGNAL|"):
        filepath = ai_response.split("|")[1]
        await send_file_to_telegram(update.effective_chat.id, filepath, context)
    # CHECK: Did the AI ask to schedule something?
    elif "SCHEDULE_SIGNAL" in ai_response:
        # Split the message: SIGNAL | MINUTES | TASK
        parts = ai_response.split("|")
        mins = float(parts[1])
        task_desc = parts[2]

        # Set the 'Alarm'
        context.job_queue.run_once(
            scheduled_callback,
            when=mins * 60,
            chat_id=update.effective_chat.id,
            data={'desc': task_desc}
        )
        await update.message.reply_text(f"✅ Okay, I've scheduled that for {mins} minutes from now.")
    else:
        # Just a normal reply
        await update.message.reply_text(ai_response)


if __name__ == '__main__':
    print("Bot is starting with Scheduler...")

    # The JobQueue is built-in to the application
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))

    print("Bot is now listening (and can schedule tasks)!")
    app.run_polling()