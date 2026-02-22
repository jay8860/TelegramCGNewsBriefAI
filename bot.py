import os
import logging
import time
import threading
import schedule
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from scraper import fetch_feed_articles, fetch_article_text
from summarizer import summarize_daily_news, summarize_single_article
from database import init_db, is_url_seen, mark_url_seen

# Logging configuration
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Constants
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TARGET_CHAT_ID = os.environ.get("TARGET_CHAT_ID")  # Chat ID of the user for the 8 AM message

# Initialize DB
init_db()

async def send_daily_briefing(context: ContextTypes.DEFAULT_TYPE):
    """Job function to send the 8 AM daily briefing."""
    if not TARGET_CHAT_ID:
        logger.error("TARGET_CHAT_ID environment variable not set. Cannot send daily briefing.")
        return

    logger.info("Starting daily briefing generation...")
    
    # 1. Fetch articles
    raw_articles = fetch_feed_articles(max_per_feed=5)
    
    # 2. Filter out already seen and get text
    unseen_articles = []
    for art in raw_articles:
        if not is_url_seen(art['url']):
            text = fetch_article_text(art['url'])
            if text:
                art['content'] = text
                unseen_articles.append(art)

    if not unseen_articles:
        await context.bot.send_message(chat_id=TARGET_CHAT_ID, text="Good morning! There are no new fresh high-priority news articles to summarize today.")
        return

    # 3. Summarize using Gemini
    summary_text = summarize_daily_news(unseen_articles)

    # 4. Send to user
    await context.bot.send_message(chat_id=TARGET_CHAT_ID, text=summary_text, parse_mode='Markdown')

    # 5. Mark as seen
    for art in unseen_articles:
        mark_url_seen(art['url'])
        
    logger.info("Daily briefing sent efficiently.")


# Scheduled task runner
def run_scheduler(application):
    """Runs the schedule continuously in a separate thread."""
    # Assuming Indian Standard Time (IST) configured on server or Railway
    schedule.every().day.at("08:00").do(
        lambda: application.job_queue.run_once(send_daily_briefing, 1)
    )
    
    while True:
        schedule.run_pending()
        time.sleep(60)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message when the command /start is issued."""
    user = update.effective_user
    chat_id = update.effective_chat.id
    welcome_text = (
        f"Hello {user.first_name}! I am your Chhattisgarh News Brief AI.\n\n"
        f"Your Chat ID is: `{chat_id}`\n"
        f"Please set this as your TARGET_CHAT_ID environment variable in Railway.\n\n"
        f"I will send you a daily briefing at 8 AM. You can also send me any article text to summarize."
    )
    await update.message.reply_markdown(welcome_text)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Summarize any pasted article or long text."""
    text = update.message.text
    if len(text) < 50:
        await update.message.reply_text("Please paste a longer text or article to summarize.")
        return
        
    processing_msg = await update.message.reply_text("Analyzing and summarizing your article... ⏳")
    
    summary = summarize_single_article(text)
    
    await processing_msg.edit_text(summary, parse_mode='Markdown')

async def trigger_briefing(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Manual trigger to get the briefing immediately. Useful for testing."""
    if str(update.effective_chat.id) != TARGET_CHAT_ID:
        await update.message.reply_text("You are not authorized to trigger this command.")
        return
    
    processing_msg = await update.message.reply_text("Generating ad-hoc daily briefing... ⏳")
    
    # 1. Fetch articles
    raw_articles = fetch_feed_articles(max_per_feed=5)
    
    # 2. Filter out already seen and get text
    unseen_articles = []
    for art in raw_articles:
        if not is_url_seen(art['url']):
            text = fetch_article_text(art['url'])
            if text:
                art['content'] = text
                unseen_articles.append(art)

    if not unseen_articles:
        await processing_msg.edit_text("No new articles to summarize right now.")
        return

    # 3. Summarize using Gemini
    summary_text = summarize_daily_news(unseen_articles)

    # 4. Send to user
    await processing_msg.edit_text(summary_text, parse_mode='Markdown')

    # 5. Mark as seen
    for art in unseen_articles:
        mark_url_seen(art['url'])

def main():
    """Start the bot."""
    if not TELEGRAM_TOKEN:
        logger.error("TELEGRAM_TOKEN must be set.")
        return

    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # on different commands - answer in Telegram
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("briefing", trigger_briefing))

    # on non command i.e message - echo the message on Telegram
    application.add_handler(MessageHandler(filters.TEXT & ~(filters.COMMAND), handle_message))

    # Start the scheduler thread
    scheduler_thread = threading.Thread(target=run_scheduler, args=(application,), daemon=True)
    scheduler_thread.start()

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
