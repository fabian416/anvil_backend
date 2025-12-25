# Logging and Monitoring Guide

## Overview

All development services automatically save logs to the `logs/` directory for monitoring and debugging.

## Log File Locations

```
logs/
├── fastapi.log                    # FastAPI server logs
└── celery/                        # Celery workers logs
    ├── maintenance.log            # Maintenance worker
    ├── agents.log                 # Agents worker
    ├── graph.log                  # Graph processing worker
    ├── distillation.log           # LLM distillation worker ⚠️
    ├── projects.log               # Projects worker
    ├── llm.log                    # LLM orchestration worker
    ├── transactions.log           # Blockchain transactions worker
    ├── risk.log                   # Risk monitoring worker
    ├── email.log                  # Email sending worker
    ├── beat.log                   # Celery Beat scheduler
    └── flower.log                 # Flower monitoring UI
```

⚠️ **Note**: The `distillation.log` file contains the telemetry aggregation task that was recently fixed.

## Makefile Commands

### Starting Services

```bash
make start-dev      # Start all development services with logging
make stop-dev       # Stop all development services
```

### Viewing Logs

```bash
# View all logs in real-time
make logs-all       # Tail all logs (FastAPI + Celery)
make logs-dev       # Alias for logs-all

# View specific service logs
make logs-fastapi   # Only FastAPI logs
make logs-celery    # Only Celery workers logs

# Advanced monitoring
make logs-tail      # Interactive monitor with color-coded prefixes
make logs-summary   # Show summary with error counts and recent activity
make logs-errors    # Search for errors across all logs
```

## Interactive Log Monitor

The `logs-tail` command provides an advanced monitoring interface:

```bash
make logs-tail
```

**Features:**
- Color-coded prefixes for each service
- Real-time updates from all services simultaneously
- Uses `multitail` if available (install with `sudo apt-get install multitail`)
- Fallback to colored `tail -f` if multitail not available

## Log Summary

Quick overview of all services:

```bash
make logs-summary
```

**Shows:**
- ✅ Service status
- 📊 File sizes
- ⚠️ Error counts
- 🕐 Last modification times
- 📝 Recent log entries
- 💾 Total disk usage

## Searching Logs

### Search for errors
```bash
make logs-errors
```

### Custom searches
```bash
# Search for specific text in FastAPI logs
grep "search_term" logs/fastapi.log

# Search across all logs
grep -r "search_term" logs/

# Search for errors in distillation worker
grep -i "error\|exception" logs/celery/distillation.log

# Get last 100 lines from a specific service
tail -n 100 logs/celery/agents.log
```

## Log Rotation

Logs can grow large over time. To manage log files:

```bash
# View log file sizes
du -sh logs/

# Clear old logs (be careful!)
rm logs/fastapi.log
rm logs/celery/*.log

# Archive logs before clearing
tar -czf logs-backup-$(date +%Y%m%d).tar.gz logs/
```

## Troubleshooting

### No logs appearing?

1. Check if services are running:
   ```bash
   ps aux | grep uvicorn
   ps aux | grep celery
   ```

2. Check log directory permissions:
   ```bash
   ls -la logs/
   ```

3. Check disk space:
   ```bash
   df -h
   ```

### Finding specific errors

```bash
# Count errors by service
for log in logs/celery/*.log; do
    echo "$log: $(grep -ic error $log)";
done

# Find recent errors (last hour)
find logs -name "*.log" -mmin -60 -exec grep -l "error" {} \;

# Get context around errors
grep -B 5 -A 5 "error" logs/celery/distillation.log
```

## Monitoring Tips

1. **Start services**: `make start-dev`
2. **In another terminal**: `make logs-tail` or `make logs-summary`
3. **Check for errors periodically**: `make logs-errors`

## Production Logging

For production environments, consider:

- Setting up log rotation with `logrotate`
- Forwarding logs to a centralized logging system (ELK, Grafana Loki, etc.)
- Setting up alerts for error patterns
- Implementing structured logging (JSON format)

## Recent Fixes

✅ **Distillation Telemetry Fixed** (2025-12-23):
- Created missing `distillation_telemetry_hourly` table
- Fixed column name mismatches in aggregation query
- Hourly aggregation task now runs without errors

Check `logs/celery/distillation.log` to monitor the telemetry aggregation task.
