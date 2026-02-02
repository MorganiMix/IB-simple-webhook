# Trading Bot Docker Setup

## Prerequisites

1. **Interactive Brokers TWS/Gateway**: Must be running on your host machine
   - TWS: Usually runs on port 7497 (live) or 7496 (paper)
   - Gateway: Usually runs on port 4001 (live) or 4002 (paper)
   - Enable API connections in TWS/Gateway settings

2. **Docker and Docker Compose**: Installed on your system

## Configuration

### Environment Variables

Copy the example environment file and customize it:

```bash
cp .env.example .env
```

Edit `.env` to configure your trading bot:

```bash
# Stock/Contract Settings
EXCHANGE=SMART              # Exchange routing (SMART, SEHK, etc.)
INSTRUMENT=2800             # Stock symbol to trade
ORDER_SIZE=500              # Order size (shares)

# Interactive Brokers Connection
IB_HOST=127.0.0.1          # IB Gateway/TWS host
IB_PORT=4002               # IB Gateway/TWS port
CLIENT_ID=130              # Unique client ID

# Bot Settings
RETRY_INTERVAL=30          # Retry connection every N seconds
WEBHOOK_PORT=8001          # Port for webhook server
```

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

### Common IB Port Settings:
- **IB Gateway Paper Trading**: 4002
- **IB Gateway Live Trading**: 4001  
- **TWS Paper Trading**: 7496
- **TWS Live Trading**: 7497

## Build and Run

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

## Important Notes

- **Network Mode**: Uses `host` networking to connect to IB on localhost
- **Environment Configuration**: All settings are configurable via `.env` file
- **Health Check**: Automatically checks if the service is responding
- **Restart Policy**: Container restarts unless manually stopped
- **Auto-Retry**: Bot automatically retries connection if IB Gateway is unavailable

## Troubleshooting

1. **Connection Issues**: Ensure IB TWS/Gateway is running and API is enabled
2. **Port Conflicts**: Check `WEBHOOK_PORT` and `IB_PORT` in `.env`
3. **Client ID**: Use a unique `CLIENT_ID` (avoid conflicts with other connections)
4. **Permissions**: Ensure Docker has necessary permissions and market data is enabled

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