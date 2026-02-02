from flask import Flask, request
from ib_insync import *
from datetime import datetime, timezone
import asyncio
import threading
import queue
import time
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

############################
exchange="SMART" # Use SMART routing for Hong Kong stocks
instructment="2800" # Tracker Fund of Hong Kong (HK stock)
min_order_size=500 # Minimum order size for HK stock 2800
retry_interval=30 # Retry initialization every 30 seconds if failed
############################

class BotManager:
    def __init__(self):
        self.bot = None
        self.initialization_thread = None
        self.is_initializing = False
        self.last_init_attempt = 0
        
    def get_bot(self):
        """Get the bot instance, trigger initialization if needed"""
        current_time = time.time()
        
        # If bot is None or not connected, and enough time has passed since last attempt
        if (self.bot is None or not self._is_bot_connected()) and \
           (current_time - self.last_init_attempt) > retry_interval and \
           not self.is_initializing:
            
            logger.info("Bot not available, triggering initialization...")
            self._start_initialization()
            
        return self.bot
    
    def _is_bot_connected(self):
        """Check if bot is connected and has a valid contract"""
        try:
            return (self.bot is not None and 
                   self.bot.ib.isConnected() and 
                   self.bot.contract is not None)
        except:
            return False
    
    def _start_initialization(self):
        """Start bot initialization in a separate thread"""
        if self.is_initializing:
            return
            
        self.is_initializing = True
        self.last_init_attempt = time.time()
        
        def init_worker():
            try:
                logger.info("Starting bot initialization...")
                new_bot = TradingBotAsync('127.0.0.1', 4002, 130, min_order_size)
                logger.info("Bot connected to IB successfully")
                
                # Try to set contract
                logger.info(f"Setting contract for {instructment} on {exchange}...")
                new_bot.set_contract(exchange, "STK", instructment)
                
                if new_bot.contract:
                    logger.info(f"✓ Bot initialized successfully with contract: {new_bot.contract}")
                    logger.info(f"✓ Minimum order size set to: {min_order_size} shares")
                    self.bot = new_bot
                else:
                    logger.warning("✗ Warning: Contract not set properly")
                    
            except Exception as e:
                logger.error(f"✗ Error initializing bot: {str(e)}")
                logger.info("Will retry initialization in 30 seconds...")
            finally:
                self.is_initializing = False
        
        self.initialization_thread = threading.Thread(target=init_worker, daemon=True)
        self.initialization_thread.start()

# Global bot manager
bot_manager = BotManager()

class TradingBotAsync:
    def __init__(self, host, port, clientId, min_order_size=500):
        self.host = host
        self.port = port
        self.clientId = clientId
        self.min_order_size = min_order_size
        self.ib = IB()
        self.contract = None
        self.L_log = []
        
        # Queue for communication between threads
        self.command_queue = queue.Queue()
        self.result_queue = queue.Queue()
        
        # Start the async thread
        self.async_thread = threading.Thread(target=self._run_async_loop, daemon=True)
        self.async_thread.start()
        
        # Wait for connection
        time.sleep(2)
        
    def _run_async_loop(self):
        """Run the asyncio event loop in a separate thread"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        async def async_main():
            try:
                # Connect to IB
                await self.ib.connectAsync(self.host, self.port, self.clientId)
                print(f"Connected to IB at {self.host}:{self.port}")
                
                # Process commands from the queue
                while True:
                    try:
                        # Check for commands with timeout
                        try:
                            command = self.command_queue.get(timeout=0.1)
                        except queue.Empty:
                            await asyncio.sleep(0.1)
                            continue
                            
                        if command['action'] == 'set_contract':
                            await self._async_set_contract(command['exchange'], command['secType'], command['symbol'])
                        elif command['action'] == 'test_permissions':
                            result = await self._async_test_permissions()
                            self.result_queue.put(result)
                        elif command['action'] == 'check_position':
                            result = await self._async_check_position(command['direction'], command['contract'])
                            self.result_queue.put(result)
                        elif command['action'] == 'submit_order':
                            result = await self._async_submit_order(command['contract'], command['direction'], command['qty'])
                            self.result_queue.put(result)
                        elif command['action'] == 'stop':
                            break
                            
                    except Exception as e:
                        print(f"Error in async loop: {e}")
                        self.result_queue.put({'error': str(e)})
                        
            except Exception as e:
                print(f"Failed to connect to IB: {e}")
                self.result_queue.put({'error': f'Connection failed: {e}'})
        
        loop.run_until_complete(async_main())
        
    async def _async_set_contract(self, exchange, secType, symbol):
        """Set contract in async context"""
        # For Hong Kong stocks, try different contract formats
        contracts_to_try = [
            # Try with SEHK exchange first
            Stock(symbol, 'SEHK', 'HKD'),
            # Try with SMART routing
            Stock(symbol, 'SMART', 'HKD'),
            # Try with full symbol format (some HK stocks need .HK suffix)
            Stock(f"{symbol}.HK", 'SMART', 'HKD'),
        ]
        
        for i, contract in enumerate(contracts_to_try):
            try:
                print(f"Trying contract {i+1}: {contract.symbol} on {contract.exchange}")
                qualified_contracts = await self.ib.qualifyContractsAsync(contract)
                if qualified_contracts:
                    self.contract = qualified_contracts[0]
                    print(f"✓ Contract qualified successfully: {self.contract}")
                    return
            except Exception as e:
                print(f"✗ Contract {i+1} failed: {e}")
                continue
        
        # If all attempts fail, raise an error
        raise Exception(f"Could not qualify contract for symbol {symbol}. Check market data permissions and symbol format.")
        
    async def _async_test_permissions(self):
        """Test market data permissions"""
        try:
            # Try to get market data for a simple HK stock
            test_contract = Stock('0005', 'SEHK', 'HKD')  # HSBC Holdings
            qualified = await self.ib.qualifyContractsAsync(test_contract)
            if qualified:
                return {'success': 'Market data permissions OK for HK stocks'}
            else:
                return {'error': 'Could not qualify HK test contract'}
        except Exception as e:
            return {'error': f'Market data permission test failed: {e}'}
        
    async def _async_check_position(self, direction, contract):
        """Check position in async context"""
        try:
            positions = self.ib.positions()
            
            for pos in positions:
                if (pos.contract.symbol == contract.symbol and 
                    pos.contract.exchange == contract.exchange and
                    pos.contract.secType == contract.secType):
                    
                    if direction == "long" and pos.position >= self.min_order_size:
                        return True
                    elif direction == "short" and pos.position <= -self.min_order_size:
                        return True
            return False
        except Exception as e:
            return {'error': f'Position check failed: {e}'}
            
    async def _async_submit_order(self, contract, direction, qty):
        """Submit order in async context"""
        try:
            if direction == "long":
                action = "BUY"
            elif direction == "short":
                action = "SELL"
            else:
                return {'error': f'Invalid direction: {direction}'}
                
            # Create market order with proper settings
            order = MarketOrder(action, qty)
            order.tif = 'GTC'  # Good Till Cancelled instead of DAY
            order.outsideRth = True  # Allow outside regular trading hours
            
            trade = self.ib.placeOrder(contract, order)
            
            # Wait a moment for order processing
            await asyncio.sleep(2)
            
            # Check if order was filled or still pending
            if trade.orderStatus.status in ['Filled', 'PartiallyFilled']:
                status_msg = f"Order {trade.orderStatus.status}: {action} {qty} {contract.symbol}"
            elif trade.orderStatus.status == 'Submitted':
                status_msg = f"Order submitted: {action} {qty} {contract.symbol}"
            elif trade.orderStatus.status == 'Cancelled':
                return {'error': f'Order cancelled: {trade.log[-1].message if trade.log else "Unknown reason"}'}
            else:
                status_msg = f"Order status: {trade.orderStatus.status} - {action} {qty} {contract.symbol}"
            
            self.L_log.append([datetime.now(timezone.utc), status_msg])
            print(status_msg)
            
            return {'success': status_msg}
            
        except Exception as e:
            error_msg = f'Order failed: {e}'
            self.L_log.append([datetime.now(timezone.utc), error_msg])
            return {'error': error_msg}
    
    def set_contract(self, exchange, secType, symbol):
        """Thread-safe contract setting"""
        self.command_queue.put({
            'action': 'set_contract',
            'exchange': exchange,
            'secType': secType,
            'symbol': symbol
        })
        time.sleep(3)  # Give more time for contract qualification
        
    def test_market_data_permissions(self):
        """Test if we have market data permissions for HK stocks"""
        self.command_queue.put({
            'action': 'test_permissions'
        })
        
        try:
            result = self.result_queue.get(timeout=10)
            return result
        except queue.Empty:
            return {'error': 'Market data permission test timeout'}
        
    def check_contract_position(self, direction, contract):
        """Thread-safe position checking"""
        self.command_queue.put({
            'action': 'check_position',
            'direction': direction,
            'contract': contract
        })
        
        try:
            result = self.result_queue.get(timeout=10)
            if isinstance(result, dict) and 'error' in result:
                print(f"Position check error: {result['error']}")
                return False
            return result
        except queue.Empty:
            print("Position check timeout")
            return False
            
    def submit_order(self, contract, direction, qty):
        """Thread-safe order submission"""
        self.command_queue.put({
            'action': 'submit_order',
            'contract': contract,
            'direction': direction,
            'qty': qty
        })
        
        try:
            result = self.result_queue.get(timeout=30)
            if isinstance(result, dict):
                if 'error' in result:
                    raise Exception(result['error'])
                elif 'success' in result:
                    return result['success']
            return result
        except queue.Empty:
            raise Exception("Order submission timeout")

# Initialize bot manager and start first initialization attempt
logger.info("Starting bot manager...")
bot_manager._start_initialization()

# Webhook setup
app = Flask(__name__)

@app.route('/test', methods=['GET', 'POST'])
def test():
    if request.method == 'GET':
        return "Webhook server is running! Use POST to /webhook with JSON data."
    else:
        return f"Test POST received. Data: {request.get_data(as_text=True)}"

@app.route('/webhook', methods=['POST'])
def webhook():
    if request.method == 'POST':
        try:
            # Log the raw request data for debugging
            raw_data = request.get_data(as_text=True)
            logger.info(f"Raw webhook data received: {raw_data}")
            logger.info(f"Content-Type: {request.content_type}")
            
            # Try to get JSON data
            message = request.json
            if not message:
                logger.error("Error: No JSON data could be parsed")
                return "Error: No JSON data received or invalid JSON format", 400
            
            logger.info(f"Parsed JSON: {message}")
            
            direction = message.get("direction")
            if not direction:
                logger.error("Error: 'direction' field missing from JSON")
                return "Error: 'direction' field is required", 400
            
            if direction not in ["long", "short"]:
                logger.error(f"Error: Invalid direction value: {direction}")
                return f"Error: Invalid direction '{direction}'. Must be 'long' or 'short'", 400
            
            # Get bot instance (will trigger initialization if needed)
            bot = bot_manager.get_bot()
            if not bot or not bot.contract:
                logger.warning("Bot not initialized or contract not available, will retry soon...")
                return "Bot not ready, initialization in progress. Please try again in a moment.", 503
            
            # Check if position already exists
            position_exists = bot.check_contract_position(direction, bot.contract)
            
            if not position_exists:
                # No existing position, place new order with minimum required size
                result = bot.submit_order(bot.contract, direction, min_order_size)
                success_msg = f"Webhook received: {result}"
                logger.info(success_msg)
                return success_msg
            else:
                # Position already exists
                skip_msg = f"Webhook received: {direction} position already exists, skipping order"
                logger.info(skip_msg)
                return skip_msg
                
        except Exception as e:
            error_msg = f"Error processing webhook: {str(e)}"
            logger.error(error_msg)
            return error_msg, 400

# Run the Flask app
if __name__ == '__main__':
    logger.info("Starting webhook server on port 8000...")
    logger.info("Bot will initialize automatically when IB Gateway becomes available")
    app.run(host='0.0.0.0', port=8000)