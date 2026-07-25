# E:\tradedo\app\backend\utils\telegram_bot.py

import os
import logging
import asyncio
from typing import Optional, Dict, List
from datetime import datetime
from dotenv import load_dotenv

from telegram import Bot, Update
from telegram.constants import ParseMode
from telegram.ext import (
    Application, CommandHandler, ContextTypes
)

load_dotenv()
logger = logging.getLogger("tradedo.telegram")

# ─── Configuration ────────────────────────────────────────────
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID   = os.getenv("TELEGRAM_CHAT_ID")

if not BOT_TOKEN or not CHAT_ID:
    logger.warning("⚠️  Telegram credentials missing in .env")


# ─── Bot Instance (singleton) ────────────────────────────────
class TelegramNotifier:
    _bot: Optional[Bot] = None
    _app: Optional[Application] = None

    @classmethod
    def get_bot(cls) -> Bot:
        if cls._bot is None:
            cls._bot = Bot(token=BOT_TOKEN)
        return cls._bot

    @classmethod
    async def send(cls, message: str, silent: bool = False) -> bool:
        """Send a message to configured chat."""
        if not BOT_TOKEN or not CHAT_ID:
            logger.warning("Telegram not configured")
            return False

        try:
            bot = cls.get_bot()
            await bot.send_message(
                chat_id      = CHAT_ID,
                text         = message,
                parse_mode   = ParseMode.HTML,
                disable_notification = silent,
            )
            return True
        except Exception as e:
            logger.error(f"Telegram send failed: {e}")
            return False


# ─── Message Formatters ───────────────────────────────────────

def format_signal_alert(prediction: Dict) -> str:
    """Format strong signal alert."""
    signal   = prediction.get("signal")
    symbol   = prediction.get("symbol", "").replace(".NS", "")
    price    = prediction.get("current_price", 0)
    conf     = prediction.get("confidence_pct", 0)
    plan     = prediction.get("trade_plan", {})
    composite = prediction.get("composite", {}).get("composite_score", 0)
    reasoning = prediction.get("ai_reasoning", "")

    emoji = "🟢" if signal == "BUY" else "🔴"
    
    msg = f"{emoji} <b>STRONG {signal}: {symbol}</b>\n\n"
    msg += f"📊 Confidence: <b>{conf:.1f}%</b>\n"
    msg += f"⚡ Composite: <b>{composite}/90</b>\n"
    msg += f"💰 Current: <b>₹{price:,.2f}</b>\n\n"

    if plan and plan.get("tradeable"):
        entry = plan.get("entry", {})
        t1    = plan.get("target_1", {})
        t2    = plan.get("target_2", {})
        sl    = plan.get("stop_loss", {})
        exit_time = plan.get("time_exit", {})

        msg += f"🎯 <b>Entry:</b> ₹{entry.get('price', 0):,.2f}\n"
        msg += f"📈 <b>Target 1:</b> ₹{t1.get('price', 0):,.2f} "
        msg += f"(+{t1.get('profit_pct', 0):.1f}%)\n"
        msg += f"📈 <b>Target 2:</b> ₹{t2.get('price', 0):,.2f} "
        msg += f"(+{t2.get('profit_pct', 0):.1f}%)\n"
        msg += f"🛑 <b>Stop Loss:</b> ₹{sl.get('price', 0):,.2f} "
        msg += f"({sl.get('loss_pct', 0):.1f}%)\n"
        
        if exit_time.get("exit_by"):
            msg += f"⏰ Exit by: <b>{exit_time.get('exit_by')}</b>\n"
    
    if reasoning:
        msg += f"\n🧠 <b>AI:</b> <i>{reasoning[:250]}</i>\n"

    msg += f"\n📱 <a href='http://localhost:3000/predict/{symbol}'>View on Dashboard</a>"

    return msg


def format_daily_summary(predictions: List[Dict]) -> str:
    """Format morning daily summary."""
    buys  = [p for p in predictions if p.get("signal") == "BUY"]
    sells = [p for p in predictions if p.get("signal") == "SELL"]
    
    # Sort by confidence
    buys.sort(key=lambda x: x.get("confidence_pct", 0), reverse=True)
    sells.sort(key=lambda x: x.get("confidence_pct", 0), reverse=True)

    msg = "🌅 <b>Good Morning! Today's Picks</b>\n\n"

    if buys:
        msg += f"🟢 <b>BUY Signals ({len(buys)}):</b>\n"
        for i, p in enumerate(buys[:5], 1):
            symbol = p.get("symbol", "").replace(".NS", "")
            msg += f"{i}. <b>{symbol}</b>  "
            msg += f"{p.get('confidence_pct', 0):.0f}%  "
            msg += f"₹{p.get('current_price', 0):,.0f}\n"
        msg += "\n"

    if sells:
        msg += f"🔴 <b>SELL Signals ({len(sells)}):</b>\n"
        for i, p in enumerate(sells[:5], 1):
            symbol = p.get("symbol", "").replace(".NS", "")
            msg += f"{i}. <b>{symbol}</b>  "
            msg += f"{p.get('confidence_pct', 0):.0f}%  "
            msg += f"₹{p.get('current_price', 0):,.0f}\n"
        msg += "\n"

    if not buys and not sells:
        msg += "🟡 No strong signals today. Market seems uncertain.\n\n"

    # Market regime
    if predictions and predictions[0].get("market_regime"):
        regime = predictions[0]["market_regime"]
        emoji = {"BULLISH": "📈", "BEARISH": "📉", "NEUTRAL": "➖"}
        msg += f"{emoji.get(regime, '📊')} Market Regime: <b>{regime}</b>\n"

    msg += f"\n📱 <a href='http://localhost:3000'>Open Dashboard</a>"
    return msg


def format_simple_prediction(prediction: Dict) -> str:
    """Format for /predict command reply."""
    symbol = prediction.get("symbol", "").replace(".NS", "")
    signal = prediction.get("signal")
    emoji  = prediction.get("emoji", "🟡")

    msg = f"{emoji} <b>{symbol} — {signal}</b>\n\n"
    msg += f"💰 Price: ₹{prediction.get('current_price', 0):,.2f}\n"
    msg += f"📊 Confidence: {prediction.get('confidence_pct', 0):.1f}%\n"
    msg += f"🔼 Prob Up: {prediction.get('prob_up', 0):.2%}\n"

    indicators = prediction.get("indicators", {})
    if indicators:
        msg += f"\n📈 <b>Indicators:</b>\n"
        msg += f"  RSI: {indicators.get('rsi', 0):.1f}\n"
        msg += f"  MACD: {indicators.get('macd', 0):.3f}\n"

    return msg


# ─── High-Level Alert Functions ───────────────────────────────

async def send_signal_alert(prediction: Dict) -> bool:
    """Send strong signal alert."""
    msg = format_signal_alert(prediction)
    return await TelegramNotifier.send(msg)


async def send_daily_summary(predictions: List[Dict]) -> bool:
    """Send morning summary."""
    msg = format_daily_summary(predictions)
    return await TelegramNotifier.send(msg)


async def send_message(text: str, silent: bool = False) -> bool:
    """Send a simple text message."""
    return await TelegramNotifier.send(text, silent=silent)


# ─── Command Handlers ─────────────────────────────────────────

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/start command."""
    msg = (
        "🤖 <b>Welcome to TRADEDO Bot!</b>\n\n"
        "I'll send you AI-powered stock alerts for NSE.\n\n"
        "<b>Available Commands:</b>\n"
        "/predict SYMBOL - Get instant prediction\n"
        "  Example: <code>/predict RELIANCE</code>\n\n"
        "/watchlist - Show all watchlist signals\n"
        "/status - Bot status\n"
        "/help - Show this menu\n\n"
        "You'll also receive:\n"
        "• 🌅 Morning summary at 9:00 AM\n"
        "• ⚡ Instant alerts for strong signals"
    )
    await update.message.reply_html(msg)


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/help command."""
    await cmd_start(update, context)


async def cmd_predict(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/predict SYMBOL command."""
    if not context.args:
        await update.message.reply_text(
            "Usage: /predict SYMBOL\nExample: /predict RELIANCE"
        )
        return

    symbol = context.args[0].upper()
    await update.message.reply_text(f"🔍 Analyzing {symbol}...")

    try:
        from ml.engine import predict
        result = predict(symbol, mode="swing")
        msg = format_simple_prediction(result)
        await update.message.reply_html(msg)
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")


async def cmd_watchlist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/watchlist command."""
    await update.message.reply_text("📊 Fetching watchlist...")

    try:
        from database.db import get_watchlist
        from ml.engine import predict

        symbols = get_watchlist()
        predictions = []

        for sym in symbols:
            try:
                p = predict(sym, mode="swing")
                predictions.append(p)
            except Exception as e:
                logger.warning(f"Failed for {sym}: {e}")

        msg = format_daily_summary(predictions)
        await update.message.reply_html(msg)
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")


async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/status command."""
    msg = (
        "✅ <b>TRADEDO Bot is running</b>\n\n"
        f"🕒 Server time: {datetime.now().strftime('%H:%M:%S')}\n"
        "📊 Models: Loaded\n"
        "🔔 Alerts: Active\n"
        "📱 Dashboard: http://localhost:3000"
    )
    await update.message.reply_html(msg)


# ─── Polling Setup (for commands) ─────────────────────────────

def create_bot_app() -> Optional[Application]:
    """
    Create the bot application with command handlers.
    Returns None if not configured.
    """
    if not BOT_TOKEN:
        return None

    app = Application.builder().token(BOT_TOKEN).build()

    # Register command handlers
    app.add_handler(CommandHandler("start",     cmd_start))
    app.add_handler(CommandHandler("help",      cmd_help))
    app.add_handler(CommandHandler("predict",   cmd_predict))
    app.add_handler(CommandHandler("watchlist", cmd_watchlist))
    app.add_handler(CommandHandler("status",    cmd_status))

    logger.info("✅ Telegram bot configured with 5 commands")
    return app


# ─── Quick Test ───────────────────────────────────────────────
if __name__ == "__main__":
    async def test():
        result = await send_message("🚀 TRADEDO Bot is live!")
        print("Sent:" if result else "Failed:", result)
    
    asyncio.run(test())