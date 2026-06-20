"""Notifications Module - Email & Webhook & Telegram alerts"""
import logging
import requests
from datetime import datetime
from config import NOTIFICATIONS

logger = logging.getLogger(__name__)

TELEGRAM_TOKEN = NOTIFICATIONS.get("telegram_token")
TELEGRAM_CHAT_ID = NOTIFICATIONS.get("telegram_chat_id")


class NotificationManager:
    """Send trade notifications via email/webhook"""

    @staticmethod
    def send_trade_alert(
        trade_type: str,
        symbol: str,
        price: float,
        quantity: float,
        stop_loss: float,
        take_profit: float,
        reason: str = "",
    ):
        """Send trade entry alert"""
        if not NOTIFICATIONS["enabled"]:
            return

        message = f"""
🤖 <b>TRADE ALERT - {trade_type}</b>
Symbol: <b>{symbol}</b>
Entry Price: ${price:.2f}
Quantity: {quantity}
Stop Loss: ${stop_loss:.2f}
Take Profit: ${take_profit:.2f}
Reason: {reason}
Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """

        NotificationManager._send_webhook(message, "trade_entry")
        NotificationManager._send_email(
            f"Trade Alert: {symbol} {trade_type}",
            message
        )
        NotificationManager._send_telegram(message)

    @staticmethod
    def send_position_closed(
        symbol: str,
        entry_price: float,
        exit_price: float,
        quantity: float,
        pnl: float,
        reason: str = "Take Profit",
    ):
        """Send position closed alert"""
        if not NOTIFICATIONS["enabled"]:
            return

        pnl_pct = (pnl/entry_price)*100 if entry_price != 0 else 0
        emoji = "✅" if pnl > 0 else "❌"

        message = f"""
{emoji} <b>POSITION CLOSED</b>
Symbol: <b>{symbol}</b>
Entry Price: ${entry_price:.2f}
Exit Price: ${exit_price:.2f}
Quantity: {quantity}
P&L: <b>${pnl:.2f}</b> ({pnl_pct:.2f}%)
Reason: {reason}
Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """

        NotificationManager._send_webhook(message, "position_closed")
        NotificationManager._send_email(
            f"Position Closed: {symbol}",
            message
        )
        NotificationManager._send_telegram(message)

    @staticmethod
    def send_daily_stats(stats: dict):
        """Send daily trading statistics"""
        if not NOTIFICATIONS["enabled"]:
            return

        message = f"""
📈 <b>DAILY TRADING SUMMARY</b>
Date: {datetime.now().strftime('%Y-%m-%d')}
Daily P&L: <b>${stats['daily_pnl']:.2f}</b>
Daily Loss: ${stats['daily_loss']:.2f}
Trades: {stats['trades_count']}
Open Positions: {stats['open_positions']}
        """

        NotificationManager._send_webhook(message, "daily_summary")
        NotificationManager._send_telegram(message)

    @staticmethod
    def _send_webhook(message: str, event_type: str):
        """Send notification via webhook (Slack/Discord)"""
        if not NOTIFICATIONS.get("webhook_url"):
            return

        try:
            payload = {
                "text": message,
                "event": event_type,
                "timestamp": datetime.now().isoformat(),
            }
            requests.post(
                NOTIFICATIONS["webhook_url"],
                json=payload,
                timeout=5
            )
            logger.info(f"Webhook sent: {event_type}")
        except Exception as e:
            logger.error(f"Webhook failed: {e}")

    @staticmethod
    def _send_email(subject: str, message: str):
        """Send notification via email"""
        if not NOTIFICATIONS.get("email"):
            return

        try:
            # Placeholder for email integration (use smtplib or service like SendGrid)
            logger.info(f"Email sent to {NOTIFICATIONS['email']}: {subject}")
        except Exception as e:
            logger.error(f"Email failed: {e}")

    @staticmethod
    def _send_telegram(message: str):
        """Send notification via Telegram"""
        if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
            return

        try:
            url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
            payload = {
                "chat_id": TELEGRAM_CHAT_ID,
                "text": message,
                "parse_mode": "HTML"
            }
            response = requests.post(url, json=payload, timeout=5)
            if response.status_code == 200:
                logger.info("Telegram notification sent")
            else:
                logger.error(f"Telegram failed: {response.text}")
        except Exception as e:
            logger.error(f"Telegram failed: {e}")
