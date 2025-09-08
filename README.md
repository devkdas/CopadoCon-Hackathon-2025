# CopadoCon 2025 Hackathon - Intelligent Salesforce Monitor

A smart monitoring system that watches your Salesforce org 24/7 and automatically fixes problems before they impact users. Think of it as having an AI-powered DevOps expert on your team who never sleeps.

## What This Does
Transforms Salesforce issue resolution from **"Oh no, production is broken!"** to **"Issue detected and already fixed"**. We're talking about reducing incident response time from days to minutes using AI that actually understands your code and deployments.

## Current Status
This system is **fully functional** with:
- Real-time Salesforce monitoring and incident detection
- Beautiful web dashboard with live updates and detailed incident views
- AI-powered root cause analysis that correlates issues to code changes
- Automated ticket creation, Slack notifications, and rollback suggestions
- Production-ready deployment with Docker support

## Architecture

### How It Works

**1. Always Watching** 
- Monitors your Salesforce org constantly for errors, slow performance, and deployment issues
- Listens to your Git webhooks to track what code changes are being deployed
- Connects to your testing systems to catch failures immediately

**2. Smart Analysis**
- When something breaks, our AI agent figures out why by looking at recent deployments
- Correlates error patterns with code changes to pinpoint the exact cause
- Learns from past incidents to get better at predicting future problems

**3. Automatic Response**
- Creates detailed Jira tickets with all the context your team needs
- Sends smart Slack alerts that actually help instead of just adding noise  
- Suggests rollbacks when deployments are causing issues
- Can even comment on GitHub PRs with fix suggestions

## Requirements

- **Python**: 3.11+ (tested with 3.11, 3.12, 3.13)
- **Docker**: Optional, for containerized deployment
- **Git**: For cloning the repository

## Getting Started

### The Easy Way (5 minutes to running)

1. **Grab the code**:
   ```bash
   git clone https://github.com/devkdas/CopadoCon-Hackathon-2025.git
   cd "CopadoCon-Hackathon-2025"
   ```

2. **Install what you need**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up your config**:
   ```bash
   cp .env.example .env
   # Open .env and add your API keys (at minimum, you need OpenAI API key)
   ```

4. **Start monitoring**:
   ```bash
   python main.py
   ```

5. **Check it out**:
   Open http://localhost:8080 in your browser and watch the magic happen!

### Just Want to See It Work? (No setup required)

If you just want to see what this looks like without connecting to real systems:

```bash
# Install just the basics
pip install fastapi uvicorn pydantic requests python-dotenv jinja2 aiofiles websockets loguru httpx

# Create a basic config file
cp .env.example .env

# Run the demo with fake data
python simple_demo.py
```

This will show you the dashboard with simulated incidents so you can see how it all works.

## Docker Deployment

### Development with Docker Compose

1. **Setup environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

2. **Build and run with Docker Compose**:
   ```bash
   docker-compose up --build
   ```

3. **Access application**:
   - Dashboard: `http://localhost:8080`
   - Redis: Available on `localhost:6379`

4. **Stop services**:
   ```bash
   docker-compose down
   ```

### Production Deployment

1. **Create production environment**:
   ```bash
   cp .env.example .env.production
   # Configure production values in .env.production
   ```

2. **Deploy with production compose**:
   ```bash
   docker-compose -f docker-compose.prod.yml up -d --build
   ```

3. **Monitor deployment**:
   ```bash
   docker-compose -f docker-compose.prod.yml logs -f
   docker-compose -f docker-compose.prod.yml ps
   ```

### Manual Docker Build

1. **Build image**:
   ```bash
   docker build -t copadocon-2025-hackathon .
   ```

2. **Run container**:
   ```bash
   docker run -d \
     --name hackathon-app \
     -p 8080:8080 \
     --env-file .env \
     copadocon-2025-hackathon
   ```

3. **View logs**:
   ```bash
   docker logs hackathon-app -f
   ```

### Docker Features

- **Multi-stage build**: Optimized for production deployment
- **Health checks**: Built-in health monitoring at `/api/health`
- **Security**: Runs as non-root user
- **Persistence**: Data and logs mounted to host volumes
- **Redis integration**: Includes Redis for caching and background tasks
- **Auto-restart**: Containers restart unless explicitly stopped

## Project Structure

```
CopadoCon 2025 Hackathon/
├── src/                    # Core application source
│   ├── core/              # Agent and configuration
│   ├── analyzers/         # AI analysis engine
│   ├── actions/           # Automated workflows
│   ├── integrations/      # External API clients
│   └── api/               # REST API endpoints
├── static/                # Dashboard UI files
├── .env.example          # Environment configuration template
├── requirements.txt      # All project dependencies
├── main.py              # Production application entry
├── simple_demo.py       # Standalone demo version
└── README.md           # This file
```

## Configuration

The `.env.example` file contains all configuration options:

### Required Settings
- **OPENAI_API_KEY**: For AI-powered analysis (minimum requirement)
- **PORT**: Application port (default: 8080)
- **ENVIRONMENT**: development/production/testing

### Optional Integrations
- **Salesforce**: Username, password, security token, domain
- **GitHub**: Token and webhook secret for code integration
- **Jira**: Server URL, username, API token for ticket management
- **Slack**: Bot token and webhook URL for notifications
- **Database**: SQLite (dev) or PostgreSQL (prod)
- **Redis**: For caching and background tasks

### Production Setup
For production deployment:
1. Copy `.env.example` to `.env`
2. Uncomment production overrides section
3. Replace placeholder values with actual credentials
4. Set `ENVIRONMENT=production`

## What Makes This Special

**Real-Time Intelligence**: Your dashboard updates live as incidents happen. No refreshing, no delays.

**Actually Smart AI**: Uses GPT-4 to understand what broke and why. It reads your code changes, correlates them with errors, and gives you actionable insights instead of just "something's wrong."

**Self-Healing Workflows**: Doesn't just alert you to problems - it starts fixing them. Creates tickets with context, suggests rollbacks, and even comments on problematic PRs.

**Beautiful Interface**: Clean, professional dashboard that your executives will love and your developers will actually use.

**Plays Nice with Everything**: Works with Salesforce, GitHub, Jira, Slack, and your existing tools. No need to change your workflow.

## Technology Stack

- **Backend**: Python, FastAPI, SQLAlchemy
- **AI**: OpenAI GPT-4, scikit-learn, pandas
- **Frontend**: HTML5, CSS3, JavaScript, Chart.js
- **Integrations**: Salesforce API, GitHub API, Jira API, Slack SDK
- **Deployment**: Docker, Copado CI/CD
