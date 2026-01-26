# Trading Bot with TradingView Webhook Integration

This trading bot connects to Interactive Brokers (IB) and receives webhook signals from TradingView to execute buy/sell orders automatically.

## Prerequisites

1. **Interactive Brokers Account**: Active IB account with TWS or IB Gateway running
2. **Python Environment**: Python 3.7+ with required packages
3. **TradingView Account**: Pro/Pro+ account for webhook alerts
4. **Network Access**: Bot must be accessible from the internet for webhooks

## Installation

1. Install required Python packages:
```bash
pip install flask ib_insync
```

2. Configure your contract settings in the bot file:
```python
exchange="HKFE"        # Your exchange (e.g., "SMART", "NYSE", "NASDAQ")
instructment="MHI"     # Your contract symbol (e.g., "AAPL", "ES", "MHI")
```

## Interactive Brokers Setup

1. **Enable API Access**:
   - Open TWS or IB Gateway
   - Go to File → Global Configuration → API → Settings
   - Check "Enable ActiveX and Socket Clients"
   - Set Socket port to `7497` (paper trading) or `7496` (live trading) or `4002` (IB gateway-paper trading)
   - Add your local IP to "Trusted IPs" if needed

2. **Configure Connection**:
   - The bot connects to `127.0.0.1:4002` with client ID `130`
   - Modify these settings in the bot initialization if needed

## Running the Bot

1. Start your TWS or IB Gateway
2. Run the trading bot:
```bash
python trading_bot_webhooking_simplified_v1.py
```
3. The webhook server will start on `http://0.0.0.0:8000`

## TradingView Webhook Setup

### Step 1: Create Alert in TradingView

1. Open your chart in TradingView
2. Click the "Alert" button (bell icon) or press `Alt + A`
3. Configure your alert conditions (price, indicators, etc.)

### Step 2: Configure Webhook URL

1. In the alert dialog, scroll down to "Notifications"
2. Check "Webhook URL"
3. Enter your webhook URL: `http://YOUR_SERVER_IP:8000/webhook`
   - For local testing: `http://localhost:8000/webhook`
   - For remote server: `http://your-server-ip:8000/webhook`

### Step 3: Set Alert Message

In the "Message" field, use this JSON format:

**For Buy Signal:**
```json
{
  "direction": "long"
}
```

**For Sell Signal:**
```json
{
  "direction": "short"
}
```

### Step 4: Complete Alert Setup

1. Set alert frequency (Once Per Bar Close recommended)
2. Set expiration date
3. Click "Create"

## Webhook Message Format

The bot expects JSON messages with the following structure:

```json
{
  "direction": "long"    // "long" for buy, "short" for sell
}
```

## Bot Behavior

- **New Position**: If no existing position, places market order for 1 contract
- **Existing Position**: If position already exists in the same direction, skips the order
- **Logging**: All actions are logged with timestamps
- **Error Handling**: Connection issues and invalid requests are handled gracefully

## Security Considerations

1. **Firewall**: Only open port 8000 to TradingView's IP ranges if possible
2. **Authentication**: Consider adding API key authentication for production use
3. **HTTPS**: Use HTTPS in production environments
4. **Validation**: The bot validates all incoming webhook data

## Troubleshooting

### Common Issues:

1. **Connection Failed**: 
   - Ensure TWS/IB Gateway is running
   - Check API settings are enabled
   - Verify port numbers match

2. **Webhook Not Received**:
   - Check firewall settings
   - Verify webhook URL is accessible
   - Test with curl: `curl -X POST -H "Content-Type: application/json" -d '{"direction":"long"}' http://localhost:8000/webhook`

3. **Order Not Placed**:
   - Check IB connection status
   - Verify contract qualification
   - Check account permissions and margin

### Testing the Webhook

Test your webhook locally:

```bash
curl -X POST -H "Content-Type: application/json" \
  -d '{"direction":"long"}' \
  http://localhost:8000/webhook
```

## Production Deployment

For production use:

1. **Use a VPS/Cloud Server**: Deploy on AWS, DigitalOcean, etc.
2. **Domain/SSL**: Use a domain with SSL certificate
3. **Process Manager**: Use PM2 or systemd to keep the bot running
4. **Monitoring**: Add logging and monitoring solutions
5. **Backup**: Implement position and trade logging

## Example TradingView Pine Script Alert

```pinescript
//@version=5
strategy("Webhook Example", overlay=true)

// Your strategy logic here
longCondition = ta.crossover(ta.sma(close, 14), ta.sma(close, 28))
shortCondition = ta.crossunder(ta.sma(close, 14), ta.sma(close, 28))

if longCondition
    strategy.entry("Long", strategy.long)
    alert('{"direction": "long"}', alert.freq_once_per_bar_close)

if shortCondition
    strategy.entry("Short", strategy.short)
    alert('{"direction": "short"}', alert.freq_once_per_bar_close)
```

## Support

- Check IB API documentation for contract specifications
- TradingView webhook documentation for advanced features
- Monitor bot logs for debugging information