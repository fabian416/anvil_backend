# Authentication & User Management - Celery Background Tasks

**Document Version:** 1.0
**Last Updated:** 2026-01-25
**Architecture:** Hexagonal (Clean Architecture)

---

## Table of Contents

1. [Overview](#overview)
2. [Email Tasks](#email-tasks)
3. [User Context Tasks](#user-context-tasks)
4. [Task Configuration](#task-configuration)
5. [Queue Routing](#queue-routing)
6. [Monitoring & Retry Policies](#monitoring--retry-policies)
7. [Scheduled Tasks (Celery Beat)](#scheduled-tasks-celery-beat)

---

## Overview

The Authentication & User Management module uses **Celery** for asynchronous background task processing.

**Celery Configuration:**
- **Broker:** Redis (connection string in config)
- **Backend:** Redis (for result storage)
- **Worker Concurrency:** Configurable (default: CPU count)
- **Task Serializer:** JSON
- **Result Serializer:** JSON

**Celery App Location:** `src/app/infrastructure/celery/app.py:celery_app`

**Key Features:**
- Task routing to dedicated queues
- Automatic retry with exponential backoff
- Task result persistence (optional)
- Scheduled tasks via Celery Beat
- Task monitoring via Flower

---

## Email Tasks

Email tasks are implemented in `src/app/infrastructure/celery/compat_tasks.py`.

### 1. Send Email (Generic)

**Task Name:** `tasks.email_tasks.send_email`

**Location:** `src/app/infrastructure/celery/compat_tasks.py:59-65`

**Function:**
```python
@celery_app.task(name="tasks.email_tasks.send_email")
def send_email_namespaced(**kwargs: Any) -> None:
```

**Parameters:**
- `to_email` (str): Recipient email address
- `subject` (str): Email subject line
- `body` (str): Email body (plain text)

**Example Usage:**
```python
celery_app.send_task(
    "tasks.email_tasks.send_email",
    kwargs={
        "to_email": "user@example.com",
        "subject": "Welcome!",
        "body": "Thank you for signing up.",
    },
)
```

**Implementation Details:**
1. Reads Mailgun config from settings (domain, api_key)
2. Makes HTTP POST to Mailgun API
3. Sends email with `from: noreply@{domain}`
4. Logs warnings on failure (non-blocking)
5. 10-second timeout on HTTP request

**Mailgun API Call:** (Lines 29-39)
```python
resp = requests.post(
    f"https://api.mailgun.net/v3/{domain}/messages",
    auth=("api", api_key),
    data={
        "from": f"noreply@{domain}",
        "to": [to_email],
        "subject": subject,
        "text": body,
    },
    timeout=10,
)
```

**Error Handling:**
- Logs warning if Mailgun not configured (no-op)
- Logs warning on HTTP failure (status >= 300)
- Catches and logs exceptions without raising

**Queue:** `email` (dedicated queue for email tasks)

---

### 2. Send Verification Email

**Task Name:** `tasks.email_tasks.send_verification_email`

**Location:** `src/app/infrastructure/celery/compat_tasks.py:83-93`

**Function:**
```python
@celery_app.task(name="tasks.email_tasks.send_verification_email")
def send_verification_email(**kwargs: Any) -> None:
```

**Parameters:**
- `to_email` (str): Recipient email address
- `verification_url` (str): Verification token/URL

**Email Template:**
```
Subject: Verify your email
Body:
use the code below to verify your email
{verification_url}
```

**Triggered By:**
1. **Sign Up Handler:** `src/app/infrastructure/auth/handlers/sign_up.py:179-187`
   ```python
   celery_app.send_task(
       "tasks.email_tasks.send_verification_email",
       kwargs={
           "to_email": user.email.value,
           "verification_url": token,
       },
   )
   ```

2. **Send Email Verification Handler:** `src/app/infrastructure/auth/handlers/send_email_verification.py`

**Business Logic:**
- Token is generated with `secrets.token_urlsafe(32)` (32 bytes = 256 bits)
- Token expires in 24 hours
- Stored in `email_verifications` table

**Frontend Integration:**
- Frontend should provide verification link: `https://app.example.com/verify-email?token={token}`
- Backend provides token, frontend constructs full URL

---

### 3. Send Password Reset Email

**Task Name:** `tasks.email_tasks.send_password_reset_email`

**Location:** `src/app/infrastructure/celery/compat_tasks.py:96-107`

**Function:**
```python
@celery_app.task(name="tasks.email_tasks.send_password_reset_email")
def send_password_reset_email(**kwargs: Any) -> None:
```

**Parameters:**
- `to_email` (str): Recipient email address
- `reset_token` (str): Password reset token

**Email Template:**
```
Subject: Password reset request
Body:
Use the code below to reset your password
{reset_token}

If you did not request this, you can ignore this email.
```

**Triggered By:**
**Forgot Password Handler:** `src/app/infrastructure/auth/handlers/password_reset.py`

**Business Logic:**
- Token is generated with `secrets.token_urlsafe(32)`
- Token expires in 24 hours
- Stored in `password_resets` table
- Token is single-use (marked as used after password reset)

**Security Notes:**
- Token is cryptographically random (256 bits)
- Short expiration (24 hours)
- Single-use to prevent replay attacks

---

### 4. Send Password Change Notification

**Task Name:** `tasks.email_tasks.send_password_change_notification`

**Location:** `src/app/infrastructure/celery/compat_tasks.py:68-80`

**Function:**
```python
@celery_app.task(name="tasks.email_tasks.send_password_change_notification")
def send_password_change_notification(**kwargs: Any) -> None:
```

**Parameters:**
- `to_email` (str): User email address
- `username` (str): User's name
- `ip_address` (str): IP address of password change request
- `user_agent` (str): Browser/device user agent

**Email Template:**
```
Subject: Password Changed
Body:
Hello {username},

Your password was changed.
IP: {ip_address}
User-Agent: {user_agent}

If this was not you, contact support.
```

**Triggered By:**
1. **Change Own Password Handler:** `src/app/infrastructure/auth/handlers/change_password.py`
2. **Admin Change Password Interactor:** `src/app/application/commands/user/change_password.py`

**Security Purpose:**
- Alert users of password changes
- Provide IP and user-agent for suspicious activity detection
- Immediate notification for security incidents

---

## User Context Tasks

User context tasks manage the `user_context_aware` table for context-aware AI agents.

**Location:** `src/app/infrastructure/celery/tasks/user_context_tasks.py`

### 5. Update User Context

**Task Name:** `update_user_context`

**Location:** `src/app/infrastructure/celery/tasks/user_context_tasks.py:53-221`

**Function:**
```python
@celery_app.task(name="update_user_context")
def update_user_context():
```

**Purpose:**
Update user context for users eligible for processing.

This task performs **TWO operations:**

#### Operation 1: CREATE MISSING CONTEXTS (Lines 117-168)
- Find authenticated users without `user_context_aware` entry
- Create with default values
- Ensures all users eventually get context
- **Limit:** Max 30 users per run

**SQL Logic:**
```sql
SELECT cu.id, cu.user_id
FROM chat_users cu
LEFT JOIN user_context_aware uc ON cu.id = uc.chat_user_id
WHERE cu.user_type = 'authenticated'
  AND uc.id IS NULL
LIMIT 30
```

**Created Fields:**
- Portfolio state: "empty"
- Activity level: "new"
- User type: "new_user"
- Next update eligible: NOW() + 1 hour

#### Operation 2: UPDATE EXISTING CONTEXTS (Lines 170-205)
- Fetch users where `next_update_eligible_at <= NOW()`
- Aggregate chat stats, wallet data, execution history
- Recalculate classifications
- **Limit:** Max 100 users per run

**Update Logic:**
1. Get chat message count
2. Get wallet balance (USD) from `wallet_balance` adapter
3. Get execution history (swaps, buys, etc.)
4. Calculate portfolio state: empty, starter, active, whale
5. Calculate activity level: new, very_active, active, weekly_active, monthly_active, inactive, reactivated
6. Calculate user type: new_user, casual, trader, yield_farmer, power_user
7. Set `next_update_eligible_at` to NOW() + 1 hour

**Configuration:**
```python
MAX_USERS_PER_RUN = 100         # Max users to UPDATE per run
MAX_CREATE_PER_RUN = 30         # Max users to CREATE per run
UPDATE_COOLDOWN_HOURS = 1       # Skip users updated within last hour
```

**Execution Flow:**
```
1. Load DI container with async providers
2. Get repositories from container
3. CREATE STEP: Find and create missing contexts (max 30)
4. UPDATE STEP: Find and update eligible contexts (max 100)
5. Log summary statistics
6. Close container
```

**Scheduled:** Every 10 minutes (Celery Beat)

**Logging:**
```
🔄 Starting user context task at {timestamp}
📝 Step 1: Creating missing user contexts...
  Found {count} users without context
  Created context for {chat_user_id}
  ✓ All users have context entries
🔄 Step 2: Updating existing user contexts...
  Processing {count} users for update
  Updated {chat_user_id}: portfolio=active, activity=very_active, type=trader
✅ User context task complete: created={count}, updated={count}, errors={count}, duration={seconds}s
```

**Error Handling:**
- Logs errors per user but continues processing
- Tracks `error_count` in summary
- Raises exception on critical failure (stops task)

---

### 6. Create Missing User Contexts

**Task Name:** `create_missing_user_contexts`

**Location:** `src/app/infrastructure/celery/tasks/user_context_tasks.py:224-327`

**Function:**
```python
@celery_app.task(name="create_missing_user_contexts")
def create_missing_user_contexts():
```

**Purpose:**
One-time migration task to create context entries for users who don't have one.

**Business Logic:**
- Same as Operation 1 from `update_user_context`
- Processes max 100 users per run
- Can be run periodically to catch stragglers

**Usage:**
```python
# Manual trigger via Flower or Django shell
from app.infrastructure.celery.app import celery_app
celery_app.send_task("create_missing_user_contexts")
```

**Scheduled:** Not scheduled (manual execution)

---

### 7. User Context Analytics

**Task Name:** `user_context_analytics`

**Location:** `src/app/infrastructure/celery/tasks/user_context_tasks.py:330-468`

**Function:**
```python
@celery_app.task(name="user_context_analytics")
def user_context_analytics():
```

**Purpose:**
Generate analytics report and persist snapshot to database.

**Workflow:**
1. Aggregate user distribution stats from `user_context_aware`
2. Calculate portfolio state distribution (empty, starter, active, whale)
3. Calculate activity level distribution (new, very_active, active, etc.)
4. Calculate user type distribution (new_user, casual, trader, etc.)
5. Get execution stats (total, swap, buy, lending, transfer, cashout)
6. Get total balance (USD) across all users
7. Create `AnalyticsSnapshot` entity
8. Persist to `analytics_snapshots` table
9. Log summary statistics for monitoring

**Analytics Snapshot Entity:** (Lines 403-440)
```python
snapshot = AnalyticsSnapshot(
    id=uuid4(),
    snapshot_date=date.today(),
    snapshot_type="daily",
    portfolio=PortfolioDistribution(
        empty=portfolio_stats.get("empty", 0),
        starter=portfolio_stats.get("starter", 0),
        active=portfolio_stats.get("active", 0),
        whale=portfolio_stats.get("whale", 0),
    ),
    activity=ActivityDistribution(
        new=activity_stats.get("new", 0),
        very_active=activity_stats.get("very_active", 0),
        active=activity_stats.get("active", 0),
        weekly_active=activity_stats.get("weekly_active", 0),
        monthly_active=activity_stats.get("monthly_active", 0),
        inactive=activity_stats.get("inactive", 0),
        reactivated=activity_stats.get("reactivated", 0),
    ),
    user_types=UserTypeDistribution(
        new_user=type_stats.get("new_user", 0),
        casual=type_stats.get("casual", 0),
        trader=type_stats.get("trader", 0),
        yield_farmer=type_stats.get("yield_farmer", 0),
        power_user=type_stats.get("power_user", 0),
    ),
    executions=ExecutionMetrics(
        total=exec_stats.get("total", 0),
        swap=exec_stats.get("swap", 0),
        buy=exec_stats.get("buy", 0),
        lending=exec_stats.get("lending", 0),
        transfer=exec_stats.get("transfer", 0),
        cashout=exec_stats.get("cashout", 0),
    ),
    total_users=total_users,
    total_balance_usd=total_balance,
)
```

**Scheduled:** Daily at 6:00 AM (Celery Beat)

**Logging:**
```
📊 Generating user context analytics and snapshot
📈 User Context Analytics (Total: {total})
Portfolio State Distribution:
  - empty: {count} ({percent}%)
  - starter: {count} ({percent}%)
  - active: {count} ({percent}%)
  - whale: {count} ({percent}%)
Activity Level Distribution:
  - new: {count} ({percent}%)
  - very_active: {count} ({percent}%)
  ...
User Type Distribution:
  - new_user: {count} ({percent}%)
  - casual: {count} ({percent}%)
  ...
✅ Analytics snapshot saved and logged
```

**Database Table:** `analytics_snapshots`

**Use Cases:**
- Daily dashboard metrics
- User growth tracking
- Portfolio distribution analysis
- Activity trend monitoring

---

## Task Configuration

### Celery App Configuration

**Location:** `src/app/infrastructure/celery/app.py`

**Broker URL:**
```python
broker_url = settings.celery.broker_url
# Example: "redis://localhost:6379/0"
```

**Result Backend:**
```python
result_backend = settings.celery.result_backend
# Example: "redis://localhost:6379/0"
```

**Task Serializer:**
```python
task_serializer = "json"
accept_content = ["json"]
result_serializer = "json"
```

**Timezone:**
```python
timezone = "UTC"
enable_utc = True
```

**Task Settings:**
```python
task_track_started = True              # Track task start time
task_acks_late = True                  # Acknowledge after completion
worker_prefetch_multiplier = 1         # One task at a time per worker
task_time_limit = 3600                 # 1 hour hard limit
task_soft_time_limit = 3000            # 50 minutes soft limit
```

---

## Queue Routing

**Configuration:** `src/app/infrastructure/celery/app.py`

### Default Queue
**Queue Name:** `celery` (default)

**Tasks:** All tasks not explicitly routed

---

### Email Queue
**Queue Name:** `email`

**Routing:** (Lines in `app.py`)
```python
task_routes = {
    "tasks.email_tasks.*": {"queue": "email"},
}
```

**Tasks:**
- `tasks.email_tasks.send_email`
- `tasks.email_tasks.send_verification_email`
- `tasks.email_tasks.send_password_reset_email`
- `tasks.email_tasks.send_password_change_notification`

**Dedicated Workers:**
```bash
# Start email queue worker
celery -A app.infrastructure.celery.app worker --queue email --concurrency 2
```

**Rationale:**
- Isolate email sending from other tasks
- Prevent email failures from blocking other tasks
- Dedicated concurrency for email throughput

---

### User Context Queue (Default)
**Queue Name:** `celery` (default queue)

**Tasks:**
- `update_user_context`
- `create_missing_user_contexts`
- `user_context_analytics`

**Rationale:**
- Uses default queue for now
- Can be moved to dedicated queue if needed

---

## Monitoring & Retry Policies

### Flower (Task Monitoring)

**Start Flower:**
```bash
make celery.flower
# Or: celery -A app.infrastructure.celery.app flower --port=5555
```

**Access:** `http://localhost:5555`

**Features:**
- Real-time task monitoring
- Task history and results
- Worker status and performance
- Task execution graphs
- Manual task triggering

---

### Retry Policy

**Default Retry:** (Lines in `app.py`)
```python
task_autoretry_for = (Exception,)
task_retry_kwargs = {"max_retries": 3}
task_retry_backoff = True              # Exponential backoff
task_retry_backoff_max = 600           # Max 10 minutes
task_retry_jitter = True               # Add randomness
```

**Exponential Backoff:**
- Attempt 1: Immediate
- Attempt 2: ~4 seconds
- Attempt 3: ~16 seconds
- Attempt 4: ~64 seconds (with jitter)

**Email Task Retry:**
Email tasks have **custom behavior**:
- **No automatic retry** (handled gracefully)
- Logs warnings on failure
- Does not raise exceptions
- Non-blocking for user flows

**Rationale:**
- Email failures should not block sign up/login
- Users can resend verification emails manually
- Monitoring alerts on repeated failures

---

### Task Result Persistence

**Configuration:**
```python
result_backend = "redis://localhost:6379/0"
result_expires = 86400  # 24 hours
```

**Result Storage:**
- Task results stored in Redis
- Expires after 24 hours
- Used for task status queries

**Query Task Result:**
```python
from app.infrastructure.celery.app import celery_app

result = celery_app.AsyncResult(task_id)
if result.ready():
    print(result.result)
else:
    print(result.state)  # PENDING, STARTED, SUCCESS, FAILURE
```

---

### Error Tracking

**Sentry Integration:** (if configured)
```python
# In celery app.py
import sentry_sdk
from sentry_sdk.integrations.celery import CeleryIntegration

sentry_sdk.init(
    dsn=settings.sentry.dsn,
    integrations=[CeleryIntegration()],
)
```

**Error Notifications:**
- Task failures sent to Sentry
- Email alerts for critical errors
- Slack notifications (if configured)

---

## Scheduled Tasks (Celery Beat)

**Celery Beat** schedules periodic tasks.

**Configuration:** `src/app/infrastructure/celery/app.py`

### Beat Schedule

```python
beat_schedule = {
    "update-user-context-every-10-minutes": {
        "task": "update_user_context",
        "schedule": crontab(minute="*/10"),  # Every 10 minutes
    },
    "user-context-analytics-daily": {
        "task": "user_context_analytics",
        "schedule": crontab(hour=6, minute=0),  # Daily at 6:00 AM UTC
    },
}
```

---

### Task: Update User Context

**Schedule:** Every 10 minutes

**Cron Expression:** `*/10 * * * *`

**Task Name:** `update_user_context`

**Purpose:**
- Create missing user contexts (max 30 per run)
- Update existing user contexts (max 100 per run)
- Keeps user classifications fresh for AI agents

**Execution Time:** ~5-30 seconds (depends on user count)

**Monitoring:**
- Check Flower for task history
- Monitor logs for errors
- Track success rate in Sentry

---

### Task: User Context Analytics

**Schedule:** Daily at 6:00 AM UTC

**Cron Expression:** `0 6 * * *`

**Task Name:** `user_context_analytics`

**Purpose:**
- Generate daily analytics snapshot
- Calculate user distribution stats
- Store in `analytics_snapshots` table

**Execution Time:** ~1-5 seconds

**Use Cases:**
- Admin dashboard metrics
- Daily email reports
- Growth trend analysis

---

### Start Celery Beat

**Command:**
```bash
make celery.beat
# Or: celery -A app.infrastructure.celery.app beat --loglevel=info
```

**Important:**
- **Only run ONE beat instance** (prevents duplicate task execution)
- Beat schedule is stored in `celerybeat-schedule` file
- Beat and workers can run on separate servers

---

## Development Commands

### Start Celery Worker

```bash
# Default worker (all queues)
make celery.worker

# Email queue worker
celery -A app.infrastructure.celery.app worker --queue email --concurrency 2

# Multiple queues
celery -A app.infrastructure.celery.app worker --queues celery,email --concurrency 4
```

---

### Start Celery Beat

```bash
make celery.beat

# With custom schedule file
celery -A app.infrastructure.celery.app beat --schedule=/tmp/celerybeat-schedule
```

---

### Start Flower (Monitoring)

```bash
make celery.flower

# Custom port
celery -A app.infrastructure.celery.app flower --port=5555 --address=0.0.0.0
```

---

### Manual Task Trigger

**Python Shell:**
```python
from app.infrastructure.celery.app import celery_app

# Trigger email task
celery_app.send_task(
    "tasks.email_tasks.send_verification_email",
    kwargs={
        "to_email": "test@example.com",
        "verification_url": "test-token-123",
    },
)

# Trigger user context update
celery_app.send_task("update_user_context")

# Get task result
result = celery_app.send_task("update_user_context")
print(result.get(timeout=60))  # Wait up to 60 seconds
```

---

### View Active Tasks

**Flower:** `http://localhost:5555/tasks`

**Command Line:**
```bash
celery -A app.infrastructure.celery.app inspect active
celery -A app.infrastructure.celery.app inspect scheduled
celery -A app.infrastructure.celery.app inspect registered
```

---

### Purge Queue

**Warning:** This deletes all pending tasks!

```bash
# Purge all queues
celery -A app.infrastructure.celery.app purge

# Purge specific queue
celery -A app.infrastructure.celery.app purge --queue email
```

---

## Production Deployment

### Systemd Service (Worker)

**File:** `/etc/systemd/system/celery-worker.service`

```ini
[Unit]
Description=Celery Worker
After=network.target redis.target

[Service]
Type=forking
User=ubuntu
Group=ubuntu
WorkingDirectory=/home/ubuntu/anvil_backend
Environment="PATH=/home/ubuntu/anvil_backend/.venv/bin"
Environment="APP_ENV=prod"
ExecStart=/home/ubuntu/anvil_backend/.venv/bin/celery -A app.infrastructure.celery.app worker \
    --loglevel=info \
    --logfile=/var/log/celery/worker.log \
    --pidfile=/var/run/celery/worker.pid \
    --detach
ExecStop=/bin/kill -s TERM $MAINPID
Restart=always

[Install]
WantedBy=multi-user.target
```

---

### Systemd Service (Beat)

**File:** `/etc/systemd/system/celery-beat.service`

```ini
[Unit]
Description=Celery Beat
After=network.target redis.target

[Service]
Type=forking
User=ubuntu
Group=ubuntu
WorkingDirectory=/home/ubuntu/anvil_backend
Environment="PATH=/home/ubuntu/anvil_backend/.venv/bin"
Environment="APP_ENV=prod"
ExecStart=/home/ubuntu/anvil_backend/.venv/bin/celery -A app.infrastructure.celery.app beat \
    --loglevel=info \
    --logfile=/var/log/celery/beat.log \
    --pidfile=/var/run/celery/beat.pid \
    --detach
ExecStop=/bin/kill -s TERM $MAINPID
Restart=always

[Install]
WantedBy=multi-user.target
```

---

### Enable and Start Services

```bash
sudo systemctl daemon-reload
sudo systemctl enable celery-worker celery-beat
sudo systemctl start celery-worker celery-beat
sudo systemctl status celery-worker celery-beat
```

---

### Monitoring Logs

```bash
# Worker logs
sudo journalctl -u celery-worker -f

# Beat logs
sudo journalctl -u celery-beat -f

# Tail log files
tail -f /var/log/celery/worker.log
tail -f /var/log/celery/beat.log
```

---

## Task Execution Statistics

### Email Tasks (Estimated)

| Task | Frequency | Duration | Priority |
|------|-----------|----------|----------|
| Send Verification Email | ~10-50/day | 1-3 seconds | Medium |
| Send Password Reset Email | ~5-20/day | 1-3 seconds | High |
| Send Password Change Notification | ~2-10/day | 1-3 seconds | High |
| Generic Send Email | ~20-100/day | 1-3 seconds | Low |

---

### User Context Tasks (Estimated)

| Task | Frequency | Duration | Priority |
|------|-----------|----------|----------|
| Update User Context | Every 10 minutes | 5-30 seconds | Medium |
| User Context Analytics | Daily at 6 AM | 1-5 seconds | Low |
| Create Missing Contexts | Manual | 2-10 seconds | Low |

---

### Resource Usage

**Worker Memory:** ~100-200 MB per worker process

**Worker CPU:** Low (email tasks are I/O bound)

**Redis Memory:** ~10-50 MB for task queue and results

**Recommended Worker Count:**
- Development: 2 workers
- Staging: 4 workers
- Production: 8-16 workers (depending on load)

---

**End of Document**
