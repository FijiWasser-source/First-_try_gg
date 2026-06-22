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
        self.lot_size_cache = {}    # symbol -> step size (quantity)
        self.tick_size_cache = {}   # symbol -> tick size (price)
        logger.info(f"Connected to Binance Futures ({'testnet' if self.testnet else 'live'})")
        self.load_exchange_info()

    @staticmethod
    def _decimals_from_step(step: float) -> int:
        """Count the number of decimal places implied by a step/tick size"""
        s = f"{step:.10f}".rstrip("0")
        if "." in s:
            return len(s.split(".")[1])
        return 0

    def load_exchange_info(self):
        """Load exchange info with lot size (qty) and tick size (price) for all pairs"""
        try:
            response = self._request("GET", "/fapi/v1/exchangeInfo")
            if response and "symbols" in response:
                for symbol_info in response["symbols"]:
                    symbol = symbol_info.get("symbol")
                    if not symbol:
                        continue
                    lot_size = 1.0
                    tick_size = 0.01
                    for filter_item in symbol_info.get("filters", []):
                        ftype = filter_item.get("filterType")
                        if ftype == "LOT_SIZE":
                            lot_size = float(filter_item.get("stepSize", 1.0))
                        elif ftype == "PRICE_FILTER":
                            tick_size = float(filter_item.get("tickSize", 0.01))
                    self.lot_size_cache[symbol] = lot_size
                    self.tick_size_cache[symbol] = tick_size
                logger.info(f"Loaded lot/tick size for {len(self.lot_size_cache)} symbols")
            else:
                logger.warning("Failed to load exchange info")
        except Exception as e:
            logger.error(f"Error loading exchange info: {e}")

    def get_lot_size(self, symbol: str) -> float:
        """Get lot size (quantity step size) for a symbol"""
        return self.lot_size_cache.get(symbol, 1.0)

    def get_tick_size(self, symbol: str) -> float:
        """Get tick size (price step size) for a symbol"""
        return self.tick_size_cache.get(symbol, 0.01)

    def format_quantity(self, symbol: str, quantity: float) -> float:
        """Round quantity down to the symbol's lot size and format with correct decimals"""
        step = self.get_lot_size(symbol)
        if step <= 0:
            return quantity
        adjusted = (int(quantity / step)) * step
        adjusted = max(adjusted, step)
        decimals = self._decimals_from_step(step)
        return float(f"{adjusted:.{decimals}f}")

    def format_price(self, symbol: str, price: float) -> float:
        """Round price to the symbol's tick size and format with correct decimals"""
        tick = self.get_tick_size(symbol)
        if tick <= 0:
            return price
        adjusted = round(price / tick) * tick
        decimals = self._decimals_from_step(tick)
        return float(f"{adjusted:.{decimals}f}")

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

            if response.status_code in [200, 201]:
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
        """Place order with exchange-derived quantity and price precision"""
        try:
            if quantity <= 0:
                logger.debug(f"Quantity {quantity} too small for {symbol}")
                return {}

            # Round quantity to lot size and price to tick size (from exchange info)
            quantity = self.format_quantity(symbol, quantity)
            logger.info(
                f"📊 {symbol} {side} {order_type} order: qty={quantity}, lot_size={self.get_lot_size(symbol)}"
            )

            params = {
                "symbol": symbol,
                "side": side,
                "type": order_type,
                "quantity": quantity,
            }

            if order_type == "LIMIT" and price:
                price = self.format_price(symbol, price)
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
        quantity = self.format_quantity(symbol, quantity)

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
        results = {"sl_order": None, "tp_order": None}

        if not stop_loss and not take_profit:
            logger.warning(f"No SL or TP provided for {symbol}")
            return results

        try:
            # Format quantity once for both orders
            quantity = self.format_quantity(symbol, quantity)
            if quantity <= 0:
                logger.error(f"Invalid quantity {quantity} for {symbol}")
                return results

            # Determine close side (opposite of entry side)
            close_side = "SELL" if side == "BUY" else "BUY"

            # Place Stop Loss
            if stop_loss:
                sl_price = self.format_price(symbol, stop_loss)
                sl_params = {
                    "symbol": symbol,
                    "side": close_side,
                    "type": "LIMIT",
                    "quantity": quantity,
                    "price": sl_price,
                    "timeInForce": "GTC"
                }
                logger.info(f"📉 Placing SL: {symbol} {close_side} {quantity} @ {sl_price}")
                sl_response = self._request("POST", "/fapi/v1/order", sl_params, private=True)

                if sl_response and "orderId" in sl_response:
                    results["sl_order"] = sl_response
                    logger.info(f"✅ SL Order {sl_response['orderId']} placed: {symbol} @ ${sl_price}")
                else:
                    logger.error(f"❌ SL Order failed: {sl_response}")

                import time
                time.sleep(0.3)

            # Place Take Profit
            if take_profit:
                tp_price = self.format_price(symbol, take_profit)
                tp_params = {
                    "symbol": symbol,
                    "side": close_side,
                    "type": "LIMIT",
                    "quantity": quantity,
                    "price": tp_price,
                    "timeInForce": "GTC"
                }
                logger.info(f"📈 Placing TP: {symbol} {close_side} {quantity} @ {tp_price}")
                tp_response = self._request("POST", "/fapi/v1/order", tp_params, private=True)

                if tp_response and "orderId" in tp_response:
                    results["tp_order"] = tp_response
                    logger.info(f"✅ TP Order {tp_response['orderId']} placed: {symbol} @ ${tp_price}")
                else:
                    logger.error(f"❌ TP Order failed: {tp_response}")

            return results

        except Exception as e:
            logger.error(f"❌ Failed to place SL/TP orders: {e}")
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
