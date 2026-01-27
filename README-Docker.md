# Trading Bot Docker Setup

## Prerequisites

1. **Interactive Brokers TWS/Gateway**: Must be running on your host machine
   - TWS: Usually runs on port 7497 (live) or 7496 (paper)
   - Gateway: Usually runs on port 4001 (live) or 4002 (paper)
   - Enable API connections in TWS/Gateway settings

2. **Docker and Docker Compose**: Installed on your system

## Configuration

Before running, update the connection settings in `trading_bot_webhooking_v2.py`:

```python
# Update these lines based on your IB setup
bot = TradingBotAsync('127.0.0.1', 4002, 130)  # host, port, clientId
exchange = "SEHK"  # Hong Kong Stock Exchange
instructment = "2800"  # Tracker Fund of Hong Kong
```

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
# Build the image
docker build -t trading-bot .

# Run the container
docker run -p 8000:8000 --network host trading-bot
```

## Testing the Webhook

Once running, test the webhook endpoints:

```bash
# Test GET endpoint
curl http://localhost:8000/test

# Test webhook with long position
curl -X POST http://localhost:8000/webhook \
  -H "Content-Type: application/json" \
  -d '{"direction": "long"}'

# Test webhook with short position
curl -X POST http://localhost:8000/webhook \
  -H "Content-Type: application/json" \
  -d '{"direction": "short"}'
```

## Important Notes

- **Network Mode**: Uses `host` networking to connect to IB on localhost
- **Port 8000**: Webhook server runs on this port
- **Health Check**: Automatically checks if the service is responding
- **Restart Policy**: Container restarts unless manually stopped

## Troubleshooting

1. **Connection Issues**: Ensure IB TWS/Gateway is running and API is enabled
2. **Port Conflicts**: Make sure port 8000 is available
3. **Client ID**: Use a unique client ID (130 in the example)
4. **Permissions**: Ensure Docker has necessary permissions

## Logs

Container logs will show:
- IB connection status
- Webhook requests
- Order submissions
- Any errors

View logs with: `docker-compose logs -f trading-bot`