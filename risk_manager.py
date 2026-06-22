"""Risk Management Module"""
import logging
from datetime import datetime
from config import RISK_MANAGEMENT

logger = logging.getLogger(__name__)


class RiskManager:
    """Manage trading risk and position sizing"""

    def __init__(self):
        self.daily_pnl = 0.0
        self.daily_loss = 0.0
        self.open_positions = 0
        self.trades_today = []
        self.session_start = datetime.now()

    def reset_daily_stats(self):
        """Reset daily statistics (call at market open)"""
        self.daily_pnl = 0.0
        self.daily_loss = 0.0
        self.open_positions = 0
        self.trades_today = []
        self.session_start = datetime.now()

    def can_open_position(self) -> bool:
        """Check if we can open a new position"""
        checks = [
            self.open_positions < RISK_MANAGEMENT["max_open_positions"],
            self.daily_loss < RISK_MANAGEMENT["max_daily_loss"],
            self.daily_pnl < RISK_MANAGEMENT["max_daily_profit"],
        ]

        if not all(checks):
            logger.warning(
                f"Position blocked. Open: {self.open_positions}, "
                f"Daily Loss: ${self.daily_loss:.2f}, Daily PnL: ${self.daily_pnl:.2f}"
            )
            return False

        return True

    def calculate_position_size(self, entry_price: float, stop_loss: float) -> float:
        """Calculate position size based on 1% risk rule, adjusted for leverage"""
        from config import MAX_RISK_PER_TRADE, ASSET_PRECISION

        # Risk amount per trade
        risk_amount = MAX_RISK_PER_TRADE  # $50

        # Adjust risk for leverage (divide by leverage to maintain 1% actual risk)
        leverage = RISK_MANAGEMENT.get("leverage", 1)
        adjusted_risk = risk_amount / leverage

        # Calculate distance to stop loss
        sl_distance = abs(entry_price - stop_loss)

        if sl_distance == 0:
            sl_distance = entry_price * 0.015  # Default 1.5% if no SL

        # Position size = Adjusted Risk / Distance per unit
        quantity = adjusted_risk / sl_distance

        # Round with extra precision to avoid floating-point errors
        quantity = round(quantity, 6)
        return quantity

    def calculate_stop_loss(self, entry_price: float, side: str = "LONG") -> float:
        """Calculate stop loss price"""
        sl_pct = RISK_MANAGEMENT["stop_loss_pct"] / 100
        if side == "LONG":
            return entry_price * (1 - sl_pct)
        else:  # SHORT
            return entry_price * (1 + sl_pct)

    def calculate_take_profit(self, entry_price: float, side: str = "LONG") -> float:
        """Calculate take profit price"""
        tp_pct = RISK_MANAGEMENT["take_profit_pct"] / 100
        if side == "LONG":
            return entry_price * (1 + tp_pct)
        else:  # SHORT
            return entry_price * (1 - tp_pct)

    def update_pnl(self, pnl: float):
        """Update daily P&L"""
        self.daily_pnl += pnl
        if pnl < 0:
            self.daily_loss += abs(pnl)

    def on_position_opened(self):
        """Track when position is opened"""
        self.open_positions += 1

    def on_position_closed(self, pnl: float):
        """Track when position is closed"""
        self.open_positions = max(0, self.open_positions - 1)
        self.update_pnl(pnl)
        self.trades_today.append(
            {"timestamp": datetime.now(), "pnl": pnl}
        )

    def get_daily_stats(self) -> dict:
        """Get current daily trading statistics"""
        return {
            "daily_pnl": self.daily_pnl,
            "daily_loss": self.daily_loss,
            "open_positions": self.open_positions,
            "trades_count": len(self.trades_today),
            "max_daily_loss_limit": RISK_MANAGEMENT["max_daily_loss"],
            "max_daily_profit_limit": RISK_MANAGEMENT["max_daily_profit"],
        }
