# Git and GitHub Setup Guide

## Initial Repository Setup

This guide explains how to push the Multi-Agent Alert Triage System to GitHub.

## Prerequisites

- Git installed on your system
- GitHub account
- SSH key configured with GitHub (or use HTTPS with personal access token)

## Step-by-Step Instructions

### 1. Create a New Repository on GitHub

1. Go to [GitHub.com](https://github.com)
2. Click the "+" icon in the top-right corner
3. Select "New repository"
4. Configure repository:
   - **Name**: `multi-agent-aml-triage` (or your preferred name)
   - **Description**: "Production-grade multi-agent system for AML/KYC alert triage"
   - **Visibility**: Choose Private or Public
   - **DO NOT** initialize with README, .gitignore, or license (we already have these)
5. Click "Create repository"

### 2. Initialize Local Git Repository

The repository is already initialized. To verify:

```bash
cd /Users/ekuekpodar/Desktop/Multi-Agent
git status
```

### 3. Add Remote Repository

Replace `YOUR_USERNAME` with your GitHub username:

```bash
# Using SSH (recommended)
git remote add origin git@github.com:YOUR_USERNAME/multi-agent-aml-triage.git

# OR using HTTPS
git remote add origin https://github.com/YOUR_USERNAME/multi-agent-aml-triage.git
```

### 4. Stage and Commit All Files

```bash
# Check current status
git status

# Add all files
git add .

# Commit with descriptive message
git commit -m "Initial commit: Multi-agent AML alert triage system

- Implemented 5 specialized AI agents (Supervisor, Data Enrichment, Risk Scoring, Context Builder, Decision Maker)
- Complete audit trail system for regulatory compliance
- Comprehensive data models with Pydantic v2
- Production-ready infrastructure with error handling and retry logic
- Full test suite (unit + integration tests)
- Comprehensive documentation (Getting Started, Architecture, API Reference, Deployment)
- Example scripts for basic and batch processing
- Docker and Kubernetes deployment configurations
- 3,453 lines of production code"
```

### 5. Push to GitHub

```bash
# Push to main branch
git push -u origin main

# If your default branch is 'master' instead of 'main'
git push -u origin master
```

### 6. Verify Upload

1. Go to your GitHub repository URL
2. Verify all files are present
3. Check that the README.md displays correctly

## Common Git Commands

### Check Status
```bash
git status
```

### View Commit History
```bash
git log --oneline
```

### Create a New Branch
```bash
git checkout -b feature/new-feature
```

### Switch Between Branches
```bash
git checkout main
git checkout feature/new-feature
```

### Update Remote Repository
```bash
git add .
git commit -m "Description of changes"
git push
```

### Pull Latest Changes
```bash
git pull origin main
```

## Recommended .gitignore

Already created at `.gitignore` with common Python exclusions:
- `__pycache__/`
- `*.pyc`
- `.env` (keeps secrets safe)
- Virtual environments
- IDE files
- Database files
- Logs

## Branch Protection (Recommended for Production)

For production repositories, consider setting up branch protection:

1. Go to repository Settings > Branches
2. Add rule for `main` branch
3. Enable:
   - Require pull request reviews before merging
   - Require status checks to pass (if CI/CD is set up)
   - Require conversation resolution before merging

## Setting Up GitHub Actions (Optional)

Create `.github/workflows/ci.yml` for automated testing:

```yaml
name: CI

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v3

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.10'

    - name: Install Poetry
      run: |
        curl -sSL https://install.python-poetry.org | python3 -

    - name: Install dependencies
      run: poetry install

    - name: Run tests
      run: poetry run pytest

    - name: Run linting
      run: poetry run ruff check src/

    - name: Run type checking
      run: poetry run mypy src/
```

## Troubleshooting

### Issue: "remote origin already exists"

```bash
# Remove existing remote
git remote remove origin

# Add new remote
git remote add origin git@github.com:YOUR_USERNAME/repo-name.git
```

### Issue: "Permission denied (publickey)"

You need to set up SSH keys:

```bash
# Generate SSH key
ssh-keygen -t ed25519 -C "your_email@example.com"

# Copy public key
cat ~/.ssh/id_ed25519.pub

# Add to GitHub: Settings > SSH and GPG keys > New SSH key
```

### Issue: "Updates were rejected because the remote contains work"

```bash
# Pull and merge first
git pull origin main --rebase

# Then push
git push origin main
```

## Next Steps After Pushing

1. **Add Topics**: On GitHub, add relevant topics (e.g., `aml`, `kyc`, `compliance`, `ai-agents`, `claude`)
2. **Create Releases**: Tag versions for production deployments
3. **Set Up Issues**: Track bugs and feature requests
4. **Add CODEOWNERS**: Define code ownership for reviews
5. **Configure Dependabot**: Automated dependency updates
6. **Add Status Badges**: Display build status in README

## Security Considerations

### Never Commit Secrets

Ensure these are in `.gitignore`:
- `.env` files with API keys
- `*.pem` or `*.key` files
- Database credentials
- Any file with sensitive data

### If You Accidentally Commit Secrets

```bash
# Remove file from git history
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch path/to/secret/file" \
  --prune-empty --tag-name-filter cat -- --all

# Force push (DANGEROUS - coordinate with team)
git push origin --force --all
```

Then immediately:
1. Rotate the exposed credentials
2. Update secrets in secure storage
3. Review access logs for unauthorized use

## Collaboration Workflow

### For Team Development

1. **Clone Repository**
   ```bash
   git clone git@github.com:USERNAME/multi-agent-aml-triage.git
   cd multi-agent-aml-triage
   ```

2. **Create Feature Branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Make Changes and Commit**
   ```bash
   git add .
   git commit -m "Add feature: description"
   ```

4. **Push and Create Pull Request**
   ```bash
   git push origin feature/your-feature-name
   # Then create PR on GitHub
   ```

5. **Code Review and Merge**
   - Request reviews from team members
   - Address feedback
   - Merge to main after approval

## Continuous Integration

Consider setting up:
- **GitHub Actions**: Automated testing on every push
- **Pre-commit Hooks**: Run linting before commits
- **Codecov**: Track test coverage
- **Dependabot**: Security updates

## Version Control Best Practices

1. **Commit Messages**: Use conventional commits format
   - `feat:` for new features
   - `fix:` for bug fixes
   - `docs:` for documentation
   - `test:` for tests
   - `refactor:` for code refactoring

2. **Branch Naming**: Use descriptive names
   - `feature/add-monitoring-dashboard`
   - `fix/risk-scoring-calculation`
   - `docs/update-api-reference`

3. **Pull Requests**: Include
   - Clear description of changes
   - Link to related issues
   - Test results
   - Screenshots (if UI changes)

## License

If making the repository public, add an appropriate LICENSE file.
For proprietary code, add:

```
Copyright (c) 2026 Castellum.AI
All rights reserved.
```
