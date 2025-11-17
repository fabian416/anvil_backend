# 👋 Anvil Platform - Developer Onboarding Guide

## Welcome to the Anvil Development Team!

**Version:** 1.0  
**Date:** November 2025  
**Your First Day Starts Here**

---

## 🎯 Welcome!

Welcome to Anvil! We're building a revolutionary DeFi trading platform that makes cryptocurrency accessible to everyone. This guide will help you get up to speed quickly.

### What You'll Learn

```yaml
Day 1:
  - Team introductions
  - Product overview
  - Environment setup
  - First commit

Week 1:
  - Codebase familiarity
  - First feature task
  - Team processes
  - Development workflow

Month 1:
  - Independent contributions
  - Code reviews
  - Team collaboration
  - Product knowledge
```

---

## 📚 Pre-Reading (Before Day 1)

### Essential Documents (1-2 hours)

**Priority Order:**
1. **[README](computer:///mnt/user-data/outputs/00_MASTER_INDEX.md)** - Start here! (15 min)
2. **[Product Requirements](computer:///mnt/user-data/outputs/13_product_requirements.md)** - Understand what we're building (30 min)
3. **[Technical Architecture](computer:///mnt/user-data/outputs/03_technical_architecture.md)** - System design (30 min)
4. **[User Stories](computer:///mnt/user-data/outputs/user_stories_for_devs.md)** - Features and requirements (20 min)

### Optional Reading (Day 1-2)
- **[API Endpoints](computer:///mnt/user-data/outputs/api_endpoints_for_devs.md)** - If you're backend focused
- **[Mobile Architecture](computer:///mnt/user-data/outputs/11_mobile_architecture.md)** - If you're mobile focused
- **[Code Style Guide](computer:///mnt/user-data/outputs/10_code_style_guide.md)** - Important for all developers

---

## 📅 Your First Day

### Morning (9 AM - 12 PM)

**9:00 AM - Team Introduction (30 min)**
```yaml
Who You'll Meet:
  - CTO (Matias)
  - Tech Lead
  - Product Manager
  - Your immediate team
  - Other developers

What to Expect:
  - Overview of team structure
  - Introduction to team culture
  - Questions and answers
```

**9:30 AM - Product Demo (30 min)**
```yaml
Your Manager Will:
  - Demo the current mobile app
  - Show key features
  - Explain user flows
  - Answer product questions

Your Goal:
  - Understand the product vision
  - See features in action
  - Ask clarifying questions
```

**10:00 AM - Coffee Break & Office Tour** ☕

**10:15 AM - Access Setup (1 hour)**
```yaml
Accounts to Create:
  - [ ] GitHub organization access
  - [ ] Slack workspace access
  - [ ] Jira/Linear (project management)
  - [ ] AWS console access (read-only initially)
  - [ ] Sentry account
  - [ ] 1Password/secrets management

Tools to Install:
  - [ ] Slack desktop app
  - [ ] Git and GitHub Desktop (optional)
  - [ ] VS Code + extensions
  - [ ] Docker Desktop
  - [ ] Postman or Insomnia
  - [ ] DBeaver or TablePlus (database client)

Access Your Manager Will Grant:
  - Slack channels (#general, #engineering, #your-team)
  - GitHub repository access
  - Development environment credentials
  - VPN access (if remote)
```

**11:15 AM - Development Environment Setup (45 min)**

Follow the **[Environment Setup Guide](computer:///mnt/user-data/outputs/09_environment_setup_guide.md)**

```bash
# Clone the repositories
git clone git@github.com:anvil/anvil-backend.git
git clone git@github.com:anvil/anvil-mobile.git
git clone git@github.com:anvil/anvil-admin.git

# Setup backend
cd anvil-backend
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with development credentials

# Setup mobile
cd ../anvil-mobile
npm install
cd ios && pod install && cd ..
cp .env.example .env

# Setup admin
cd ../anvil-admin
npm install
cp .env.example .env.local
```

### Afternoon (1 PM - 5 PM)

**1:00 PM - Lunch with Team** 🍕

**2:00 PM - Codebase Tour (1 hour)**
```yaml
Your Tech Lead Will:
  - Walk through project structure
  - Explain key files and folders
  - Show how features are organized
  - Demonstrate development workflow

Backend Focus:
  - app/api/ - API endpoints
  - app/models/ - Database models
  - app/services/ - Business logic
  - app/integrations/ - External APIs

Mobile Focus:
  - src/screens/ - Screen components
  - src/components/ - Reusable components
  - src/services/api/ - API calls
  - src/store/ - State management
```

**3:00 PM - Your First Task (2 hours)**

**Starter Task: Fix a "Good First Issue"**

```yaml
Goal:
  Complete your first contribution

Steps:
  1. Find issue labeled "good-first-issue" in GitHub
  2. Assign it to yourself
  3. Create feature branch: git checkout -b fix/issue-123
  4. Make changes
  5. Write/update tests
  6. Create pull request
  7. Address code review feedback

Common First Issues:
  - Update documentation
  - Add unit test
  - Fix minor UI bug
  - Add validation to endpoint
  - Improve error message
```

**5:00 PM - Day 1 Wrap-up**
```yaml
With Your Manager:
  - Review what you learned
  - Plan for Day 2
  - Ask any questions
  - Share feedback
```

---

## 📆 Your First Week

### Day 2: Deep Dive

**Morning:**
```yaml
- [ ] Read assigned documentation sections
- [ ] Explore codebase independently
- [ ] Set up debugging tools
- [ ] Run full test suite
- [ ] Complete first PR (if not done)
```

**Afternoon:**
```yaml
- [ ] Pair programming session with senior dev
- [ ] Learn deployment process
- [ ] Understand CI/CD pipeline
- [ ] Start second task (small feature)
```

### Day 3: Feature Development

**Morning:**
```yaml
- [ ] Daily standup (your first one!)
- [ ] Work on assigned feature
- [ ] Ask questions in Slack
- [ ] Code review someone's PR
```

**Afternoon:**
```yaml
- [ ] Continue feature development
- [ ] Write tests for your code
- [ ] Update documentation
- [ ] Demo progress to team
```

### Day 4: Testing & Quality

**Morning:**
```yaml
- [ ] Learn testing strategy
- [ ] Write comprehensive tests
- [ ] Run tests locally
- [ ] Fix any test failures
```

**Afternoon:**
```yaml
- [ ] Code review process
- [ ] Address PR feedback
- [ ] Learn about monitoring tools
- [ ] Explore Sentry error tracking
```

### Day 5: Deployment

**Morning:**
```yaml
- [ ] Learn deployment process
- [ ] Watch a deployment (staging)
- [ ] Understand rollback procedure
- [ ] Review monitoring dashboards
```

**Afternoon:**
```yaml
- [ ] Week 1 retrospective with manager
- [ ] Plan Week 2 tasks
- [ ] Team happy hour! 🎉
```

---

## 🛠️ Development Workflow

### Daily Routine

**Morning (9 AM - 12 PM)**
```yaml
9:00 AM:
  - Check Slack messages
  - Review PR feedback
  - Check Jira/Linear for updates

9:15 AM:
  - Daily standup (15 min)
  - What did you do yesterday?
  - What will you do today?
  - Any blockers?

9:30 AM - 12:00 PM:
  - Focus time: coding, testing, reviewing
  - Respond to urgent messages only
  - Deep work on assigned tasks
```

**Afternoon (1 PM - 5 PM)**
```yaml
1:00 PM - 3:00 PM:
  - Continue development work
  - Code reviews for teammates
  - Collaborate as needed

3:00 PM - 5:00 PM:
  - Testing and bug fixes
  - Documentation updates
  - Prepare for tomorrow
  - Review day's progress
```

### Git Workflow

**Branch Naming:**
```bash
# Feature branches
feature/user-authentication
feature/swap-interface

# Bug fixes
fix/wallet-balance-display
fix/transaction-history-pagination

# Hotfixes
hotfix/critical-api-error

# Example
git checkout -b feature/add-swap-slippage-selector
```

**Commit Messages:**
```bash
# Good commit messages
feat(swap): add slippage tolerance selector

Allow users to customize slippage tolerance (0.1% - 5.0%)
when executing swaps. Default remains at 0.5%.

Closes #123

# Bad commit messages
updated files
fixed stuff
changes
```

**Pull Request Process:**
```yaml
1. Create Branch:
   git checkout -b feature/your-feature

2. Make Changes:
   - Write code
   - Write tests
   - Update docs

3. Self Review:
   - Run tests locally
   - Run linter
   - Review your own changes

4. Create PR:
   - Write clear description
   - Link to Jira/Linear ticket
   - Add screenshots (if UI changes)
   - Request reviewers

5. Address Feedback:
   - Respond to comments
   - Make requested changes
   - Re-request review

6. Merge:
   - Squash and merge (default)
   - Delete branch after merge
```

---

## 🧪 Testing Guidelines

### Before Every Commit

```bash
# Backend
pytest tests/
black .
flake8 app/

# Mobile
npm test
npm run lint

# Always run tests before pushing!
```

### Writing Tests

**Backend Example:**
```python
# tests/test_services/test_swap_service.py
def test_execute_swap_creates_transaction():
    """Test that swap creates a transaction record."""
    # Arrange
    user = create_test_user()
    
    # Act
    tx = swap_service.execute_swap(
        user_id=user.id,
        from_asset="USDC",
        to_asset="ETH",
        amount=Decimal("50")
    )
    
    # Assert
    assert tx is not None
    assert tx.status == TransactionStatus.PENDING
    assert tx.from_asset == "USDC"
```

**Mobile Example:**
```typescript
// __tests__/SwapScreen.test.tsx
describe('SwapScreen', () => {
  it('should validate minimum amount', () => {
    const { getByPlaceholderText, getByText } = render(<SwapScreen />)
    
    const input = getByPlaceholderText('0.00')
    fireEvent.changeText(input, '0.001')
    
    expect(getByText('Minimum amount is 0.01')).toBeTruthy()
  })
})
```

---

## 🤝 Team Collaboration

### Communication Channels

**Slack Channels:**
```yaml
#general:
  - Company-wide announcements
  - General discussion

#engineering:
  - Technical discussions
  - Architecture decisions
  - Code reviews

#backend:
  - Backend-specific discussions
  - API design
  - Database questions

#mobile:
  - Mobile development
  - UI/UX discussions
  - Native platform issues

#devops:
  - Infrastructure
  - Deployments
  - Monitoring alerts

#standup:
  - Daily standup summaries
  - Automated standup bot
```

### Asking for Help

**Good Question:**
```
Hey team! I'm working on implementing the swap slippage
selector (issue #123) and I'm not sure about the best way to
validate the slippage input on the backend.

Should I:
1. Validate in Pydantic schema?
2. Add custom validator in the service layer?

Context: The mobile app already validates client-side, but we
want server-side validation as well.

Relevant code: app/api/v1/routes/trading.py:45
```

**Not So Good:**
```
My code doesn't work. Help?
```

### Code Review Etiquette

**As a Reviewer:**
```yaml
Do:
  - Be kind and constructive
  - Explain the "why" behind suggestions
  - Approve quickly if changes are good
  - Ask questions to understand intent

Don't:
  - Be harsh or dismissive
  - Nitpick on style (use linters)
  - Block on personal preferences
  - Review too slowly (aim for same day)
```

**As an Author:**
```yaml
Do:
  - Respond to all comments
  - Ask for clarification if confused
  - Thank reviewers for feedback
  - Make suggested changes promptly

Don't:
  - Take feedback personally
  - Ignore comments
  - Get defensive
  - Make unrelated changes
```

---

## 📖 Learning Resources

### Internal Resources
```yaml
Documentation:
  - All docs in /outputs directory
  - API documentation: /docs endpoint
  - Team wiki (Notion/Confluence)

Code Examples:
  - Look at existing similar features
  - Check test files for usage examples
  - Review recent PRs for patterns
```

### External Resources

**Backend (Python/FastAPI):**
```yaml
- FastAPI docs: https://fastapi.tiangolo.com/
- SQLAlchemy tutorial: https://docs.sqlalchemy.org/
- Python best practices: https://realpython.com/
- Web3.py docs: https://web3py.readthedocs.io/
```

**Mobile (React Native):**
```yaml
- React Native docs: https://reactnative.dev/
- React Navigation: https://reactnavigation.org/
- TypeScript handbook: https://www.typescriptlang.org/docs/
- React hooks guide: https://react.dev/reference/react
```

**DeFi Protocols:**
```yaml
- Aave docs: https://docs.aave.com/
- 1inch docs: https://docs.1inch.io/
- Hyperliquid docs: https://hyperliquid.gitbook.io/
```

---

## 🎯 Success Metrics

### Your First Month

**Week 1:**
- [ ] Environment fully set up
- [ ] First PR merged
- [ ] Attended all team meetings
- [ ] Know all team members

**Week 2:**
- [ ] Completed 3+ PRs
- [ ] Participated in code reviews
- [ ] Understand development workflow
- [ ] Comfortable with codebase

**Week 3:**
- [ ] Working on medium-sized features
- [ ] Providing helpful code reviews
- [ ] Contributing to discussions
- [ ] Unblocked on most tasks

**Week 4:**
- [ ] Independent contributor
- [ ] Understanding product deeply
- [ ] Helping onboard next new hire
- [ ] Feeling confident and productive

---

## 🚀 Tips for Success

### Dos
```yaml
✅ Ask questions early and often
✅ Document what you learn
✅ Pair program with teammates
✅ Review others' code actively
✅ Test your changes thoroughly
✅ Update documentation
✅ Communicate proactively
✅ Take breaks and maintain work-life balance
```

### Don'ts
```yaml
❌ Stay stuck for hours without asking
❌ Skip writing tests
❌ Merge without code review
❌ Commit secrets or credentials
❌ Work in isolation
❌ Ignore team standards
❌ Deploy on Fridays (unless critical)
❌ Burn out - we're in this for the long haul
```

---

## 📞 Who to Contact

### Your Key Contacts

```yaml
Manager:
  - Daily questions
  - Task assignments
  - Career development
  - Time off requests

Tech Lead:
  - Architecture questions
  - Technical decisions
  - Code review escalations
  - Best practices

DevOps:
  - Infrastructure issues
  - Deployment problems
  - Access requests
  - Monitoring questions

Product Manager:
  - Feature questions
  - Requirements clarification
  - User stories
  - Priority questions

CTO:
  - Strategic questions
  - Major technical decisions
  - Company direction
```

---

## ✅ Onboarding Checklist

### Pre-Start
- [ ] Received welcome email
- [ ] Have laptop and equipment
- [ ] Accounts being created
- [ ] Read pre-reading materials

### Day 1
- [ ] Team introductions completed
- [ ] All accounts created
- [ ] Development environment set up
- [ ] First commit made
- [ ] Understand product

### Week 1
- [ ] Completed first feature task
- [ ] Understand git workflow
- [ ] Attended all standups
- [ ] Code reviewed 3+ PRs
- [ ] Asked lots of questions

### Month 1
- [ ] Completed 10+ PRs
- [ ] Comfortable with codebase
- [ ] Contributing independently
- [ ] Helping teammates
- [ ] Feel like part of team

---

## 🎉 Welcome to the Team!

You're now part of building something amazing. We're creating a platform that will help millions of people access DeFi safely and easily.

Remember:
- **Everyone was new once** - Don't hesitate to ask questions
- **We're a team** - We succeed together
- **Quality matters** - Take time to do it right
- **Have fun** - We're building cool stuff!

**Your first day is just the beginning. Let's build something great together! 🚀**

---

## 📝 Feedback

We're always improving our onboarding. After your first month, please share feedback:
- What went well?
- What was confusing?
- What would you change?
- What resources helped most?

Send feedback to: engineering@anvil.com

---

**Document Version:** 1.0  
**Last Updated:** November 2025  
**Maintained By:** Engineering Leadership  
**Questions:** Your manager or tech-lead@anvil.com

**Welcome aboard! 🎊**
