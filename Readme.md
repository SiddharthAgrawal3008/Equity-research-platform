# Equity Research Platform (Ongoing)

Automated equity research and valuation intelligence system.

## Team & Engine Ownership

| Member | Engine(s) | Branch |
|--------|-----------|--------|
| **Divyansh** | Engine 1 (Financial Data) + Frontend | `dev/divyansh` |
| **Siddharth** | Engine 2 (Valuation) + Engine 3 (Risk) | `dev/siddharth` |
| **Annant** | Engine 4 (NLP Intelligence) | `dev/annant` |
| **Naman** | Engine 5 (Investment Memo) | `dev/naman` |

## Branch Strategy

- `main` — **protected**, only receives tested merges
- `dev/<name>` — each member works exclusively on their branch
- Never push directly to `main`. Merge via pull request after review.

## Quick Start (Codespaces)
1. Click the green "Code" button above
2. Select "Codespaces" tab
3. Click "Create codespace on main"
4. Wait 2 minutes for setup
5. Everything is installed automatically

## Run Backend
```bash
cd backend
uvicorn main:app --reload --port 8000
```

## Run Frontend
```bash
cd frontend
npm run dev
```
