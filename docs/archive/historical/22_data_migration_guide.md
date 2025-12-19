# 🔄 Anvil Platform - Data Migration Guide

## Database Schema Changes & Data Migrations

**Version:** 1.0  
**Date:** November 2025  
**Audience:** Backend Developers, DevOps

---

## 🎯 Overview

This guide covers all aspects of database migrations including schema changes, data transformations, and best practices for zero-downtime deployments.

---

## 🛠️ Migration Tools

### Alembic (SQLAlchemy Migrations)

**Setup:**
```python
# alembic/env.py
from app.core.database import Base
from app.models import *  # Import all models

target_metadata = Base.metadata

def run_migrations_online():
    """Run migrations in 'online' mode."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True
        )

        with context.begin_transaction():
            context.run_migrations()
```

---

## 📋 Migration Workflow

### 1. Create Migration

```bash
# Auto-generate migration from model changes
alembic revision --autogenerate -m "add user subscription tier"

# Create empty migration for manual changes
alembic revision -m "migrate old transaction data"

# Result: Creates file in alembic/versions/
# Example: 001_add_user_subscription_tier.py
```

### 2. Review Generated Migration

```python
# alembic/versions/001_add_user_subscription_tier.py
"""add user subscription tier

Revision ID: 001
Revises: 
Create Date: 2025-11-17 10:00:00

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = '001'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    """Apply migration."""
    op.add_column('users',
        sa.Column('subscription_tier', 
                  sa.String(20), 
                  nullable=False,
                  server_default='free')
    )
    
    # Create index
    op.create_index('idx_users_subscription_tier',
                    'users',
                    ['subscription_tier'])

def downgrade():
    """Revert migration."""
    op.drop_index('idx_users_subscription_tier', 'users')
    op.drop_column('users', 'subscription_tier')
```

### 3. Test Migration

```bash
# Test on local database
alembic upgrade head

# Verify schema
mysql -u root -p anvil_dev -e "DESCRIBE users;"

# Test rollback
alembic downgrade -1

# Re-apply
alembic upgrade head
```

### 4. Deploy to Staging

```bash
# On staging server
cd /app
source venv/bin/activate

# Backup database first
./scripts/backup_database.sh

# Run migration
alembic upgrade head

# Verify
python scripts/verify_migration.py
```

### 5. Deploy to Production

```bash
# ALWAYS backup first!
./scripts/backup_database.sh

# Run migration
alembic upgrade head

# Monitor
tail -f /var/log/anvil/migration.log
```

---

## 🔧 Common Migration Patterns

### Adding a Column

**Without Default (NOT NULL will fail on existing rows):**
```python
def upgrade():
    # Step 1: Add column as nullable first
    op.add_column('users',
        sa.Column('phone_number', sa.String(20), nullable=True)
    )
    
    # Step 2: Backfill data if needed
    op.execute("""
        UPDATE users 
        SET phone_number = '' 
        WHERE phone_number IS NULL
    """)
    
    # Step 3: Make NOT NULL
    op.alter_column('users', 'phone_number',
                    nullable=False,
                    existing_type=sa.String(20))
```

**With Default (Safe):**
```python
def upgrade():
    op.add_column('users',
        sa.Column('email_verified', 
                  sa.Boolean(),
                  nullable=False,
                  server_default='0')  # Default false
    )
```

---

### Renaming a Column

**Zero-Downtime Approach:**
```python
# Migration 1: Add new column
def upgrade():
    op.add_column('users',
        sa.Column('email_address', sa.String(255))
    )
    
    # Copy data from old to new
    op.execute("""
        UPDATE users 
        SET email_address = email
    """)
    
    # Make NOT NULL after backfill
    op.alter_column('users', 'email_address',
                    nullable=False)

# Migration 2 (after deployment): Remove old column
def upgrade():
    op.drop_column('users', 'email')
```

**Alternative (requires downtime):**
```python
def upgrade():
    op.alter_column('users', 'email',
                    new_column_name='email_address')
```

---

### Changing Column Type

**Safe Approach:**
```python
def upgrade():
    # For PostgreSQL
    op.alter_column('transactions', 'amount',
                    type_=sa.Numeric(precision=36, scale=18),
                    existing_type=sa.Numeric(precision=18, scale=8))
    
    # For MySQL
    op.execute("""
        ALTER TABLE transactions 
        MODIFY COLUMN amount DECIMAL(36,18)
    """)
```

**Zero-Downtime for Complex Changes:**
```python
# Step 1: Add new column
def upgrade():
    op.add_column('transactions',
        sa.Column('amount_new', sa.Numeric(36,18))
    )
    
    # Copy and transform data
    op.execute("""
        UPDATE transactions 
        SET amount_new = CAST(amount AS DECIMAL(36,18))
    """)

# Step 2 (after deployment): Drop old, rename new
def upgrade():
    op.drop_column('transactions', 'amount')
    op.alter_column('transactions', 'amount_new',
                    new_column_name='amount')
```

---

### Adding Foreign Key

```python
def upgrade():
    # Add column first
    op.add_column('transactions',
        sa.Column('wallet_id', sa.Integer(), nullable=True)
    )
    
    # Backfill data
    op.execute("""
        UPDATE transactions t
        JOIN users u ON t.user_id = u.id
        SET t.wallet_id = u.wallet_id
    """)
    
    # Make NOT NULL
    op.alter_column('transactions', 'wallet_id',
                    nullable=False)
    
    # Add foreign key constraint
    op.create_foreign_key(
        'fk_transactions_wallet',
        'transactions', 'wallets',
        ['wallet_id'], ['id']
    )
    
    # Add index
    op.create_index('idx_transactions_wallet',
                    'transactions', ['wallet_id'])
```

---

### Creating Index

```python
def upgrade():
    # Simple index
    op.create_index('idx_users_email',
                    'users',
                    ['email'])
    
    # Composite index
    op.create_index('idx_transactions_user_date',
                    'transactions',
                    ['user_id', 'created_at'],
                    unique=False)
    
    # Unique index
    op.create_index('idx_users_email_unique',
                    'users',
                    ['email'],
                    unique=True)
    
    # Partial index (PostgreSQL)
    op.create_index('idx_transactions_pending',
                    'transactions',
                    ['user_id', 'created_at'],
                    postgresql_where=sa.text("status = 'pending'"))
```

---

### Dropping Table

**Safe Approach:**
```python
# Step 1: Drop foreign keys referencing this table
def upgrade():
    op.drop_constraint('fk_table_ref', 'other_table')

# Step 2: Drop the table
def upgrade():
    # Backup data first!
    op.execute("""
        CREATE TABLE old_table_backup AS 
        SELECT * FROM old_table
    """)
    
    op.drop_table('old_table')
```

---

## 📊 Data Transformations

### Complex Data Migration

```python
# alembic/versions/002_migrate_transaction_data.py
"""migrate transaction data to new format

Revision ID: 002
"""

def upgrade():
    # Add new columns
    op.add_column('transactions',
        sa.Column('from_asset', sa.String(10))
    )
    op.add_column('transactions',
        sa.Column('to_asset', sa.String(10))
    )
    
    # Migrate data in batches (important for large tables!)
    connection = op.get_bind()
    
    batch_size = 1000
    offset = 0
    
    while True:
        # Fetch batch
        result = connection.execute(f"""
            SELECT id, metadata 
            FROM transactions 
            LIMIT {batch_size} OFFSET {offset}
        """)
        
        rows = result.fetchall()
        if not rows:
            break
        
        # Transform and update
        for row in rows:
            metadata = json.loads(row.metadata)
            
            connection.execute(f"""
                UPDATE transactions 
                SET from_asset = '{metadata.get('from')}',
                    to_asset = '{metadata.get('to')}'
                WHERE id = {row.id}
            """)
        
        offset += batch_size
        
        # Log progress
        print(f"Migrated {offset} rows...")
    
    # Make columns NOT NULL after backfill
    op.alter_column('transactions', 'from_asset', nullable=False)
    op.alter_column('transactions', 'to_asset', nullable=False)
```

---

### Data Cleanup Migration

```python
def upgrade():
    """Clean up duplicate and invalid data."""
    
    # Remove duplicates
    op.execute("""
        DELETE t1 FROM transactions t1
        INNER JOIN transactions t2 
        WHERE t1.id > t2.id 
        AND t1.tx_hash = t2.tx_hash
    """)
    
    # Fix invalid data
    op.execute("""
        UPDATE users 
        SET email = LOWER(TRIM(email))
        WHERE email != LOWER(TRIM(email))
    """)
    
    # Remove orphaned records
    op.execute("""
        DELETE FROM token_balances
        WHERE wallet_id NOT IN (SELECT id FROM wallets)
    """)
```

---

## 🔄 Zero-Downtime Migrations

### Expand-Contract Pattern

**Phase 1: Expand (Add new schema)**
```python
# Migration 1: Add new columns
def upgrade():
    op.add_column('users',
        sa.Column('full_name', sa.String(255))
    )
    
# Deploy code that writes to BOTH old and new columns
```

**Phase 2: Migrate Data**
```python
# Migration 2: Backfill data
def upgrade():
    op.execute("""
        UPDATE users 
        SET full_name = CONCAT(firstname, ' ', lastname)
        WHERE full_name IS NULL
    """)
```

**Phase 3: Contract (Remove old schema)**
```python
# Migration 3: Remove old columns
def upgrade():
    op.drop_column('users', 'firstname')
    op.drop_column('users', 'lastname')

# Deploy code that only uses new column
```

---

## 🚨 Migration Best Practices

### DO's

```yaml
✅ Always backup before migration:
   - Automated snapshot
   - Manual backup
   - Verify backup works

✅ Test migrations thoroughly:
   - Test on local
   - Test on staging
   - Test rollback

✅ Use transactions:
   - Wrap in BEGIN/COMMIT
   - Ensure atomicity
   - Rollback on error

✅ Add indexes AFTER data:
   - Insert data first
   - Then create indexes
   - Much faster

✅ Monitor during migration:
   - Watch query times
   - Check error logs
   - Monitor resources

✅ Document migrations:
   - Why change is needed
   - What changed
   - Rollback procedure
```

### DON'Ts

```yaml
❌ Never migrate on Friday
❌ Don't skip staging testing
❌ Don't assume backups work (verify!)
❌ Don't ignore warnings
❌ Don't migrate during peak hours
❌ Don't forget to communicate
❌ Don't rush
```

---

## 📋 Migration Checklist

### Pre-Migration

```yaml
- [ ] Migration tested on local
- [ ] Migration tested on staging
- [ ] Backup strategy verified
- [ ] Rollback plan documented
- [ ] Team notified
- [ ] Maintenance window scheduled (if needed)
- [ ] Monitoring alerts active
```

### During Migration

```yaml
- [ ] Database backup created
- [ ] Migration started
- [ ] Progress monitored
- [ ] Errors logged
- [ ] Performance monitored
```

### Post-Migration

```yaml
- [ ] Migration completed successfully
- [ ] Application functioning normally
- [ ] Data integrity verified
- [ ] Performance acceptable
- [ ] Team notified
- [ ] Documentation updated
```

---

## 🔍 Verification Scripts

### Verify Migration Success

```python
# scripts/verify_migration.py
import sys
from app.core.database import SessionLocal
from sqlalchemy import inspect, text

def verify_migration():
    """Verify migration completed successfully."""
    db = SessionLocal()
    
    try:
        # Check schema
        inspector = inspect(db.bind)
        
        # Verify table exists
        tables = inspector.get_table_names()
        assert 'transactions' in tables, "transactions table missing"
        
        # Verify columns
        columns = [c['name'] for c in inspector.get_columns('transactions')]
        assert 'from_asset' in columns, "from_asset column missing"
        assert 'to_asset' in columns, "to_asset column missing"
        
        # Verify indexes
        indexes = inspector.get_indexes('transactions')
        index_names = [idx['name'] for idx in indexes]
        assert 'idx_transactions_user_date' in index_names
        
        # Verify data integrity
        result = db.execute(text("""
            SELECT COUNT(*) as count
            FROM transactions
            WHERE from_asset IS NULL OR to_asset IS NULL
        """))
        
        null_count = result.scalar()
        assert null_count == 0, f"Found {null_count} rows with NULL values"
        
        print("✅ Migration verification passed!")
        return True
        
    except AssertionError as e:
        print(f"❌ Migration verification failed: {e}")
        return False
    finally:
        db.close()

if __name__ == "__main__":
    success = verify_migration()
    sys.exit(0 if success else 1)
```

---

## 🚑 Rollback Procedures

### Automatic Rollback

```bash
# Rollback last migration
alembic downgrade -1

# Rollback to specific version
alembic downgrade <revision>

# Rollback all
alembic downgrade base
```

### Manual Rollback

```sql
-- If migration failed mid-way, manual cleanup may be needed

-- Restore from backup
mysql -u root -p anvil_production < backup_before_migration.sql

-- Or restore specific table
DROP TABLE transactions;
CREATE TABLE transactions LIKE transactions_backup;
INSERT INTO transactions SELECT * FROM transactions_backup;
```

---

## 📊 Large Table Migrations

### Strategies for Tables with Millions of Rows

**1. Batch Processing:**
```python
def upgrade():
    """Migrate large table in batches."""
    connection = op.get_bind()
    
    batch_size = 10000
    offset = 0
    total_rows = connection.execute("SELECT COUNT(*) FROM large_table").scalar()
    
    while offset < total_rows:
        connection.execute(f"""
            UPDATE large_table
            SET new_column = some_calculation(old_column)
            WHERE id BETWEEN {offset} AND {offset + batch_size}
        """)
        
        offset += batch_size
        progress = (offset / total_rows) * 100
        print(f"Progress: {progress:.1f}%")
```

**2. Shadow Table:**
```python
def upgrade():
    """Use shadow table for large migrations."""
    
    # Create new table with correct schema
    op.execute("""
        CREATE TABLE transactions_new LIKE transactions
    """)
    
    # Add new columns
    op.execute("""
        ALTER TABLE transactions_new 
        ADD COLUMN from_asset VARCHAR(10),
        ADD COLUMN to_asset VARCHAR(10)
    """)
    
    # Copy data (can be done gradually)
    op.execute("""
        INSERT INTO transactions_new
        SELECT *, 
               JSON_EXTRACT(metadata, '$.from') as from_asset,
               JSON_EXTRACT(metadata, '$.to') as to_asset
        FROM transactions
    """)
    
    # Atomic swap
    op.execute("RENAME TABLE transactions TO transactions_old, transactions_new TO transactions")
```

**3. Online Schema Change (pt-online-schema-change):**
```bash
# For very large tables, use Percona Toolkit
pt-online-schema-change \
  --alter "ADD COLUMN new_column VARCHAR(255)" \
  D=anvil_production,t=transactions \
  --execute
```

---

## 📖 References

```yaml
Tools:
  Alembic: https://alembic.sqlalchemy.org/
  Percona Toolkit: https://www.percona.com/software/database-tools/percona-toolkit

Documentation:
  SQLAlchemy: https://docs.sqlalchemy.org/
  MySQL ALTER TABLE: https://dev.mysql.com/doc/refman/8.0/en/alter-table.html

Best Practices:
  - GitHub's online migrations: https://github.blog/2014-05-29-move-fast/
  - Stripe's schema migrations: https://stripe.com/blog/online-migrations
```

---

**Document Version:** 1.0  
**Last Updated:** November 2025  
**Maintained By:** Backend Team  
**Review:** Before each major migration
