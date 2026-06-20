"""Broker Connection Module - ByBit API"""
import logging
from pybit.unified_trading import HTTP
from config import BYBIT_API_KEY, BYBIT_API_SECRET, BYBIT_TESTNET

logger = logging.getLogger(__name__)


class ByBitBroker:
    """ByBit broker connection and order management"""

    def __init__(self):
        self.testnet = BYBIT_TESTNET
        self.client = HTTP(
            testnet=self.testnet,
            api_key=BYBIT_API_KEY,
            api_secret=BYBIT_API_SECRET,
        )
        logger.info(f"Connected to ByBit ({'testnet' if self.testnet else 'live'})")

    def get_balance(self) -> dict:
        """Get account balance"""
        try:
            response = self.client.get_wallet_balance(
                accountType="UNIFIED"
            )
            return response.get("result", {})
        except Exception as e:
            logger.error(f"Failed to get balance: {e}")
            return {}

    def get_latest_price(self, symbol: str) -> float:
        """Get latest price for symbol"""
        try:
            response = self.client.get_tickers(
                category="linear",
                symbol=symbol
            )
            if response["retCode"] == 0 and response["result"]["list"]:
                return float(response["result"]["list"][0]["lastPrice"])
        except Exception as e:
            logger.error(f"Failed to get price for {symbol}: {e}")
        return 0.0

    def place_order(
        self,
        symbol: str,
        side: str,
        order_type: str,
        qty: float,
        price: float = None,
    ) -> dict:
        """Place an order (LONG or SHORT)"""
        try:
            params = {
                "category": "linear",
                "symbol": symbol,
                "side": side,  # "Buy" or "Sell"
                "orderType": order_type,  # "Market" or "Limit"
                "qty": str(qty),
            }

            if order_type == "Limit" and price:
                params["price"] = str(price)

            response = self.client.place_order(**params)

            if response["retCode"] == 0:
                logger.info(f"Order placed: {symbol} {side} {qty}")
                return response.get("result", {})
            else:
                logger.error(f"Order failed: {response['retMsg']}")
                return {}

        except Exception as e:
            logger.error(f"Failed to place order: {e}")
            return {}

    def close_position(
        self,
        symbol: str,
        qty: float,
        side: str = "Sell",
    ) -> dict:
        """Close a position"""
        try:
            response = self.client.place_order(
                category="linear",
                symbol=symbol,
                side=side,
                orderType="Market",
                qty=str(qty),
                reduceOnly=True,
            )

            if response["retCode"] == 0:
                logger.info(f"Position closed: {symbol}")
                return response.get("result", {})
            else:
                logger.error(f"Close failed: {response['retMsg']}")
                return {}

        except Exception as e:
            logger.error(f"Failed to close position: {e}")
            return {}

    def set_stop_loss_take_profit(
        self,
        symbol: str,
        stop_loss: float,
        take_profit: float,
    ) -> dict:
        """Set stop loss and take profit for a position"""
        try:
            response = self.client.set_trading_stop(
                category="linear",
                symbol=symbol,
                stopLoss=str(stop_loss),
                takeProfit=str(take_profit),
                tpslMode="Partial",
            )

            if response["retCode"] == 0:
                logger.info(f"SL/TP set for {symbol}")
                return response.get("result", {})
            else:
                logger.error(f"SL/TP failed: {response['retMsg']}")
                return {}

        except Exception as e:
            logger.error(f"Failed to set SL/TP: {e}")
            return {}

    def get_klines(
        self,
        symbol: str,
        interval: str,
        limit: int = 200,
    ) -> list:
        """Get OHLCV candle data"""
        try:
            response = self.client.get_kline(
                category="linear",
                symbol=symbol,
                interval=interval,
                limit=limit,
            )

            if response["retCode"] == 0:
                return response.get("result", {}).get("list", [])
            else:
                logger.error(f"Kline fetch failed: {response['retMsg']}")
                return []

        except Exception as e:
            logger.error(f"Failed to get klines: {e}")
            return []

    def get_positions(self) -> list:
        """Get open positions"""
        try:
            response = self.client.get_positions(
                category="linear"
            )

            if response["retCode"] == 0:
                return response.get("result", {}).get("list", [])
            else:
                logger.error(f"Position fetch failed: {response['retMsg']}")
                return []

        except Exception as e:
            logger.error(f"Failed to get positions: {e}")
            return []
