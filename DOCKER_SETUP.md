# Docker Setup Guide for Wild Ginger Bot

This guide will help you containerize and deploy the Wild Ginger Telegram Bot using Docker.

## Prerequisites

- Docker installed on your system
- Docker Compose installed
- Google Sheets API credentials
- Telegram Bot Token

## Quick Start

### 1. Setup Environment Variables

Copy the example environment file and configure it:

```bash
cp docker.env.example .env
```

Edit `.env` with your actual values:

```bash
# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN=your_actual_bot_token_here

# Google Sheets Configuration
GOOGLE_SHEETS_SPREADSHEET_ID=your_spreadsheet_id_here
GOOGLE_SHEETS_RANGE=managed!A3:Z1000

# Admin Configuration
ADMIN_USER_IDS=123456789,987654321

# Logging Configuration
LOG_LEVEL=INFO
```

### 2. Setup Google Sheets Credentials

Create a `credentials` directory and place your Google Sheets API credentials:

```bash
mkdir credentials
# Copy your credentials.json file to credentials/credentials.json
```

### 3. Create Logs Directory

```bash
mkdir logs
```

### 4. Build and Run

#### Development Mode
```bash
# Build and run with development settings
docker-compose up --build

# Or run in background
docker-compose up -d --build
```

#### Production Mode
```bash
# Build and run with production settings
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
```

## Docker Commands

### Basic Operations

```bash
# Build the image
docker build -t wild-ginger-bot .

# Run the container
docker run -d --name wild-ginger-bot \
  --env-file .env \
  -v $(pwd)/credentials:/app/credentials:ro \
  -v $(pwd)/logs:/app/logs \
  wild-ginger-bot

# Stop the container
docker stop wild-ginger-bot

# Remove the container
docker rm wild-ginger-bot

# View logs
docker logs wild-ginger-bot

# Follow logs
docker logs -f wild-ginger-bot
```

### Docker Compose Operations

```bash
# Start services
docker-compose up

# Start services in background
docker-compose up -d

# Stop services
docker-compose down

# Rebuild and start
docker-compose up --build

# View logs
docker-compose logs

# Follow logs
docker-compose logs -f

# Restart services
docker-compose restart

# Scale services (if needed)
docker-compose up --scale wild-ginger-bot=2
```

## Development Workflow

### 1. Development Mode with Live Reload

The `docker-compose.override.yml` file is automatically used in development and provides:

- Live code reloading (source code mounted as volume)
- Debug port exposed (5678)
- More generous resource limits
- Debug logging level

### 2. Debugging

To enable debugging, uncomment the debug command in `docker-compose.override.yml`:

```yaml
command: ["python", "-m", "debugpy", "--listen", "0.0.0.0:5678", "run_bot.py"]
```

Then install debugpy in requirements.txt and rebuild:

```bash
echo "debugpy==1.8.0" >> requirements.txt
docker-compose up --build
```

### 3. Testing

```bash
# Run tests in container
docker-compose exec wild-ginger-bot python -m pytest

# Run specific test file
docker-compose exec wild-ginger-bot python -m pytest tests/test_bot.py
```

## Production Deployment

### 1. Production Configuration

Use the production compose file for optimized settings:

```bash
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### 2. Environment Variables for Production

Create a production-specific environment file:

```bash
cp docker.env.example .env.prod
# Edit .env.prod with production values
```

### 3. Docker Swarm (Optional)

For production deployments with multiple instances:

```bash
# Initialize swarm
docker swarm init

# Deploy stack
docker stack deploy -c docker-compose.yml -c docker-compose.prod.yml wild-ginger

# Scale services
docker service scale wild-ginger_wild-ginger-bot=3
```

## Monitoring and Logging

### 1. Health Checks

The container includes health checks that run every 30 seconds:

```bash
# Check container health
docker ps
# Look for "healthy" status

# View health check logs
docker inspect wild-ginger-bot | grep -A 10 "Health"
```

### 2. Logs

Logs are stored in the `./logs` directory and can be viewed with:

```bash
# Docker logs
docker logs wild-ginger-bot

# File logs
tail -f logs/bot.log
```

### 3. Resource Monitoring

```bash
# Monitor resource usage
docker stats wild-ginger-bot

# View container details
docker inspect wild-ginger-bot
```

## Troubleshooting

### Common Issues

1. **Permission Denied on Credentials**
   ```bash
   # Fix file permissions
   chmod 600 credentials/credentials.json
   ```

2. **Container Won't Start**
   ```bash
   # Check logs
   docker logs wild-ginger-bot
   
   # Check environment variables
   docker-compose config
   ```

3. **Google Sheets Authentication Issues**
   ```bash
   # Verify credentials file
   docker-compose exec wild-ginger-bot ls -la /app/credentials/
   
   # Test credentials
   docker-compose exec wild-ginger-bot python -c "
   import json
   with open('/app/credentials/credentials.json') as f:
       print('Credentials file exists and is valid JSON')
   "
   ```

4. **Memory Issues**
   ```bash
   # Increase memory limits in docker-compose.yml
   deploy:
     resources:
       limits:
         memory: 1G
   ```

### Debug Mode

To run in debug mode:

```bash
# Override command for debugging
docker-compose run --rm wild-ginger-bot python -m pdb run_bot.py
```

## Security Considerations

1. **Never commit credentials to version control**
2. **Use secrets management in production**
3. **Run container as non-root user (already configured)**
4. **Use read-only volumes where possible**
5. **Regularly update base images**

## Backup and Recovery

### Backup Data

```bash
# Backup logs
tar -czf logs-backup-$(date +%Y%m%d).tar.gz logs/

# Backup credentials (if needed)
cp -r credentials/ credentials-backup/
```

### Restore

```bash
# Restore logs
tar -xzf logs-backup-YYYYMMDD.tar.gz

# Restore credentials
cp -r credentials-backup/* credentials/
```

## Performance Optimization

1. **Use multi-stage builds for smaller images**
2. **Optimize Python dependencies**
3. **Use Alpine Linux base for smaller footprint**
4. **Implement proper logging rotation**
5. **Monitor resource usage and adjust limits**

## Support

For issues related to:
- Docker setup: Check this guide and Docker documentation
- Bot functionality: Check the main README.md
- Google Sheets integration: Check the CONFIGURATION_GUIDE.md 