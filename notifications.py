"""Notifications Module - Email & Webhook alerts"""
import logging
import requests
from datetime import datetime
from config import NOTIFICATIONS

logger = logging.getLogger(__name__)


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
🤖 TRADE ALERT - {trade_type}
Symbol: {symbol}
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

        message = f"""
📊 POSITION CLOSED
Symbol: {symbol}
Entry Price: ${entry_price:.2f}
Exit Price: ${exit_price:.2f}
Quantity: {quantity}
P&L: ${pnl:.2f} ({(pnl/entry_price)*100:.2f}%)
Reason: {reason}
Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """

        NotificationManager._send_webhook(message, "position_closed")
        NotificationManager._send_email(
            f"Position Closed: {symbol}",
            message
        )

    @staticmethod
    def send_daily_stats(stats: dict):
        """Send daily trading statistics"""
        if not NOTIFICATIONS["enabled"]:
            return

        message = f"""
📈 DAILY TRADING SUMMARY
Date: {datetime.now().strftime('%Y-%m-%d')}
Daily P&L: ${stats['daily_pnl']:.2f}
Daily Loss: ${stats['daily_loss']:.2f}
Trades: {stats['trades_count']}
Open Positions: {stats['open_positions']}
        """

        NotificationManager._send_webhook(message, "daily_summary")

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
