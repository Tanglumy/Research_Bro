# Research Copilot API Management Scripts

This directory contains bash scripts to manage the Research Copilot backend API server.

## 📋 Quick Start

### Prerequisites

1. **Python 3.10+** installed
2. **Virtual environment** created: `python -m venv spoon-env`
3. **Dependencies** installed: `pip install -r requirements.txt`
4. **API keys** configured in `.env` file

### First-Time Setup

```bash
# 1. Create and activate virtual environment
python3 -m venv spoon-env
source spoon-env/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Create .env file with your API keys
cp .env.example .env  # or let start_api.sh create a template
nano .env  # Edit and add your API keys

# 4. Start the API server
./scripts/start_api.sh
```

## 🚀 Management Scripts

### start_api.sh

**Start the API server**

```bash
./scripts/start_api.sh
```

**Features:**
- ✅ Checks if server is already running
- ✅ Validates environment variables and API keys
- ✅ Creates `.env` template if missing
- ✅ Activates virtual environment
- ✅ Installs/updates dependencies
- ✅ Starts server in background with nohup
- ✅ Saves PID for management
- ✅ Logs to `logs/api.log`

### stop_api.sh

**Stop the running API server**

```bash
./scripts/stop_api.sh
```

**Features:**
- ✅ Graceful shutdown (SIGTERM) with 10-second timeout
- ✅ Force kill (SIGKILL) if needed
- ✅ Cleans up PID file
- ✅ Handles stale PID files

### restart_api.sh

**Restart the API server**

```bash
./scripts/restart_api.sh
```

**Features:**
- ✅ Stops existing server
- ✅ Waits for clean shutdown
- ✅ Starts server with fresh configuration

### status_api.sh

**Check API server status**

```bash
./scripts/status_api.sh
```

**Features:**
- ✅ Shows process information (PID, CPU, Memory)
- ✅ Tests health endpoint
- ✅ Shows recent logs (last 10 lines)
- ✅ Displays API endpoints
- ✅ Shows management commands

## ⚙️ Configuration

### Environment Variables (.env)

The API requires at least one LLM provider API key. Create a `.env` file:

```bash
# LLM Provider API Keys (at least one required)
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
DEEPSEEK_API_KEY=...
GEMINI_API_KEY=...

# Research Tools (optional)
BITQUERY_API_KEY=...
CHAINBASE_API_KEY=...

# Server Configuration (optional)
API_HOST=0.0.0.0
API_PORT=8000
LOG_LEVEL=info  # debug, info, warning, error
```

## 📊 Monitoring

### View Live Logs

```bash
# Follow logs in real-time
tail -f logs/api.log

# View last 100 lines
tail -n 100 logs/api.log

# Search logs for errors
grep ERROR logs/api.log
```

### Check Server Health

```bash
# Using status script
./scripts/status_api.sh

# Using curl
curl http://localhost:8000/health
```

## 🔧 Troubleshooting

### Server Won't Start

**Problem:** Server fails to start

**Solutions:**

1. **Check if port is in use:**
```bash
lsof -ti:8000
kill -9 $(lsof -ti:8000)
```

2. **Check API keys:**
```bash
cat .env | grep API_KEY
```

3. **Check dependencies:**
```bash
source spoon-env/bin/activate
pip install -r requirements.txt
```

4. **Check logs:**
```bash
cat logs/api.log
```

### Server Running But Not Responding

**Solutions:**

1. **Check health endpoint:**
```bash
curl http://localhost:8000/health
```

2. **Restart server:**
```bash
./scripts/restart_api.sh
```

## 🐳 Docker Alternative

For containerized deployment:

```bash
# Build Docker image
docker build -t research-copilot-api .

# Run container
docker run -d \
  -p 8000:8000 \
  --env-file .env \
  --name research-copilot \
  research-copilot-api

# View logs
docker logs -f research-copilot

# Stop container
docker stop research-copilot
```

## 🔐 Security Considerations

### Production Deployment

1. **Use HTTPS:** Deploy behind nginx/traefik with SSL certificates
2. **Restrict access:** Bind to `127.0.0.1` and use reverse proxy
3. **Environment variables:** Never commit `.env` to version control
4. **API keys:** Rotate regularly, use secrets manager in production
5. **Firewall:** Only allow necessary ports (443 for HTTPS)
6. **Process manager:** Use systemd/supervisord instead of nohup in production

### Example Systemd Service

Create `/etc/systemd/system/research-copilot.service`:

```ini
[Unit]
Description=Research Copilot API Server
After=network.target

[Service]
Type=simple
User=your-user
WorkingDirectory=/path/to/Research_Bro
EnvironmentFile=/path/to/Research_Bro/.env
ExecStart=/path/to/Research_Bro/spoon-env/bin/python research_copilot/api.py
Restart=always
RestartSec=10
StandardOutput=append:/path/to/Research_Bro/logs/api.log
StandardError=append:/path/to/Research_Bro/logs/api.log

[Install]
WantedBy=multi-user.target
```

Manage with systemctl:
```bash
sudo systemctl daemon-reload
sudo systemctl enable research-copilot
sudo systemctl start research-copilot
sudo systemctl status research-copilot
```

## 📚 Additional Resources

- **API Documentation:** http://localhost:8000/docs
- **Frontend Integration Guide:** `docs/FRONTEND_INTEGRATION.md`
- **Project README:** `README.md`
- **SpoonOS Documentation:** `spoon-core/doc/`

---

**Last Updated:** November 23, 2024
**Version:** 1.0.0
