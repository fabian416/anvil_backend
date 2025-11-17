# 🔧 Anvil Platform - Environment Setup Guide

## Complete Development Environment Configuration

**Version:** 1.0  
**Date:** November 2025  
**Audience:** All Developers

---

## 📋 Prerequisites

### Required Software

```yaml
Operating System:
  - macOS 12+ (recommended)
  - Ubuntu 22.04+
  - Windows 10+ with WSL2

Required Installations:
  - Python 3.11+
  - Node.js 18+
  - Docker Desktop
  - Git
  - MySQL Client
  - Redis CLI
```

---

## 🐍 Backend Setup (Python/FastAPI)

### Step 1: Install Python

**macOS:**
```bash
# Install Homebrew if not installed
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Python 3.11
brew install python@3.11

# Verify installation
python3.11 --version
```

**Ubuntu:**
```bash
# Update package list
sudo apt update

# Install Python 3.11
sudo apt install python3.11 python3.11-venv python3.11-dev

# Verify installation
python3.11 --version
```

### Step 2: Clone Repository

```bash
# Clone the repository
git clone git@github.com:anvil/anvil-backend.git
cd anvil-backend

# Create and activate virtual environment
python3.11 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Upgrade pip
pip install --upgrade pip
```

### Step 3: Install Dependencies

```bash
# Install all dependencies
pip install -r requirements.txt

# Install development dependencies
pip install -r requirements-dev.txt
```

**requirements.txt:**
```txt
# Web Framework
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0
pydantic-settings==2.1.0

# Database
sqlalchemy==2.0.23
pymysql==1.1.0
alembic==1.12.1

# Authentication
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.6

# Blockchain
web3==6.11.3
eth-account==0.10.0

# Redis & Caching
redis==5.0.1
hiredis==2.2.3

# Celery
celery==5.3.4
flower==2.0.1

# External APIs
stripe==7.4.0
requests==2.31.0
httpx==0.25.2

# AI/ML
google-cloud-aiplatform==1.38.0

# Monitoring
sentry-sdk[fastapi]==1.38.0

# Utilities
python-dotenv==1.0.0
```

**requirements-dev.txt:**
```txt
# Testing
pytest==7.4.3
pytest-asyncio==0.21.1
pytest-cov==4.1.0
pytest-mock==3.12.0

# Code Quality
black==23.12.0
flake8==6.1.0
mypy==1.7.1
isort==5.13.2

# Development
ipython==8.18.1
ipdb==0.13.13
```

### Step 4: Setup Local Database

**Using Docker (Recommended):**
```bash
# Start MySQL and Redis
docker-compose up -d db redis

# Verify containers are running
docker ps

# Check logs
docker logs anvil-db
docker logs anvil-redis
```

**docker-compose.yml:**
```yaml
version: '3.8'

services:
  db:
    image: mysql:8.0
    container_name: anvil-db
    environment:
      MYSQL_ROOT_PASSWORD: rootpassword
      MYSQL_DATABASE: anvil_dev
      MYSQL_USER: anvil
      MYSQL_PASSWORD: anvilpassword
    ports:
      - "3306:3306"
    volumes:
      - mysql_data:/var/lib/mysql
    command: --default-authentication-plugin=mysql_native_password

  redis:
    image: redis:7-alpine
    container_name: anvil-redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes

volumes:
  mysql_data:
  redis_data:
```

### Step 5: Configure Environment Variables

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your values
nano .env  # or use your preferred editor
```

**.env:**
```bash
# Environment
ENVIRONMENT=development
DEBUG=true

# Database
DATABASE_URL=mysql+pymysql://anvil:anvilpassword@localhost:3306/anvil_dev
DATABASE_POOL_SIZE=5
DATABASE_MAX_OVERFLOW=10

# Redis
REDIS_URL=redis://localhost:6379/0

# JWT
JWT_SECRET_KEY=dev-secret-key-change-in-production-make-it-long-and-random
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60

# CORS
ALLOWED_ORIGINS=["http://localhost:3000","http://localhost:19006"]

# Privy (Development)
PRIVY_APP_ID=your_dev_privy_app_id
PRIVY_APP_SECRET=your_dev_privy_secret

# Stripe (Test Mode)
STRIPE_SECRET_KEY=sk_test_your_test_key
STRIPE_WEBHOOK_SECRET=whsec_your_test_webhook_secret

# Blockchain RPCs (Alchemy Test)
ARBITRUM_RPC_URL=https://arb-sepolia.g.alchemy.com/v2/your_test_key
BASE_RPC_URL=https://base-sepolia.g.alchemy.com/v2/your_test_key

# 1inch (Development)
ONEINCH_API_KEY=your_dev_api_key

# Google Cloud (Development)
GOOGLE_CLOUD_PROJECT=your-dev-project-id
GOOGLE_CLOUD_LOCATION=us-central1
VERTEX_AI_MODEL=gemini-1.5-flash

# SendGrid (Test)
SENDGRID_API_KEY=SG.your_test_key
SENDGRID_FROM_EMAIL=dev@anvil.com

# Twilio (Test)
TWILIO_ACCOUNT_SID=ACtest123
TWILIO_AUTH_TOKEN=test_token
TWILIO_FROM_NUMBER=+15555555555

# Firebase
FIREBASE_CREDENTIALS_PATH=./credentials/firebase-dev.json

# Sentry (Optional for dev)
SENTRY_DSN=

# Celery
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Rate Limiting
RATE_LIMIT_ENABLED=false
```

### Step 6: Initialize Database

```bash
# Run migrations
alembic upgrade head

# Verify tables created
mysql -h localhost -u anvil -panvilpassword anvil_dev -e "SHOW TABLES;"

# Seed initial data (optional)
python scripts/seed_data.py
```

### Step 7: Run Development Server

```bash
# Start FastAPI server with auto-reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# In another terminal, start Celery worker
celery -A app.workers.celery_app worker --loglevel=info

# In another terminal, start Celery beat (for scheduled tasks)
celery -A app.workers.celery_app beat --loglevel=info

# (Optional) Start Flower for Celery monitoring
celery -A app.workers.celery_app flower --port=5555
```

### Step 8: Verify Setup

```bash
# Test API health endpoint
curl http://localhost:8000/health

# Expected response:
# {"status":"healthy","version":"1.0.0","environment":"development"}

# Test API docs
# Open in browser: http://localhost:8000/docs
```

---

## 📱 Mobile App Setup (React Native)

### Step 1: Install Node.js

**macOS:**
```bash
# Using Homebrew
brew install node@18

# Verify installation
node --version
npm --version
```

### Step 2: Install React Native CLI

```bash
# Install globally
npm install -g react-native-cli

# Install Expo CLI (if using Expo)
npm install -g expo-cli
```

### Step 3: Setup iOS Development (macOS Only)

```bash
# Install Xcode from App Store
# Then install Command Line Tools
xcode-select --install

# Install CocoaPods
sudo gem install cocoapods

# Verify installation
pod --version
```

### Step 4: Setup Android Development

**Install Android Studio:**
1. Download from https://developer.android.com/studio
2. Install Android SDK
3. Setup environment variables:

```bash
# Add to ~/.zshrc or ~/.bashrc
export ANDROID_HOME=$HOME/Library/Android/sdk
export PATH=$PATH:$ANDROID_HOME/emulator
export PATH=$PATH:$ANDROID_HOME/tools
export PATH=$PATH:$ANDROID_HOME/tools/bin
export PATH=$PATH:$ANDROID_HOME/platform-tools
```

### Step 5: Clone and Setup Project

```bash
# Clone repository
git clone git@github.com:anvil/anvil-mobile.git
cd anvil-mobile

# Install dependencies
npm install

# Install iOS dependencies (macOS only)
cd ios && pod install && cd ..
```

### Step 6: Configure Environment

```bash
# Copy example environment
cp .env.example .env

# Edit with your values
nano .env
```

**.env:**
```bash
# API
API_URL=http://localhost:8000/api/v1

# Privy
PRIVY_APP_ID=your_dev_privy_app_id

# Environment
ENVIRONMENT=development
```

### Step 7: Run Mobile App

**iOS (macOS only):**
```bash
# Start Metro bundler
npx react-native start

# In another terminal, run iOS
npx react-native run-ios

# Or specific device
npx react-native run-ios --simulator="iPhone 15 Pro"
```

**Android:**
```bash
# Start Metro bundler
npx react-native start

# In another terminal, run Android
npx react-native run-android
```

---

## 💻 Admin Console Setup (Next.js)

### Step 1: Clone and Install

```bash
# Clone repository
git clone git@github.com:anvil/anvil-admin.git
cd anvil-admin

# Install dependencies
npm install
```

### Step 2: Configure Environment

```bash
# Copy example
cp .env.example .env.local

# Edit values
nano .env.local
```

**.env.local:**
```bash
# API
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1

# Environment
NEXT_PUBLIC_ENVIRONMENT=development
```

### Step 3: Run Development Server

```bash
# Start Next.js dev server
npm run dev

# Open in browser
# http://localhost:3000
```

---

## 🛠️ Development Tools Setup

### VS Code Configuration

**Install Extensions:**
```json
{
  "recommendations": [
    "ms-python.python",
    "ms-python.vscode-pylance",
    "ms-python.black-formatter",
    "dbaeumer.vscode-eslint",
    "esbenp.prettier-vscode",
    "bradlc.vscode-tailwindcss",
    "ms-vscode.vscode-typescript-next",
    "eamodio.gitlens"
  ]
}
```

**Workspace Settings (.vscode/settings.json):**
```json
{
  "python.defaultInterpreterPath": "${workspaceFolder}/venv/bin/python",
  "python.formatting.provider": "black",
  "python.linting.enabled": true,
  "python.linting.flake8Enabled": true,
  "python.testing.pytestEnabled": true,
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.organizeImports": true
  },
  "[python]": {
    "editor.defaultFormatter": "ms-python.black-formatter",
    "editor.tabSize": 4
  },
  "[typescript]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode",
    "editor.tabSize": 2
  },
  "[typescriptreact]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode",
    "editor.tabSize": 2
  }
}
```

### Git Configuration

```bash
# Set user info
git config --global user.name "Your Name"
git config --global user.email "your.email@company.com"

# Set default branch
git config --global init.defaultBranch main

# Setup aliases
git config --global alias.co checkout
git config --global alias.br branch
git config --global alias.ci commit
git config --global alias.st status

# Setup commit template
git config --global commit.template ~/.gitmessage

# Create commit message template
cat > ~/.gitmessage << 'EOF'
# <type>: <subject> (max 50 chars)
# |<----  Using a Maximum Of 50 Characters  ---->|

# Explain why this change is being made
# |<----   Try To Limit Each Line to a Maximum Of 72 Characters   ---->|

# Provide links or keys to any relevant tickets, articles or other resources

# --- COMMIT END ---
# Type can be
#    feat     (new feature)
#    fix      (bug fix)
#    refactor (refactoring code)
#    style    (formatting, missing semi colons, etc; no code change)
#    docs     (changes to documentation)
#    test     (adding or refactoring tests; no production code change)
#    chore    (updating build tasks etc; no production code change)
# --------------------
EOF
```

---

## 🔍 Troubleshooting

### Common Issues

**Issue: Database connection failed**
```bash
# Check if MySQL is running
docker ps | grep mysql

# Check connection manually
mysql -h localhost -u anvil -panvilpassword anvil_dev

# Restart database
docker-compose restart db
```

**Issue: Redis connection failed**
```bash
# Check if Redis is running
docker ps | grep redis

# Test connection
redis-cli ping

# Restart Redis
docker-compose restart redis
```

**Issue: Port already in use**
```bash
# Find process using port 8000
lsof -ti:8000

# Kill the process
kill -9 <PID>

# Or use different port
uvicorn app.main:app --reload --port 8001
```

**Issue: Module not found**
```bash
# Ensure virtual environment is activated
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

**Issue: React Native build failed**
```bash
# Clean build (iOS)
cd ios && pod deintegrate && pod install && cd ..

# Clean build (Android)
cd android && ./gradlew clean && cd ..

# Clear Metro cache
npx react-native start --reset-cache
```

---

## ✅ Verification Checklist

### Backend
- [ ] Python 3.11+ installed
- [ ] Virtual environment created and activated
- [ ] All dependencies installed
- [ ] MySQL running and accessible
- [ ] Redis running and accessible
- [ ] Environment variables configured
- [ ] Database migrations run successfully
- [ ] API server starts without errors
- [ ] Celery worker starts without errors
- [ ] Health endpoint returns 200 OK
- [ ] API docs accessible at /docs

### Mobile
- [ ] Node.js 18+ installed
- [ ] React Native CLI installed
- [ ] Xcode installed (iOS, macOS only)
- [ ] Android Studio installed (Android)
- [ ] Dependencies installed
- [ ] iOS pods installed (macOS only)
- [ ] Environment variables configured
- [ ] App builds successfully
- [ ] App runs on simulator/emulator
- [ ] Can connect to local API

### Admin Console
- [ ] Node.js 18+ installed
- [ ] Dependencies installed
- [ ] Environment variables configured
- [ ] Development server starts
- [ ] Can connect to local API
- [ ] UI loads without errors

### Tools
- [ ] VS Code installed with extensions
- [ ] Git configured
- [ ] Docker Desktop installed
- [ ] Database client installed (optional)

---

## 📚 Additional Resources

### Documentation
- FastAPI: https://fastapi.tiangolo.com/
- React Native: https://reactnative.dev/
- Next.js: https://nextjs.org/
- SQLAlchemy: https://docs.sqlalchemy.org/

### Community
- Internal Slack: #anvil-dev
- Backend questions: #anvil-backend
- Mobile questions: #anvil-mobile
- DevOps questions: #anvil-devops

---

**Document Version:** 1.0  
**Last Updated:** November 2025  
**Maintained By:** DevOps Team  
**Support:** devops@anvil.com
