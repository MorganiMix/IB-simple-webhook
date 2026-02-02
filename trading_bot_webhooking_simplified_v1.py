from flask import Flask, request
from ib_insync import *
from datetime import datetime, timezone
import asyncio
import threading
from concurrent.futures import ThreadPoolExecutor
import time
############################
exchange="NASDAQ" # exchange of the contract
instructment="AAPL" # contract of the trade
############################

class TradingBot:
    def __init__(self, host, port, clientId):
        self.L_log=[]
        self.L_log_summary=[]
        self.L_performance_summary=[]
        self.L_orders=None
        self.L_positions=None
        self.ib = IB()
        self.host = host
        self.port = port
        self.clientId = clientId
        self.contract = None
        self.data=None
        self.count_bar=0
        self.second_count=0
        self.df=None
        self.bar_index=0
        
        # Connect in the main thread
        self._connect()

    def _connect(self):
        """Connect to IB in the current thread"""
        try:
            self.ib.connect(self.host, self.port, self.clientId)
            print(f"Connected to IB at {self.host}:{self.port}")
        except Exception as e:
            print(f"Failed to connect to IB: {e}")
            raise

    def set_contract(self, exchange, secType, symbol):
        self.contract = Contract(exchange=exchange, secType=secType, symbol=symbol)
        self.ib.qualifyContracts(self.contract)
        
    def _ensure_connection(self):
        """Ensure IB connection is active, reconnect if needed"""
        if not self.ib.isConnected():
            print("IB connection lost, attempting to reconnect...")
            try:
                self.ib.connect(self.host, self.port, self.clientId)
                print("Reconnected to IB successfully")
            except Exception as e:
                print(f"Failed to reconnect: {e}")
                raise ConnectionError("Could not establish IB connection")
   
    # Check if there is long or short position in the contract
    def check_contract_position(self,direction,contract):  
        result=False
        try:
            self._ensure_connection()
            
            positions = self.ib.positions()
            if direction=="long":
                for pos in positions:
                    # Compare contracts by key attributes (symbol, exchange, secType)
                    if (pos.contract.symbol == contract.symbol and 
                        pos.contract.exchange == contract.exchange and
                        pos.contract.secType == contract.secType and
                        pos.position >= 1):
                        result=True
                        return result
            elif direction=="short":
                for pos in positions:
                    # Compare contracts by key attributes (symbol, exchange, secType)
                    if (pos.contract.symbol == contract.symbol and 
                        pos.contract.exchange == contract.exchange and
                        pos.contract.secType == contract.secType and
                        pos.position <= -1):
                        result=True
                        return result    
        except Exception as e:
            self.L_log.append([datetime.now(timezone.utc), f"Error checking position: {str(e)}"])
            print(f"Error checking position: {str(e)}")
        return(result)    
        
    # place market order
    def submit_order(self,contract1,direction,qty):
        try:
            self._ensure_connection()
            
            contract=contract1
            if direction=="long":
                direction1="BUY"
            elif direction=="short":
                direction1="SELL"
            else:
                raise ValueError(f"Invalid direction: {direction}. Must be 'long' or 'short'")
            
            if qty <= 0:
                raise ValueError(f"Quantity must be positive, got {qty}")
            
            order = MarketOrder(direction1, qty)
            trade = self.ib.placeOrder(contract, order)
            
            # Wait a moment for the order to be processed
            self.ib.sleep(1)
            
            self.L_log.append([datetime.now(timezone.utc), "direction:",direction,"quantity:",qty, "order placed"])
            print(f"Order placed: {direction1} {qty} of {contract.symbol}")
            return trade
        except Exception as e:
            error_msg = f"Error placing order: {str(e)}"
            self.L_log.append([datetime.now(timezone.utc), error_msg])
            print(error_msg)
            raise
    
 
# Global executor for thread-safe operations
executor = ThreadPoolExecutor(max_workers=1)

def safe_execute_trade(direction, contract, qty):
    """Execute trade in a thread-safe manner"""
    try:
        # Check position first
        position_exists = bot.check_contract_position(direction, contract)
        
        if not position_exists:
            # Place order
            bot.submit_order(contract, direction, qty)
            return f"Order submitted: {direction} {qty} shares of {contract.symbol}"
        else:
            return f"Position already exists: {direction} for {contract.symbol}, skipping order"
    except Exception as e:
        raise Exception(f"Trade execution failed: {str(e)}")

# Initialize bot
try:
    bot = TradingBot('127.0.0.1',7497,130)
    bot.set_contract(exchange, "STK", instructment)
    print("Bot initialized and contract set successfully")
except Exception as e:
    print(f"Error initializing bot: {str(e)}")
    raise



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
            print(f"Raw webhook data received: {raw_data}")
            print(f"Content-Type: {request.content_type}")
            
            # Try to get JSON data
            message = request.json
            if not message:
                print("Error: No JSON data could be parsed")
                return "Error: No JSON data received or invalid JSON format", 400
            
            print(f"Parsed JSON: {message}")
            
            direction = message.get("direction")
            if not direction:
                print("Error: 'direction' field missing from JSON")
                return "Error: 'direction' field is required", 400
            
            if direction not in ["long", "short"]:
                print(f"Error: Invalid direction value: {direction}")
                return f"Error: Invalid direction '{direction}'. Must be 'long' or 'short'", 400
            
            # Use the bot's contract instead of string from message
            # If you need to support multiple contracts, you'd need to create/qualify them here
            contract = bot.contract
            if not contract:
                print("Error: Bot contract not initialized")
                return "Error: Bot contract not initialized", 500
            
            # Execute trade in thread-safe manner
            try:
                # Submit to executor and wait for result with timeout
                future = executor.submit(safe_execute_trade, direction, contract, 1)
                result = future.result(timeout=30)  # 30 second timeout
                print(result)
                return result
            except Exception as e:
                error_msg = f"Trade execution error: {str(e)}"
                print(error_msg)
                return error_msg, 400
        except Exception as e:
            error_msg = f"Error processing webhook: {str(e)}"
            print(error_msg)
            return error_msg, 400

        
# Run the Flask app
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8001)