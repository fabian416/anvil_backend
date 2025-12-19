# ❓ Anvil Platform - FAQ & Troubleshooting Guide

## Frequently Asked Questions & Common Solutions

**Version:** 1.0  
**Date:** November 2025  
**Audience:** All Team Members

---

## 📚 Table of Contents

1. [General Questions](#general-questions)
2. [Development Setup](#development-setup)
3. [Backend Development](#backend-development)
4. [Mobile Development](#mobile-development)
5. [Database Issues](#database-issues)
6. [Deployment & DevOps](#deployment--devops)
7. [Testing](#testing)
8. [Performance](#performance)
9. [Security](#security)
10. [Third-Party Integrations](#third-party-integrations)

---

## 🎯 General Questions

### Q: Where do I start as a new developer?

**A:** Follow this path:
1. Read [Developer Onboarding Guide](computer:///mnt/user-data/outputs/14_developer_onboarding.md)
2. Set up your environment using [Environment Setup Guide](computer:///mnt/user-data/outputs/09_environment_setup_guide.md)
3. Review [Code Style Guide](computer:///mnt/user-data/outputs/10_code_style_guide.md)
4. Pick up a "good-first-issue" from GitHub
5. Ask questions in Slack #engineering

---

### Q: What's the difference between Anvil environments?

**A:**
```yaml
Development (dev):
  - Your local machine
  - Fake data for testing
  - Hot reload enabled
  - No rate limiting

Staging:
  - Cloud environment
  - Anonymized production copy
  - Pre-production testing
  - Same setup as production

Production:
  - Live system
  - Real user data
  - Monitored 24/7
  - High availability setup
```

---

### Q: Who do I contact for help?

**A:**
```yaml
Code Questions: #engineering Slack channel
API Questions: Backend team lead
Mobile Questions: Mobile team lead
DevOps/Infrastructure: #devops channel
Product Questions: Product manager
Urgent Issues: On-call engineer (PagerDuty)
```

---

## 💻 Development Setup

### Q: My database connection fails

**Problem:** `mysql.connector.errors.InterfaceError: Can't connect to MySQL server`

**Solutions:**
```bash
# 1. Check if MySQL is running
docker ps | grep mysql

# 2. Check connection details
mysql -h localhost -u anvil -panvilpassword anvil_dev

# 3. If using Docker, check network
docker network ls
docker inspect anvil-network

# 4. Reset Docker containers
docker-compose down
docker-compose up -d

# 5. Check .env file
cat .env | grep DATABASE
```

---

### Q: Redis connection fails

**Problem:** `redis.exceptions.ConnectionError: Error connecting to Redis`

**Solutions:**
```bash
# 1. Check if Redis is running
docker ps | grep redis

# 2. Test connection
redis-cli ping
# Should return: PONG

# 3. Check Redis port
redis-cli -p 6379 ping

# 4. Restart Redis
docker-compose restart redis

# 5. Check Redis logs
docker logs anvil-redis
```

---

### Q: Port already in use

**Problem:** `OSError: [Errno 48] Address already in use`

**Solutions:**
```bash
# Find process using port 8000
lsof -ti:8000

# Kill the process
kill -9 $(lsof -ti:8000)

# Or use different port
uvicorn app.main:app --port 8001
```

---

### Q: Python module not found

**Problem:** `ModuleNotFoundError: No module named 'fastapi'`

**Solutions:**
```bash
# 1. Ensure virtual environment is activated
source venv/bin/activate

# 2. Reinstall dependencies
pip install -r requirements.txt

# 3. Check Python version
python --version  # Should be 3.11+

# 4. Verify virtual environment
which python  # Should point to venv/bin/python
```

---

## 🐍 Backend Development

### Q: How do I add a new API endpoint?

**A:**
```python
# 1. Add route in app/api/v1/routes/your_module.py
@router.get("/new-endpoint")
async def new_endpoint(
    current_user: User = Depends(get_current_user)
):
    """Endpoint description."""
    return {"message": "Hello"}

# 2. Add to router in app/api/v1/api.py
api_router.include_router(
    your_module.router,
    prefix="/your-module",
    tags=["Your Module"]
)

# 3. Add tests in tests/api/v1/test_your_module.py
def test_new_endpoint(client, auth_headers):
    response = client.get("/api/v1/your-module/new-endpoint",
                          headers=auth_headers)
    assert response.status_code == 200
```

---

### Q: How do I add a database model?

**A:**
```python
# 1. Create model in app/models/your_model.py
from app.models.base import BaseModel

class YourModel(BaseModel):
    __tablename__ = "your_table"
    
    name = Column(String(255), nullable=False)
    description = Column(Text)
    # ... more fields

# 2. Import in app/models/__init__.py
from app.models.your_model import YourModel

# 3. Create migration
alembic revision --autogenerate -m "add your_model"

# 4. Review and run migration
alembic upgrade head
```

---

### Q: Alembic migration fails

**Problem:** `Target database is not up to date.`

**Solutions:**
```bash
# 1. Check current version
alembic current

# 2. Check migration history
alembic history

# 3. If stuck, stamp database
alembic stamp head

# 4. If corrupted, drop alembic_version table
mysql -u root -p anvil_dev -e "DROP TABLE alembic_version;"

# 5. Re-initialize
alembic stamp head
```

---

### Q: How do I mock external APIs in tests?

**A:**
```python
# Use responses library for HTTP mocking
import responses

@responses.activate
def test_external_api():
    # Mock the API response
    responses.add(
        responses.GET,
        'https://api.external.com/data',
        json={'key': 'value'},
        status=200
    )
    
    # Your test code
    result = fetch_external_data()
    assert result['key'] == 'value'
```

---

## 📱 Mobile Development

### Q: React Native build fails

**Problem:** iOS/Android build errors

**Solutions:**
```bash
# iOS
cd ios
pod deintegrate
pod install
cd ..
npx react-native run-ios

# Android
cd android
./gradlew clean
cd ..
npx react-native run-android

# Clear Metro cache
npx react-native start --reset-cache
```

---

### Q: API calls fail from mobile app

**Problem:** Network request failed

**Solutions:**
```typescript
// 1. Check API URL in .env
console.log(Config.API_URL)

// 2. For iOS simulator, use localhost
// .env
API_URL=http://localhost:8000/api/v1

// 3. For Android emulator, use 10.0.2.2
// .env
API_URL=http://10.0.2.2:8000/api/v1

// 4. For physical device, use computer's IP
// .env
API_URL=http://192.168.1.100:8000/api/v1

// 5. Check network permissions (Android)
// android/app/src/main/AndroidManifest.xml
<uses-permission android:name="android.permission.INTERNET" />
```

---

### Q: White screen on app launch

**Problem:** App shows blank white screen

**Solutions:**
```bash
# 1. Check console for errors
npx react-native log-ios
# or
npx react-native log-android

# 2. Rebuild app
# Delete app from device/simulator
npm run ios
# or
npm run android

# 3. Check for JavaScript errors
# Look for syntax errors, import errors

# 4. Clear React Native cache
rm -rf node_modules
rm -rf ios/build
npm install
cd ios && pod install && cd ..
```

---

### Q: How do I debug mobile app?

**A:**
```typescript
// 1. Use React Native Debugger
// Install: brew install --cask react-native-debugger

// 2. Enable debug mode
// Shake device → "Debug" → "Enable Debug"

// 3. Use console.log
console.log('Debug info:', data)

// 4. Use Reactotron
import Reactotron from 'reactotron-react-native'
Reactotron.log('Debug message')

// 5. Use React DevTools
npm install -g react-devtools
react-devtools
```

---

## 🗄️ Database Issues

### Q: Slow database queries

**Problem:** Queries taking >1 second

**Solutions:**
```sql
-- 1. Check slow query log
SELECT * FROM mysql.slow_log
ORDER BY query_time DESC
LIMIT 10;

-- 2. Explain query
EXPLAIN SELECT * FROM transactions
WHERE user_id = 123;

-- 3. Add missing indexes
CREATE INDEX idx_transactions_user 
ON transactions(user_id);

-- 4. Optimize query
-- Bad
SELECT * FROM users;

-- Good
SELECT id, email, firstname FROM users;
```

---

### Q: Database connection pool exhausted

**Problem:** `pymysql.err.OperationalError: (1040, 'Too many connections')`

**Solutions:**
```python
# 1. Check current connections
mysql> SHOW PROCESSLIST;

# 2. Increase pool size
# app/core/database.py
engine = create_engine(
    DATABASE_URL,
    pool_size=20,  # Increase from 10
    max_overflow=40  # Increase from 20
)

# 3. Check for connection leaks
# Ensure sessions are closed
with SessionLocal() as db:
    # Your code
    pass  # Session auto-closes

# 4. Implement connection pooling in application
```

---

## 🚀 Deployment & DevOps

### Q: Docker build fails

**Problem:** `ERROR: failed to solve`

**Solutions:**
```bash
# 1. Clear Docker cache
docker system prune -a

# 2. Build with no cache
docker build --no-cache -t anvil-api .

# 3. Check Dockerfile syntax
docker build --progress=plain -t anvil-api .

# 4. Verify base image exists
docker pull python:3.11-slim
```

---

### Q: ECS tasks keep restarting

**Problem:** Tasks fail health checks

**Solutions:**
```bash
# 1. Check task logs
aws logs tail /aws/ecs/anvil-api --follow

# 2. Check task status
aws ecs describe-tasks \
  --cluster anvil-production \
  --tasks <task-id>

# 3. Check health check endpoint
curl http://<task-ip>:8000/health

# 4. Increase health check grace period
# In task definition
"healthCheck": {
  "startPeriod": 60  # Increase from 30
}
```

---

### Q: Deployment failed

**Problem:** CI/CD pipeline fails

**Solutions:**
```yaml
# 1. Check GitHub Actions logs
# Go to Actions tab → Failed workflow → Check logs

# 2. Re-run workflow
# Click "Re-run all jobs"

# 3. Check secrets are set
# Settings → Secrets → Verify all required secrets exist

# 4. Test locally
docker build -t anvil-api:test .
docker run -p 8000:8000 anvil-api:test

# 5. Check AWS credentials
aws sts get-caller-identity
```

---

## 🧪 Testing

### Q: Tests fail with database errors

**Problem:** Tests can't connect to test database

**Solutions:**
```python
# 1. Use separate test database
# tests/conftest.py
TEST_DATABASE_URL = "mysql://test:test@localhost/anvil_test"

# 2. Create test database
mysql -u root -p -e "CREATE DATABASE anvil_test;"

# 3. Use in-memory SQLite for faster tests
TEST_DATABASE_URL = "sqlite:///./test.db"

# 4. Clean database between tests
@pytest.fixture(autouse=True)
def reset_database():
    # Setup
    Base.metadata.create_all(bind=engine)
    yield
    # Teardown
    Base.metadata.drop_all(bind=engine)
```

---

### Q: How do I run specific tests?

**A:**
```bash
# Run all tests
pytest

# Run specific file
pytest tests/test_users.py

# Run specific test
pytest tests/test_users.py::test_create_user

# Run tests matching pattern
pytest -k "user"

# Run with coverage
pytest --cov=app tests/

# Run with verbose output
pytest -v
```

---

## ⚡ Performance

### Q: API is slow

**Problem:** Response times >1 second

**Solutions:**
```python
# 1. Add caching
from app.core.cache import cache

@cache(ttl=300)
def get_user_balance(user_id: int):
    # Expensive operation
    pass

# 2. Optimize database queries
# Use joinedload for relationships
users = db.query(User).options(
    joinedload(User.wallet),
    joinedload(User.transactions)
).all()

# 3. Use async operations
import asyncio
results = await asyncio.gather(
    get_balances(),
    get_transactions(),
    get_positions()
)

# 4. Profile slow endpoints
import cProfile
cProfile.run('slow_function()')
```

---

### Q: High memory usage

**Problem:** Application using >2GB RAM

**Solutions:**
```python
# 1. Check for memory leaks
import tracemalloc
tracemalloc.start()
# ... run code ...
snapshot = tracemalloc.take_snapshot()
top_stats = snapshot.statistics('lineno')

# 2. Use generators for large datasets
def get_all_transactions():
    for tx in db.query(Transaction).yield_per(1000):
        yield tx

# 3. Clear caches periodically
redis_client.flushdb()

# 4. Limit query results
transactions = db.query(Transaction).limit(100).all()
```

---

## 🔒 Security

### Q: How do I store secrets?

**A:**
```python
# ❌ NEVER do this
API_KEY = "sk_live_123456789"

# ✅ Use environment variables
import os
API_KEY = os.getenv("API_KEY")

# ✅ Use AWS Secrets Manager
import boto3
secrets = boto3.client('secretsmanager')
secret = secrets.get_secret_value(SecretId='anvil/api-key')

# ✅ Use .env file (gitignored)
# .env
API_KEY=sk_live_123456789

# Load in app
from dotenv import load_dotenv
load_dotenv()
```

---

### Q: How do I handle sensitive data?

**A:**
```python
# ✅ Hash passwords
from passlib.context import CryptContext
pwd_context = CryptContext(schemes=["bcrypt"])

hashed = pwd_context.hash("password123")
pwd_context.verify("password123", hashed)  # True

# ✅ Encrypt sensitive fields
from cryptography.fernet import Fernet

key = Fernet.generate_key()
f = Fernet(key)
encrypted = f.encrypt(b"sensitive data")
decrypted = f.decrypt(encrypted)

# ✅ Don't log sensitive data
logger.info(f"User logged in: {user.email}")  # OK
logger.info(f"Password: {password}")  # ❌ NEVER
```

---

## 🔌 Third-Party Integrations

### Q: Privy authentication fails

**Problem:** User can't login with Privy

**Solutions:**
```typescript
// 1. Check Privy configuration
console.log('Privy App ID:', Config.PRIVY_APP_ID)

// 2. Verify callback URL
// Must match exactly in Privy dashboard

// 3. Check browser console for errors
// Look for CORS, network errors

// 4. Test with different provider
// Try email vs Google vs wallet

// 5. Contact Privy support
// support@privy.io with error logs
```

---

### Q: 1inch swap fails

**Problem:** Swap transaction fails

**Solutions:**
```python
# 1. Check 1inch API status
response = requests.get('https://api.1inch.dev/healthcheck')

# 2. Verify API key
headers = {'Authorization': f'Bearer {ONEINCH_API_KEY}'}

# 3. Check slippage settings
# May be too low, causing transaction to revert

# 4. Check gas price
# Transaction may be underpriced

# 5. Check allowance
# Token allowance may be insufficient
```

---

## 📞 Getting More Help

### Documentation

```yaml
Internal Docs:
  - Full documentation in /outputs directory
  - API docs: https://api.anvil.com/docs
  - Team wiki: Confluence/Notion

External Docs:
  - FastAPI: https://fastapi.tiangolo.com/
  - React Native: https://reactnative.dev/
  - SQLAlchemy: https://docs.sqlalchemy.org/
```

### Channels

```yaml
Slack:
  #engineering: General development questions
  #backend: Backend-specific questions
  #mobile: Mobile-specific questions
  #devops: Infrastructure questions
  #help: General help

Emergency:
  PagerDuty: Critical issues
  On-call: See rotation schedule
```

### Office Hours

```yaml
Backend Lead: Tuesday 2-3 PM
Mobile Lead: Wednesday 2-3 PM
DevOps: Thursday 2-3 PM
Tech Lead: Friday 10-11 AM
```

---

## 📚 Additional Resources

### Learning Materials

```yaml
Backend:
  - "Designing Data-Intensive Applications" book
  - FastAPI tutorial series
  - Real Python courses

Mobile:
  - React Native docs
  - Expo documentation
  - React hooks guide

DeFi:
  - Aave documentation
  - Uniswap v3 whitepaper
  - DeFi safety best practices
```

---

## 🎯 Quick Reference

### Common Commands

```bash
# Start development server
uvicorn app.main:app --reload

# Run tests
pytest

# Create migration
alembic revision --autogenerate -m "description"

# Run migration
alembic upgrade head

# Start mobile app (iOS)
npx react-native run-ios

# Start mobile app (Android)
npx react-native run-android

# Docker Compose
docker-compose up -d
docker-compose down
docker-compose logs -f

# Check API health
curl http://localhost:8000/health
```

---

## ✅ Troubleshooting Checklist

When something goes wrong:

```yaml
1. Read the error message carefully
2. Check the logs
3. Search this FAQ
4. Search internal documentation
5. Search Stack Overflow
6. Ask in Slack (with error message + what you tried)
7. Create a ticket if it's a bug
8. Contact on-call if urgent/critical
```

---

**Document Version:** 1.0  
**Last Updated:** November 2025  
**Maintained By:** Engineering Team  
**Contribute:** Submit PRs to improve this doc!

**Can't find your question? Ask in Slack #engineering!**
