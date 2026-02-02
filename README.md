# Trading Bot with TradingView Webhook Integration

This trading bot connects to Interactive Brokers (IB) and receives webhook signals from TradingView to execute buy/sell orders automatically. The bot supports both US and Hong Kong stocks with automatic detection and proper currency handling.

## Features

- **Automatic Stock Detection**: Detects US vs Hong Kong stocks automatically
- **Smart Contract Creation**: Uses appropriate currency (USD/HKD) and exchanges
- **Webhook Integration**: Receives signals from TradingView or other platforms
- **Docker Support**: Fully containerized with environment-based configuration
- **Auto-Retry Logic**: Automatically reconnects when IB Gateway becomes available
- **Position Management**: Prevents duplicate orders for existing positions
- **Flexible Configuration**: All settings configurable via environment variables

## Prerequisites

1. **Interactive Brokers Account**: Active IB account with TWS or IB Gateway running
2. **Docker & Docker Compose**: For containerized deployment (recommended)
3. **TradingView Account**: Pro/Pro+ account for webhook alerts (optional)
4. **Network Access**: Bot must be accessible for webhooks

## Quick Start with Docker (Recommended)

### 1. Clone and Configure

```bash
git clone https://github.com/MorganiMix/IB-simple-webhook
cd trading-bot
cp .env.example .env
```

### 2. Edit Configuration

Edit `.env` file:

```bash
# Stock/Contract Settings
EXCHANGE=SMART
INSTRUMENT=AAPL
ORDER_SIZE=1

# For Hong Kong stocks, use:
# INSTRUMENT=2800
# ORDER_SIZE=500

# Interactive Brokers Connection
IB_HOST=127.0.0.1
IB_PORT=4002
CLIENT_ID=130

# Bot Settings
RETRY_INTERVAL=30
WEBHOOK_PORT=8001
```

### 3. Start Interactive Brokers

- Start TWS or IB Gateway
- Enable API access (see IB Setup section below)

### 4. Run the Bot

```bash
# Build and start
docker-compose up --build

# Or run in background
docker-compose up -d --build

# View logs
docker-compose logs -f
```

## Configuration

### Environment Variables

All bot settings are configurable via the `.env` file:

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `EXCHANGE` | Exchange routing | `SMART` | `SMART`, `SEHK`, `NASDAQ` |
| `INSTRUMENT` | Stock symbol to trade | `AAPL` | `AAPL`, `2800`, `MSFT` |
| `ORDER_SIZE` | Order size in shares | `1` | `1`, `500`, `100` |
| `IB_HOST` | IB Gateway/TWS host | `127.0.0.1` | `127.0.0.1` |
| `IB_PORT` | IB Gateway/TWS port | `4002` | `4002`, `4001`, `7496`, `7497` |
| `CLIENT_ID` | Unique client ID | `130` | `130`, `131`, `132` |
| `RETRY_INTERVAL` | Retry connection every N seconds | `30` | `30`, `60` |
| `WEBHOOK_PORT` | Port for webhook server | `8001` | `8001`, `8000`, `9000` |

### Stock Type Detection

The bot automatically detects whether you're trading US or Hong Kong stocks:

**US Stocks (USD currency):**
- Alphabetic symbols: AAPL, MSFT, GOOGL
- Uses USD currency and US exchanges (SMART, NASDAQ, NYSE)
- Typical order size: 1 share

**Hong Kong Stocks (HKD currency):**
- Numeric symbols: 2800, 0005, 0700
- Symbols ending in .HK: 2800.HK
- Uses HKD currency and Hong Kong exchanges (SEHK, SMART)
- Typical order size: 100-500 shares (board lots)

### Common IB Port Settings:
- **IB Gateway Paper Trading**: 4002
- **IB Gateway Live Trading**: 4001  
- **TWS Paper Trading**: 7496
- **TWS Live Trading**: 7497

### Changing the Webhook Port

To use a different port (e.g., 9000), update your `.env` file:

```bash
WEBHOOK_PORT=9000
```

Then rebuild and restart:

```bash
docker-compose down
docker-compose up --build
```

The container will automatically:
- Build with the new port exposed
- Map the correct host port to container port
- Update health checks to use the new port

## Interactive Brokers Setup

### 1. Enable API Access

**For TWS (Trader Workstation):**
1. Open TWS
2. Go to File → Global Configuration → API → Settings
3. Check "Enable ActiveX and Socket Clients"
4. Set Socket port to `7497` (live) or `7496` (paper)
5. Add your local IP to "Trusted IPs" if needed

**For IB Gateway:**
1. Open IB Gateway
2. Configure API settings
3. Set port to `4001` (live) or `4002` (paper)
4. Enable API connections

### 2. Configure Connection

Update your `.env` file with the correct port:

```bash
# For IB Gateway Paper Trading
IB_PORT=4002

# For IB Gateway Live Trading  
IB_PORT=4001

# For TWS Paper Trading
IB_PORT=7496

# For TWS Live Trading
IB_PORT=7497
```

## Docker Deployment

### Using Docker Compose (Recommended)

```bash
# Build and start the container
docker-compose up --build

# Run in background
docker-compose up -d --build

# View logs
docker-compose logs -f

# Stop the container
docker-compose down
```

### Using Docker directly

```bash
# Build the image with custom port
docker build --build-arg WEBHOOK_PORT=8001 -t trading-bot .

# Run the container with environment file
docker run --env-file .env -p 8001:8001 --network host trading-bot

# Or build and run with different port
docker build --build-arg WEBHOOK_PORT=9000 -t trading-bot .
docker run --env-file .env -p 9000:9000 --network host trading-bot
```

## Manual Installation (Alternative)

If you prefer not to use Docker:

### 1. Install Python Dependencies

```bash
pip install flask ib_insync python-dotenv tzdata
```

### 2. Run the Bot

```bash
python trading_bot_webhooking_v2.py
```

## TradingView Webhook Setup

### Step 1: Create Alert in TradingView

1. Open your chart in TradingView
2. Click the "Alert" button (bell icon) or press `Alt + A`
3. Configure your alert conditions (price, indicators, etc.)

### Step 2: Configure Webhook URL

1. In the alert dialog, scroll down to "Notifications"
2. Check "Webhook URL"
3. Enter your webhook URL: `http://YOUR_SERVER_IP:8001/webhook`
   - For local testing: `http://localhost:8001/webhook`
   - For remote server: `http://your-server-ip:8001/webhook`

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

## Testing the Webhook

Once running, test the webhook endpoints:

```bash
# Test GET endpoint
curl http://localhost:8001/test

# Test webhook with long position
curl -X POST http://localhost:8001/webhook \
  -H "Content-Type: application/json" \
  -d '{"direction": "long"}'

# Test webhook with short position
curl -X POST http://localhost:8001/webhook \
  -H "Content-Type: application/json" \
  -d '{"direction": "short"}'
```

## Bot Behavior

- **New Position**: If no existing position, places market order for specified quantity
- **Existing Position**: If position already exists in the same direction, skips the order
- **Auto-Retry**: Automatically retries IB connection if Gateway becomes unavailable
- **Logging**: All actions are logged with timestamps
- **Error Handling**: Connection issues and invalid requests are handled gracefully

## Important Notes

- **Network Mode**: Uses `host` networking to connect to IB on localhost
- **Environment Configuration**: All settings are configurable via `.env` file
- **Health Check**: Automatically checks if the service is responding
- **Restart Policy**: Container restarts unless manually stopped
- **Auto-Retry**: Bot automatically retries connection if IB Gateway is unavailable

## Troubleshooting

### Common Issues:

1. **Connection Issues**: 
   - Ensure IB TWS/Gateway is running and API is enabled
   - Check `IB_PORT` and `CLIENT_ID` in `.env`
   - Verify port numbers match your IB setup

2. **Port Conflicts**: 
   - Check `WEBHOOK_PORT` in `.env`
   - Ensure the port is not used by other services

3. **Contract Not Found**:
   - Verify the stock symbol in `INSTRUMENT`
   - Check market data permissions for the stock
   - Ensure you have the right to trade the instrument

4. **Order Size Issues**:
   - US stocks: typically 1 share minimum
   - HK stocks: typically 100-500 shares (board lots)
   - Check your account's buying power

5. **Webhook Not Received**:
   - Check firewall settings
   - Verify webhook URL is accessible from internet
   - Test locally first with curl commands

### Debugging Steps:

1. **Check Logs**:
   ```bash
   docker-compose logs -f trading-bot
   ```

2. **Test IB Connection**:
   - Verify TWS/Gateway is running
   - Check API settings are enabled
   - Try connecting with a different client ID

3. **Test Webhook Locally**:
   ```bash
   curl -X POST -H "Content-Type: application/json" \
     -d '{"direction":"long"}' \
     http://localhost:8001/webhook
   ```

## Security Considerations

1. **Firewall**: Only open webhook port to trusted IPs if possible
2. **Authentication**: Consider adding API key authentication for production
3. **HTTPS**: Use HTTPS in production environments
4. **Validation**: The bot validates all incoming webhook data
5. **Environment Variables**: Keep `.env` file secure and never commit it

## Production Deployment

For production use:

1. **Use a VPS/Cloud Server**: Deploy on AWS, DigitalOcean, etc.
2. **Domain/SSL**: Use a domain with SSL certificate
3. **Process Manager**: Docker Compose handles restarts automatically
4. **Monitoring**: Monitor container logs and health checks
5. **Backup**: Implement position and trade logging
6. **Security**: Use proper firewall rules and authentication

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

## Configuration Examples

### For US Stocks (AAPL)
```bash
EXCHANGE=SMART
INSTRUMENT=AAPL
ORDER_SIZE=1
```

### For Hong Kong Stocks (2800)
```bash
EXCHANGE=SMART
INSTRUMENT=2800
ORDER_SIZE=500
```

### For Live Trading
```bash
IB_PORT=4001  # Gateway Live
# or
IB_PORT=7497  # TWS Live
```

## Logs

Container logs will show:
- IB connection status
- Webhook requests
- Order submissions
- Configuration values
- Any errors

View logs with: `docker-compose logs -f trading-bot`

## Support

- Check IB API documentation for contract specifications
- TradingView webhook documentation for advanced features
- Monitor bot logs for debugging information
- Interactive Brokers support for account and API issues

## License

This project is provided as-is for educational and personal use. Please ensure compliance with your broker's terms of service and applicable regulations when using automated trading systems.
