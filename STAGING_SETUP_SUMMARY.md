# Backend Staging Environment - Executive Summary

## What You Have Now
- ✅ Frontend staging: `sync2cal-staging.vercel.app` (Vercel)
- ✅ Frontend production: `sync2cal.com` (Vercel)
- ✅ Backend production: Railway deployment
- ❌ Backend staging: **Missing**

## What You Need
Staging environments for both backend services:
1. **Main Backend** (`sync2cal-ics-version`) - Authentication, categories, payments
2. **Events API** (`S2C-events-api`) - Calendar event integrations

## Quick Start (TL;DR)

### 1. Create Railway Staging Projects
- Create `sync2cal-backend-staging` project in Railway
- Create `sync2cal-events-api-staging` project in Railway
- Connect to GitHub repos, deploy from `staging` branch

### 2. Configure Environment Variables

**Main Backend Staging:**
```bash
DB=<staging-postgresql-connection>
STRIPE_SECRET_KEY=sk_test_...  # Use test key
RESEND_KEY=re_...
JWT_SECRET=<new-secret-different-from-prod>
CORS_ORIGINS=https://sync2cal-staging.vercel.app,http://localhost:3000
```

**Events API Staging:**
```bash
CORS_ORIGINS=https://sync2cal-staging.vercel.app,https://sync2cal.com,http://localhost:3000
# ... API keys (can reuse production)
```

### 3. Update Frontend Vercel Config
In Vercel → Environment Variables → **Preview**:
```bash
BACKEND_URL=https://sync2cal-backend-staging.up.railway.app
```

### 4. Code Changes Needed
- Update `sync2cal-ics-version/main.py` CORS to read from `CORS_ORIGINS` env var
- (Events API already supports `CORS_ORIGINS`)

## Detailed Plans
- **Full Plan**: See `BACKEND_STAGING_SETUP_PLAN.md`
- **Checklist**: See `sync2cal-ics-version/STAGING_SETUP_CHECKLIST.md`

## Estimated Time
4-6 hours total

## Key Decisions Needed
1. **Database**: Fresh staging DB or production snapshot?
2. **Branch Strategy**: Use `staging` branch or deploy from `main`?
3. **Stripe**: Use test keys for staging?
4. **Cost**: Railway charges per service - okay with additional costs?

## Next Steps
1. Review the detailed plan
2. Make key decisions (database, branch strategy)
3. Create staging branches (if using branch strategy)
4. Set up Railway projects
5. Configure environment variables
6. Update CORS code
7. Test end-to-end






