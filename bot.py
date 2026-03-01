import logging
import asyncio
import random
from io import BytesIO
from telegram import Update, Bot
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
from telegram.constants import ParseMode
from config import TELEGRAM_TOKEN, CHANNEL_ID, ADMIN_IDS
from ai_client import generate_post, generate_caption_only
from product_fetcher import fetch_product_info, download_image
from affiliate import get_affiliate_link

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


# ─── helpers ────────────────────────────────────────────────────────────────

def is_admin(user_id: int) -> bool:
    return not ADMIN_IDS or user_id in ADMIN_IDS


async def send_post_to_channel(bot: Bot, text: str, image_bytes: bytes | None = None):
    """Send post to the configured Telegram channel."""
    if not CHANNEL_ID:
        raise ValueError("CHANNEL_ID not configured! Use /setchannel @username")

    if image_bytes:
        await bot.send_photo(
            chat_id=CHANNEL_ID,
            photo=BytesIO(image_bytes),
            caption=text[:1024],
            parse_mode=ParseMode.HTML,
        )
    else:
        await bot.send_message(
            chat_id=CHANNEL_ID,
            text=text[:4096],
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=False,
        )


# ─── commands ────────────────────────────────────────────────────────────────

async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 <b>Vireo Bot — Telegram Channel AI Publisher</b>\n\n"
        "Команди:\n"
        "📤 /post <ссылка> — опублікувати пост в канал\n"
        "👁 /preview <ссылка> — переглянути пост без публікації\n"
        "📌 /setchannel @username — встановити канал\n"
        "ℹ️ /status — статус бота\n\n"
        "Приклад:\n<code>/post https://aliexpress.com/item/...</code>",
        parse_mode=ParseMode.HTML,
    )


async def cmd_status(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    channel = CHANNEL_ID or "❌ не встановлено"
    await update.message.reply_text(
        f"✅ <b>Бот працює</b>\n\n"
        f"📢 Канал: <code>{channel}</code>\n"
        f"🤖 AI: NVIDIA NIM (4 ключі)\n"
        f"🔄 Статус: online",
        parse_mode=ParseMode.HTML,
    )


async def cmd_setchannel(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    args = ctx.args
    if not args:
        await update.message.reply_text("Використання: /setchannel @username або -100XXXXX")
        return
    import config
    config.CHANNEL_ID = args[0]
    await update.message.reply_text(f"✅ Канал встановлено: <code>{args[0]}</code>", parse_mode=ParseMode.HTML)


async def cmd_post(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Generate AI post and publish to channel."""
    if not is_admin(update.effective_user.id):
        return

    args = ctx.args
    if not args:
        await update.message.reply_text(
            "Використання: /post <url> [опис товару]\n"
            "Приклад: /post https://ali.onl/abc123 Павербанк 20000мАч"
        )
        return

    url = args[0]
    extra_info = " ".join(args[1:]) if len(args) > 1 else ""

    msg = await update.message.reply_text("⏳ Збираю інформацію про товар...")

    try:
        # 1. Fetch product info
        product = fetch_product_info(url)
        product_text = f"Назва: {product['title']}\n"
        if product['price']:
            product_text += f"Ціна: {product['price']}\n"
        if product['description']:
            product_text += f"Опис: {product['description']}\n"
        if extra_info:
            product_text += f"Додаткова інформація: {extra_info}\n"

        await msg.edit_text("🤖 Генерую пост через AI...")

        # 2. Generate post text
        post_text = generate_post(product_text, url)

        # 3. Get image
        image_bytes = download_image(product['image_url']) if product['image_url'] else None

        await msg.edit_text("📤 Публікую в канал...")

        # 4. Send to channel
        await send_post_to_channel(ctx.bot, post_text, image_bytes)

        await msg.edit_text(
            f"✅ <b>Пост опубліковано!</b>\n\n"
            f"📦 Товар: {product['title'][:80]}\n"
            f"📢 Канал: {CHANNEL_ID}",
            parse_mode=ParseMode.HTML,
        )

    except Exception as e:
        logger.exception(f"post error: {e}")
        await msg.edit_text(f"❌ Помилка: {e}")


async def cmd_preview(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Preview post without publishing."""
    if not is_admin(update.effective_user.id):
        return

    args = ctx.args
    if not args:
        await update.message.reply_text("Використання: /preview <url> [опис]")
        return

    url = args[0]
    extra_info = " ".join(args[1:]) if len(args) > 1 else ""

    msg = await update.message.reply_text("⏳ Генерую попередній перегляд...")

    try:
        product = fetch_product_info(url)
        product_text = f"Назва: {product['title']}\n"
        if product['price']:
            product_text += f"Ціна: {product['price']}\n"
        if product['description']:
            product_text += f"Опис: {product['description']}\n"
        if extra_info:
            product_text += f"Додаткова інформація: {extra_info}\n"

        # Affiliate Link Generation
        ref_link = get_affiliate_link(url)

        await msg.edit_text("🤖 AI генерує...")
        post_text = generate_post(product_text, ref_link)

        await msg.delete()
        await update.message.reply_text(
            f"👁 <b>ПОПЕРЕДНІЙ ПЕРЕГЛЯД:</b>\n\n{post_text[:4000]}",
            parse_mode=ParseMode.HTML,
        )

    except Exception as e:
        logger.exception(f"preview error: {e}")
        await msg.edit_text(f"❌ Помилка: {e}")

# ─── autonomous ─────────────────────────────────────────────────────────────

async def scheduled_post(context: ContextTypes.DEFAULT_TYPE):
    """Automatically find product and post to channel."""
    logger.info("Running scheduled post...")
    if not CHANNEL_ID:
        logger.warning("No CHANNEL_ID set. Skipping scheduled post.")
        return

    # TODO: Implement automated fetching of discounted products from AliExpress/Partners
    # For now, we are waiting for the user to provide the RSS/Deeplink base or scraping logic
    # This is a placeholder for the autonomous logic
    sample_url = "https://www.aliexpress.com/item/1005006093417740.html" 
    
    try:
        product = fetch_product_info(sample_url)
        product_text = f"Назва: {product['title']}\n"
        if product['price']:
            product_text += f"Ціна: {product['price']}\n"
        
        ref_link = get_affiliate_link(sample_url)
        post_text = generate_post(product_text, ref_link)
        image_bytes = download_image(product['image_url']) if product['image_url'] else None

        await send_post_to_channel(context.bot, post_text, image_bytes)
        logger.info(f"Successfully published scheduled post for {product['title'][:50]}")
    except Exception as e:
        logger.error(f"Failed to publish scheduled post: {e}")

# ─── main ────────────────────────────────────────────────────────────────────

def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help", cmd_start))
    app.add_handler(CommandHandler("status", cmd_status))
    app.add_handler(CommandHandler("setchannel", cmd_setchannel))
    app.add_handler(CommandHandler("post", cmd_post))
    app.add_handler(CommandHandler("preview", cmd_preview))

    # Setup job queue for 5 times a day (10:00, 13:00, 16:00, 19:00, 21:00 UTC)
    if app.job_queue:
        from datetime import time, timezone
        times = [
            time(hour=7, minute=0, tzinfo=timezone.utc),  # 10:00 Kiev
            time(hour=10, minute=0, tzinfo=timezone.utc), # 13:00 Kiev
            time(hour=13, minute=0, tzinfo=timezone.utc), # 16:00 Kiev
            time(hour=16, minute=0, tzinfo=timezone.utc), # 19:00 Kiev
            time(hour=18, minute=0, tzinfo=timezone.utc), # 21:00 Kiev
        ]
        for t in times:
            app.job_queue.run_daily(scheduled_post, t)
        logger.info(f"Scheduled jobs for: {[t.strftime('%H:%M') for t in times]} UTC")

    logger.info("🚀 Vireo Bot starting...")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
