"""Broker Connection Module - Binance Futures API"""
import logging
from binance.cm_futures import CMFutures
from binance.um_futures import UMFutures
from config import BINANCE_API_KEY, BINANCE_API_SECRET, BINANCE_TESTNET

logger = logging.getLogger(__name__)


class BinanceBroker:
    """Binance Futures broker connection and order management"""

    def __init__(self):
        self.testnet = BINANCE_TESTNET

        if self.testnet:
            self.client = UMFutures(
                key=BINANCE_API_KEY,
                secret=BINANCE_API_SECRET,
                base_url="https://testnet.binancefuture.com"
            )
        else:
            self.client = UMFutures(
                key=BINANCE_API_KEY,
                secret=BINANCE_API_SECRET
            )

        logger.info(f"Connected to Binance Futures ({'testnet' if self.testnet else 'live'})")

    def get_balance(self) -> dict:
        """Get account balance"""
        try:
            response = self.client.account()
            total_balance = float(response.get("totalWalletBalance", 0))
            available_balance = float(response.get("availableBalance", 0))
            return {
                "total_balance": total_balance,
                "available_balance": available_balance
            }
        except Exception as e:
            logger.error(f"Failed to get balance: {e}")
            return {}

    def get_latest_price(self, symbol: str) -> float:
        """Get latest price for symbol"""
        try:
            ticker = self.client.ticker_price(symbol=symbol)
            return float(ticker["price"])
        except Exception as e:
            logger.error(f"Failed to get price for {symbol}: {e}")
            return 0.0

    def place_order(
        self,
        symbol: str,
        side: str,
        order_type: str,
        quantity: float,
        price: float = None,
    ) -> dict:
        """Place an order"""
        try:
            params = {
                "symbol": symbol,
                "side": side,  # "BUY" or "SELL"
                "type": order_type,  # "MARKET" or "LIMIT"
                "quantity": quantity,
            }

            if order_type == "LIMIT" and price:
                params["price"] = price
                params["timeInForce"] = "GTC"

            response = self.client.new_order(**params)

            if response and "orderId" in response:
                logger.info(f"Order placed: {symbol} {side} {quantity}")
                return response
            else:
                logger.error(f"Order failed: {response}")
                return {}

        except Exception as e:
            logger.error(f"Failed to place order: {e}")
            return {}

    def close_position(
        self,
        symbol: str,
        quantity: float,
        side: str = "SELL",
    ) -> dict:
        """Close a position"""
        try:
            response = self.client.new_order(
                symbol=symbol,
                side=side,
                type="MARKET",
                quantity=quantity,
            )

            if response and "orderId" in response:
                logger.info(f"Position closed: {symbol}")
                return response
            else:
                logger.error(f"Close failed: {response}")
                return {}

        except Exception as e:
            logger.error(f"Failed to close position: {e}")
            return {}

    def set_stop_loss_take_profit(
        self,
        symbol: str,
        stop_loss: float = None,
        take_profit: float = None,
    ) -> bool:
        """Set stop loss and take profit for a position"""
        try:
            if stop_loss:
                self.client.new_order(
                    symbol=symbol,
                    side="SELL",
                    type="STOP_MARKET",
                    stopPrice=stop_loss,
                    closePosition=True,
                )
                logger.info(f"Stop Loss set for {symbol} at {stop_loss}")

            if take_profit:
                self.client.new_order(
                    symbol=symbol,
                    side="SELL",
                    type="TAKE_PROFIT_MARKET",
                    stopPrice=take_profit,
                    closePosition=True,
                )
                logger.info(f"Take Profit set for {symbol} at {take_profit}")

            return True

        except Exception as e:
            logger.error(f"Failed to set SL/TP: {e}")
            return False

    def get_klines(
        self,
        symbol: str,
        interval: str,
        limit: int = 200,
    ) -> list:
        """Get OHLCV candle data"""
        try:
            klines = self.client.klines(
                symbol=symbol,
                interval=interval,
                limit=limit
            )

            if klines:
                return klines
            else:
                logger.error(f"No klines for {symbol}")
                return []

        except Exception as e:
            logger.error(f"Failed to get klines: {e}")
            return []

    def get_positions(self) -> list:
        """Get open positions"""
        try:
            positions = self.client.get_position_risk()

            if positions:
                return [p for p in positions if float(p.get("positionAmt", 0)) != 0]
            else:
                logger.error("Position fetch failed")
                return []

        except Exception as e:
            logger.error(f"Failed to get positions: {e}")
            return []
