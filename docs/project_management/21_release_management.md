# 🚀 Anvil Platform - Release Management Guide

## Version Control, Release Process & Change Management

**Version:** 1.0  
**Date:** November 2025  
**Audience:** Engineering Team, DevOps

---

## 🎯 Release Strategy

### Release Types

```yaml
Hotfix Release:
  Frequency: As needed
  Scope: Critical bug fixes only
  Approval: CTO
  Timeline: <4 hours
  Example: Security vulnerability, data loss bug

Patch Release (x.x.X):
  Frequency: Weekly
  Scope: Bug fixes, minor improvements
  Approval: Tech Lead
  Timeline: 1-2 days
  Example: UI bug, minor performance fix

Minor Release (x.X.0):
  Frequency: Bi-weekly
  Scope: New features, enhancements
  Approval: Product + Tech Lead
  Timeline: 1 week (includes testing)
  Example: New earn protocol, UI redesign

Major Release (X.0.0):
  Frequency: Quarterly
  Scope: Breaking changes, major features
  Approval: Executive team
  Timeline: 2-4 weeks
  Example: New product line, architecture change
```

---

## 📋 Versioning System

### Semantic Versioning (SemVer)

**Format:** MAJOR.MINOR.PATCH

```yaml
MAJOR (X.0.0):
  - Breaking API changes
  - Major architecture changes
  - Database schema breaking changes
  - Examples: 1.0.0 → 2.0.0

MINOR (x.X.0):
  - New features (backward compatible)
  - New API endpoints
  - New database tables
  - Examples: 1.0.0 → 1.1.0

PATCH (x.x.X):
  - Bug fixes
  - Performance improvements
  - Security patches
  - Examples: 1.0.0 → 1.0.1
```

### Version Numbers by Component

```yaml
Backend API: 1.2.3
Mobile App (iOS): 1.2.3 (build 45)
Mobile App (Android): 1.2.3 (build 45)
Admin Portal: 1.2.3
Database Schema: 1.2.3
```

---

## 🔄 Release Process

### 1. Planning Phase

**Inputs:**
- Product roadmap
- Bug reports
- Customer feedback
- Technical debt items

**Activities:**
```yaml
1. Create Release Ticket:
   - Jira: ANV-RELEASE-XXX
   - Title: "Release v1.2.0"
   - Target date: 2025-11-20

2. Define Scope:
   - List all features/fixes
   - Prioritize items
   - Identify dependencies

3. Risk Assessment:
   - Breaking changes?
   - Database migrations?
   - Third-party dependencies?
   - Rollback complexity?

4. Resource Planning:
   - Developer assignments
   - QA resources
   - DevOps availability
```

---

### 2. Development Phase

**Branch Strategy (Git Flow):**

```bash
# Main branches
main          # Production releases
develop       # Integration branch

# Supporting branches
feature/*     # New features
bugfix/*      # Bug fixes
hotfix/*      # Production hotfixes
release/*     # Release preparation

# Example workflow
git checkout develop
git checkout -b feature/add-save-feature

# ... develop feature ...

git checkout develop
git merge feature/add-save-feature
git push origin develop
```

**Branch Naming:**
```bash
feature/ANV-123-add-swap-slippage
bugfix/ANV-456-fix-wallet-balance
hotfix/ANV-789-security-patch
release/v1.2.0
```

**Commit Message Format:**
```
type(scope): subject

body

footer

# Examples:
feat(swap): add slippage tolerance selector

Allow users to set custom slippage (0.1%-5%) when executing swaps.
Default remains 0.5%.

Closes ANV-123

fix(wallet): correct balance calculation for USDC

The balance was not accounting for pending transactions.
This fix includes pending balances in the display.

Fixes ANV-456
```

---

### 3. Testing Phase

**Testing Checklist:**

```yaml
Unit Tests:
  - [ ] All tests passing
  - [ ] Code coverage >80%
  - [ ] New tests for new code

Integration Tests:
  - [ ] API tests passing
  - [ ] Database migrations tested
  - [ ] External API mocks working

E2E Tests:
  - [ ] Critical user flows tested
  - [ ] Mobile app smoke tests
  - [ ] Admin portal tested

Performance Tests:
  - [ ] Load testing completed
  - [ ] No performance regression
  - [ ] P95 latency <500ms

Security Tests:
  - [ ] OWASP top 10 checked
  - [ ] Dependency scan clean
  - [ ] No secrets in code

Manual Testing:
  - [ ] Feature walkthrough by PM
  - [ ] Edge cases tested
  - [ ] Error handling verified
```

**Test Environments:**

```yaml
Development:
  URL: https://dev-api.anvil.com
  Purpose: Feature testing
  Data: Fake/test data

Staging:
  URL: https://staging-api.anvil.com
  Purpose: Pre-production validation
  Data: Anonymized production copy

Production:
  URL: https://api.anvil.com
  Purpose: Live system
  Data: Real user data
```

---

### 4. Release Preparation

**Create Release Branch:**
```bash
# From develop
git checkout develop
git pull origin develop
git checkout -b release/v1.2.0

# Update version numbers
# Backend: app/__init__.py
__version__ = "1.2.0"

# Mobile: package.json
{
  "version": "1.2.0",
  "build": "45"
}

# Admin: package.json
{
  "version": "1.2.0"
}

# Commit version bump
git add .
git commit -m "chore: bump version to 1.2.0"
git push origin release/v1.2.0
```

**Create Release Notes:**

```markdown
# Release v1.2.0 - November 20, 2025

## 🎉 New Features
- **Save Feature**: Automated DCA schedules for recurring investments
- **Enhanced AI Chat**: Improved context awareness and faster responses
- **Portfolio Analytics**: New analytics dashboard with custom date ranges

## 🐛 Bug Fixes
- Fixed wallet balance display for USDC pending transactions
- Corrected APY calculations for Aave positions
- Improved error handling for failed swaps

## 🔧 Improvements
- Reduced API response times by 30%
- Enhanced mobile app performance
- Updated UI components for better accessibility

## 🔐 Security
- Updated dependencies with security patches
- Enhanced rate limiting for auth endpoints

## ⚠️ Breaking Changes
None

## 📋 Migration Notes
- Database migration required (see MIGRATION.md)
- New environment variables needed (see .env.example)

## 🔗 Links
- [Full Changelog](https://github.com/anvil/anvil/compare/v1.1.0...v1.2.0)
- [Documentation](https://docs.anvil.com/v1.2.0)
```

---

### 5. Deployment Phase

**Deployment Checklist:**

```yaml
Pre-Deployment:
  - [ ] Release notes published
  - [ ] Team notified (Slack)
  - [ ] Maintenance window scheduled (if needed)
  - [ ] Rollback plan documented
  - [ ] Database backup verified
  - [ ] Monitoring alerts active

Deployment Steps:
  - [ ] Deploy to staging
  - [ ] Smoke tests on staging
  - [ ] Deploy to production
  - [ ] Monitor for 15 minutes
  - [ ] Verify key features
  - [ ] Check error rates

Post-Deployment:
  - [ ] Merge release to main
  - [ ] Tag release in Git
  - [ ] Update status page
  - [ ] Notify customers (if major)
  - [ ] Monitor for 24 hours
```

**Deployment Script:**

```bash
#!/bin/bash
# scripts/deploy_release.sh

set -e

VERSION="$1"
ENVIRONMENT="$2"

if [ -z "$VERSION" ] || [ -z "$ENVIRONMENT" ]; then
    echo "Usage: ./deploy_release.sh <version> <environment>"
    echo "Example: ./deploy_release.sh 1.2.0 production"
    exit 1
fi

echo "🚀 Deploying Anvil v$VERSION to $ENVIRONMENT"

# 1. Run database migrations
echo "📊 Running database migrations..."
python scripts/migrate.py --env $ENVIRONMENT

# 2. Build Docker images
echo "🐳 Building Docker images..."
docker build -t anvil-api:$VERSION .
docker tag anvil-api:$VERSION 123456789.dkr.ecr.us-east-1.amazonaws.com/anvil-api:$VERSION
docker push 123456789.dkr.ecr.us-east-1.amazonaws.com/anvil-api:$VERSION

# 3. Update ECS service
echo "☁️ Updating ECS service..."
aws ecs register-task-definition --cli-input-json file://task-definition-$VERSION.json
aws ecs update-service \
    --cluster anvil-$ENVIRONMENT \
    --service anvil-api \
    --task-definition anvil-api:$VERSION

# 4. Wait for deployment
echo "⏳ Waiting for deployment..."
aws ecs wait services-stable \
    --cluster anvil-$ENVIRONMENT \
    --services anvil-api

# 5. Run smoke tests
echo "✅ Running smoke tests..."
./scripts/smoke_tests.sh https://api-$ENVIRONMENT.anvil.com

# 6. Tag release
if [ "$ENVIRONMENT" = "production" ]; then
    git tag -a "v$VERSION" -m "Release v$VERSION"
    git push origin "v$VERSION"
fi

echo "✨ Deployment complete!"
echo "🔗 Monitor: https://console.aws.amazon.com/ecs/"
echo "📊 Metrics: https://grafana.anvil.com"
```

---

### 6. Post-Release

**Monitoring Period:**

```yaml
First Hour:
  - Watch error rates
  - Monitor P95 latency
  - Check user feedback
  - Verify new features

First Day:
  - Review analytics
  - Check performance metrics
  - Monitor support tickets
  - Collect team feedback

First Week:
  - Full metrics analysis
  - User satisfaction survey
  - Identify issues
  - Plan hotfixes if needed
```

**Release Retrospective:**

```yaml
Within 1 Week:
  - [ ] Schedule retrospective meeting
  - [ ] What went well?
  - [ ] What could be improved?
  - [ ] Action items for next release
  - [ ] Update process documentation
```

---

## 🔥 Hotfix Process

### When to Hotfix

**Critical Issues:**
- Security vulnerabilities
- Data loss bugs
- Complete feature failure
- Payment processing issues
- Legal/compliance issues

### Hotfix Workflow

```bash
# 1. Create hotfix branch from main
git checkout main
git pull origin main
git checkout -b hotfix/v1.2.1-security-patch

# 2. Fix the issue
# ... make changes ...

# 3. Test thoroughly
pytest tests/
./scripts/smoke_tests.sh

# 4. Bump version (patch)
# Update version to 1.2.1

# 5. Commit and push
git add .
git commit -m "fix(security): patch XSS vulnerability"
git push origin hotfix/v1.2.1-security-patch

# 6. Deploy immediately to production
./scripts/deploy_release.sh 1.2.1 production

# 7. Merge back to main and develop
git checkout main
git merge hotfix/v1.2.1-security-patch
git push origin main

git checkout develop
git merge hotfix/v1.2.1-security-patch
git push origin develop

# 8. Tag release
git tag -a v1.2.1 -m "Hotfix: Security patch"
git push origin v1.2.1

# 9. Delete hotfix branch
git branch -d hotfix/v1.2.1-security-patch
git push origin --delete hotfix/v1.2.1-security-patch
```

---

## 📱 Mobile App Releases

### App Store Submission

**iOS (TestFlight → App Store):**

```yaml
Development:
  1. Increment build number
  2. Build in Xcode
  3. Upload to TestFlight
  4. Internal testing

Beta Testing:
  1. Add external testers
  2. Collect feedback
  3. Fix critical issues
  4. Repeat if needed

Production:
  1. Create App Store submission
  2. Complete metadata
  3. Submit for review
  4. Monitor review status
  5. Release to App Store

Timeline: 1-3 days for review
```

**Android (Internal → Production):**

```yaml
Development:
  1. Increment versionCode
  2. Build release APK/AAB
  3. Upload to internal track
  4. Internal testing

Beta Testing:
  1. Promote to beta track
  2. Add beta testers
  3. Collect feedback
  4. Fix critical issues

Production:
  1. Promote to production track
  2. Gradual rollout (10% → 50% → 100%)
  3. Monitor crash rates
  4. Complete rollout

Timeline: Immediate (gradual rollout over 7 days)
```

### Mobile Version Management

```typescript
// app/config/version.ts
export const APP_VERSION = {
  major: 1,
  minor: 2,
  patch: 0,
  build: 45,
  
  // Semantic version string
  get version() {
    return `${this.major}.${this.minor}.${this.patch}`
  },
  
  // Full version with build
  get fullVersion() {
    return `${this.version} (${this.build})`
  },
  
  // Minimum supported API version
  minApiVersion: '1.2.0',
  
  // Check if update required
  isUpdateRequired(apiVersion: string): boolean {
    // Compare versions
    return compareVersions(this.minApiVersion, apiVersion) > 0
  }
}
```

---

## 📊 Release Metrics

### Track for Each Release

```yaml
Deployment Metrics:
  - Deployment duration
  - Rollback count
  - Failed deployments
  - Time to deploy

Quality Metrics:
  - Bugs found in production
  - Hotfixes required
  - Test coverage
  - Code review time

Performance Metrics:
  - API latency (before vs after)
  - Error rate (before vs after)
  - Database query time
  - Mobile app size

Business Metrics:
  - Feature adoption rate
  - User satisfaction
  - Support tickets
  - Revenue impact
```

---

## 🎯 Release Calendar

### Typical Release Schedule

```yaml
Week 1:
  Monday: Sprint planning
  Wednesday: Feature development starts
  Friday: Mid-sprint check-in

Week 2:
  Monday: Feature development continues
  Wednesday: Code freeze for non-critical
  Thursday: Create release branch
  Friday: Deploy to staging

Week 3:
  Monday: QA testing on staging
  Tuesday: Bug fixes
  Wednesday: Final testing
  Thursday: Deploy to production (morning)
  Friday: Monitor & hotfix if needed

Holidays:
  - No releases on Fridays (avoid weekend issues)
  - No releases week before holidays
  - No releases during major events
```

---

## ✅ Release Checklist Template

```markdown
# Release v[VERSION] Checklist

## Planning
- [ ] Release ticket created (ANV-RELEASE-XXX)
- [ ] Scope defined and approved
- [ ] Release notes drafted
- [ ] Dependencies identified
- [ ] Risk assessment completed

## Development
- [ ] All features merged to develop
- [ ] All tests passing
- [ ] Code review completed
- [ ] Documentation updated
- [ ] Version numbers bumped

## Testing
- [ ] Unit tests: PASS
- [ ] Integration tests: PASS
- [ ] E2E tests: PASS
- [ ] Performance tests: PASS
- [ ] Security scan: CLEAN
- [ ] Manual testing: PASS

## Pre-Deployment
- [ ] Release branch created
- [ ] Database migrations prepared
- [ ] Rollback plan documented
- [ ] Team notified
- [ ] Maintenance window scheduled
- [ ] Backup verified

## Deployment
- [ ] Deployed to staging
- [ ] Staging smoke tests: PASS
- [ ] Deployed to production
- [ ] Production smoke tests: PASS
- [ ] Monitoring active
- [ ] Key features verified

## Post-Deployment
- [ ] Release tagged in Git
- [ ] Release notes published
- [ ] Documentation updated
- [ ] Status page updated
- [ ] Customers notified
- [ ] Monitored for 24 hours
- [ ] Retrospective scheduled

## Issues (if any)
- [ ] List any issues found
- [ ] Document resolutions
- [ ] Create follow-up tickets
```

---

## 📖 References

```yaml
Tools:
  Version Control: GitHub
  CI/CD: GitHub Actions
  Project Management: Jira/Linear
  Release Notes: GitHub Releases
  Documentation: Confluence/Notion

Contacts:
  Release Manager: tech-lead@anvil.com
  DevOps: devops@anvil.com
  QA Lead: qa-lead@anvil.com
  Product: product@anvil.com
```

---

**Document Version:** 1.0  
**Last Updated:** November 2025  
**Maintained By:** Release Manager  
**Review:** After each major release
