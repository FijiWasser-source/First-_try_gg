"""Broker Connection Module - Binance Futures REST API"""
import logging
import requests
import json
import hmac
import hashlib
import time
from urllib.parse import urlencode
from config import BINANCE_API_KEY, BINANCE_API_SECRET, BINANCE_TESTNET

logger = logging.getLogger(__name__)


class BinanceBroker:
    """Binance Futures broker using REST API"""

    def __init__(self):
        self.testnet = BINANCE_TESTNET
        self.base_url = (
            "https://testnet.binancefuture.com" if self.testnet
            else "https://fapi.binance.com"
        )
        self.api_key = BINANCE_API_KEY
        self.api_secret = BINANCE_API_SECRET
        logger.info(f"Connected to Binance Futures ({'testnet' if self.testnet else 'live'})")

    def _sign_request(self, params: dict) -> str:
        """Sign request for authentication"""
        query_string = urlencode(params)
        signature = hmac.new(
            self.api_secret.encode(),
            query_string.encode(),
            hashlib.sha256
        ).hexdigest()
        return f"{query_string}&signature={signature}"

    def _request(self, method: str, endpoint: str, params: dict = None, private: bool = False) -> dict:
        """Make API request"""
        url = f"{self.base_url}{endpoint}"
        headers = {"X-MBX-APIKEY": self.api_key} if private else {}

        try:
            if private:
                params = params or {}
                params["timestamp"] = int(time.time() * 1000)
                signed = self._sign_request(params)
                url = f"{url}?{signed}"
                response = requests.request(method, url, headers=headers, timeout=5)
            else:
                response = requests.request(method, url, params=params, timeout=5)

            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"API Error: {response.status_code} - {response.text}")
                return {}

        except Exception as e:
            logger.error(f"Request failed: {e}")
            return {}

    def get_balance(self) -> dict:
        """Get account balance"""
        response = self._request("GET", "/fapi/v2/account", private=True)
        if response and "totalWalletBalance" in response:
            return {
                "total_balance": float(response["totalWalletBalance"]),
                "available_balance": float(response["availableBalance"])
            }
        return {}

    def get_latest_price(self, symbol: str) -> float:
        """Get latest price"""
        response = self._request("GET", "/fapi/v1/ticker/price", {"symbol": symbol})
        if response and "price" in response:
            return float(response["price"])
        return 0.0

    def place_order(
        self,
        symbol: str,
        side: str,
        order_type: str,
        quantity: float,
        price: float = None,
    ) -> dict:
        """Place order with proper precision"""
        try:
            from config import ASSET_PRECISION

            # Get asset-specific precision
            precision = ASSET_PRECISION.get(symbol, 2)

            # Round quantity to proper precision (Binance requirements)
            if quantity < 0.001:
                return {}

            # Format with exact decimal places to avoid floating-point errors
            quantity = float(f"{quantity:.{precision}f}")

            params = {
                "symbol": symbol,
                "side": side,
                "type": order_type,
                "quantity": quantity,
            }

            if order_type == "LIMIT" and price:
                params["price"] = price
                params["timeInForce"] = "GTC"

            response = self._request("POST", "/fapi/v1/order", params, private=True)

            if response and "orderId" in response:
                logger.info(f"Order placed: {symbol} {side} {quantity}")
                return response
            else:
                logger.error(f"Order failed: {response}")
                return {}

        except Exception as e:
            logger.error(f"Failed to place order: {e}")
            return {}

    def close_position(self, symbol: str, quantity: float, side: str = "SELL") -> dict:
        """Close position"""
        from config import ASSET_PRECISION

        precision = ASSET_PRECISION.get(symbol, 2)
        quantity = float(f"{quantity:.{precision}f}")

        params = {
            "symbol": symbol,
            "side": side,
            "type": "MARKET",
            "quantity": quantity,
        }

        response = self._request("POST", "/fapi/v1/order", params, private=True)

        if response and "orderId" in response:
            logger.info(f"Position closed: {symbol}")
            return response
        else:
            logger.error(f"Close failed: {response}")
            return {}

    def place_sl_tp_orders(
        self,
        symbol: str,
        quantity: float,
        side: str,
        stop_loss: float = None,
        take_profit: float = None,
    ) -> dict:
        """Place Stop Loss and Take Profit as Limit Orders"""
        from config import ASSET_PRECISION

        precision = ASSET_PRECISION.get(symbol, 2)
        quantity = float(f"{quantity:.{precision}f}")
        results = {"sl_order": None, "tp_order": None}

        try:
            import time
            # Determine close side (opposite of entry side)
            close_side = "SELL" if side == "BUY" else "BUY"

            # Place Stop Loss Limit Order
            if stop_loss:
                # Round price to 2 decimals (safe for all crypto pairs)
                sl_price = round(stop_loss, 2)
                sl_params = {
                    "symbol": symbol,
                    "side": close_side,
                    "type": "LIMIT",
                    "quantity": quantity,
                    "price": sl_price,
                    "timeInForce": "GTC"
                }
                logger.debug(f"Placing SL order for {symbol}: qty={quantity}, price={sl_price}, side={close_side}")
                sl_response = self._request("POST", "/fapi/v1/order", sl_params, private=True)
                if sl_response and "orderId" in sl_response:
                    results["sl_order"] = sl_response
                    logger.info(f"Stop Loss Order placed for {symbol} at ${sl_price}")
                else:
                    logger.error(f"SL Order failed for {symbol}: {sl_response}")
                time.sleep(0.5)  # Small delay between orders

            # Place Take Profit Limit Order
            if take_profit:
                # Round price to 2 decimals (safe for all crypto pairs)
                tp_price = round(take_profit, 2)
                tp_params = {
                    "symbol": symbol,
                    "side": close_side,
                    "type": "LIMIT",
                    "quantity": quantity,
                    "price": tp_price,
                    "timeInForce": "GTC"
                }
                logger.debug(f"Placing TP order for {symbol}: qty={quantity}, price={tp_price}, side={close_side}")
                tp_response = self._request("POST", "/fapi/v1/order", tp_params, private=True)
                if tp_response and "orderId" in tp_response:
                    results["tp_order"] = tp_response
                    logger.info(f"Take Profit Order placed for {symbol} at ${tp_price}")
                else:
                    logger.error(f"TP Order failed for {symbol}: {tp_response}")

            return results

        except Exception as e:
            logger.error(f"Failed to place SL/TP orders: {e}")
            return results

    def get_klines(
        self,
        symbol: str,
        interval: str,
        limit: int = 200,
    ) -> list:
        """Get OHLCV candles"""
        params = {
            "symbol": symbol,
            "interval": interval,
            "limit": limit
        }

        response = self._request("GET", "/fapi/v1/klines", params)

        if response and isinstance(response, list):
            return response
        else:
            logger.error(f"No klines for {symbol}")
            return []

    def get_positions(self) -> list:
        """Get open positions"""
        response = self._request("GET", "/fapi/v2/positionRisk", private=True)

        if response and isinstance(response, list):
            return [p for p in response if float(p.get("positionAmt", 0)) != 0]
        else:
            logger.error("Position fetch failed")
            return []
