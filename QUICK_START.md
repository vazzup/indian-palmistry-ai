# 🚀 PalmistTalk - Quick Start Guide

## One-Command Startup

To start the entire application with all services:

```bash
./start.sh
```

That's it! The script will:
- ✅ Check prerequisites (Docker, Node.js)
- ✅ Start backend services (API, Redis, Worker)
- ✅ Run database migrations
- ✅ Start frontend application
- ✅ Verify all services are healthy

## 📱 Access the Application

Once started, open your browser and go to:
**http://localhost:3000**

## 🛠️ Management Commands

| Command | Description |
|---------|-------------|
| `./start.sh` | Start all services |
| `./stop.sh` | Stop all services |
| `./restart.sh` | Restart all services |
| `./logs.sh` | View logs from all services |
| `./logs.sh api` | View only API logs |
| `./logs.sh frontend` | View only frontend logs |
| `./logs.sh status` | Check service health |

## 📋 Prerequisites

Before running the startup script, ensure you have:

1. **Docker Desktop** installed and running
2. **Node.js 18+** installed
3. **OpenAI API Key** (optional, but needed for AI analysis)

## ⚙️ Configuration

1. **Environment Setup**: The script automatically creates `.env` from `.env.example`
2. **OpenAI API Key**: Edit `.env` and add your OpenAI API key:
   ```bash
   OPENAI_API_KEY=sk-your-key-here
   ```

## 🔗 Service URLs

After startup, these URLs will be available:

- **Main Application**: http://localhost:3000
- **API Documentation**: http://localhost:8000/docs
- **API Health Check**: http://localhost:8000/healthz
- **Backend API**: http://localhost:8000

## 🐛 Troubleshooting

If something goes wrong:

1. **Check logs**: `./logs.sh`
2. **Check service status**: `./logs.sh status`
3. **Restart everything**: `./restart.sh`
4. **Stop and start fresh**: `./stop.sh` then `./start.sh`

## 📝 What Each Service Does

- **🔧 Backend API** (port 8000): FastAPI server handling uploads and AI processing
- **💾 Redis** (port 6379): Database for caching and job queues
- **👷 Worker**: Background service for AI palm analysis
- **🎨 Frontend** (port 3000): Next.js web application with upload interface

## 🎯 Usage Flow

1. Start the application: `./start.sh`
2. Open http://localhost:3000
3. Upload palm images (left and/or right palm)
4. Wait for AI analysis to complete
5. View your palmistry reading results!

---

**Need help?** Check the logs with `./logs.sh` or view the full README.md for detailed information.