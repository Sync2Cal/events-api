# Backend Staging Environment Setup Plan

## Overview

This document outlines the plan to set up staging environments for both backend services:
1. **Main Backend** (`sync2cal-ics-version`) - Handles authentication, categories, events, payments
2. **Events API** (`S2C-events-api`) - Provides calendar event integrations (Twitch, IMDb, etc.)

Currently, the frontend has staging configured on Vercel (`sync2cal-staging.vercel.app`), but the backends only have production deployments on Railway.

## Current Architecture

### Frontend
- **Production**: `sync2cal.com` (Vercel)
- **Staging**: `sync2cal-staging.vercel.app` (Vercel)
- **Backend URL**: Configured via `BACKEND_URL` environment variable
  - Production: `https://api.sync2cal.com` (or similar)
  - Staging: Should point to staging backend (to be created)

### Main Backend (`sync2cal-ics-version`)
- **Production**: Railway deployment
- **Database**: PostgreSQL (production)
- **Environment Variables**:
  - `DB` - PostgreSQL connection string
  - `STRIPE_SECRET_KEY` - Stripe production key
  - `RESEND_KEY` - Resend API key
  - `JWT_SECRET` - JWT signing secret
  - `PORT` - Set by Railway
- **CORS**: Currently allows all origins (`["*"]`)

### Events API (`S2C-events-api`)
- **Production**: Railway deployment (`sync2cal-scraper.up.railway.app`)
- **Environment Variables**:
  - `CORS_ORIGINS` - Comma-separated list of allowed origins
  - Various API keys (Twitch, Google Sheets, TheTVDB, etc.)
- **CORS**: Configurable via `CORS_ORIGINS` env var

## Staging Setup Strategy

### Option 1: Separate Railway Projects (Recommended)
Create separate Railway projects for staging, completely isolated from production.

**Pros:**
- Complete isolation from production
- Can use separate databases
- Easy to test without affecting production
- Can use test Stripe keys

**Cons:**
- Additional Railway costs (if applicable)
- Need to manage two sets of deployments

### Option 2: Railway Environments/Branches
Use Railway's branch-based deployments or environment variables to switch between staging and production.

**Pros:**
- Single project management
- Potentially lower cost

**Cons:**
- Risk of accidentally deploying to wrong environment
- Shared resources (database, etc.)

**Recommendation: Use Option 1 (Separate Projects)**

## Implementation Plan

### Phase 1: Main Backend Staging Setup (`sync2cal-ics-version`)

#### Step 1.1: Create Railway Staging Project
1. Go to Railway dashboard
2. Create new project: `sync2cal-backend-staging`
3. Connect to GitHub repository: `sync2cal-ics-version`
4. Configure deployment:
   - **Branch**: `staging` (or create a `staging` branch)
   - **Root Directory**: `/`
   - **Build Command**: (Railway auto-detects Python)
   - **Start Command**: Uses `Procfile` (`web: bash start.sh`)

#### Step 1.2: Set Up Staging Database
1. In Railway staging project, add PostgreSQL service
2. Note the connection string (will be in `DATABASE_URL` or `POSTGRES_URL`)
3. Run migrations on staging database:
   ```bash
   # Connect to staging database and run migrations
   python migrate_add_custom_metadata.py
   ```

#### Step 1.3: Configure Staging Environment Variables
Set these in Railway staging project:

```bash
# Database
DB=<staging-postgresql-connection-string>

# Stripe (use test keys for staging)
STRIPE_SECRET_KEY=sk_test_...  # Stripe test secret key

# Email (can use same Resend key or separate)
RESEND_KEY=re_...  # Resend API key

# JWT Secret (use different secret from production)
JWT_SECRET=<generate-new-secret-for-staging>
# Generate with: openssl rand -base64 32

# Port (auto-set by Railway, but can override)
PORT=8000
```

#### Step 1.4: Update CORS Configuration
Modify `main.py` to support environment-specific CORS origins:

```python
# In sync2cal-ics-version/main.py
import os

# Get CORS origins from environment variable
cors_origins_env = os.getenv("CORS_ORIGINS", "")
if cors_origins_env:
    allowed_origins = [origin.strip() for origin in cors_origins_env.split(",") if origin.strip()]
else:
    # Default to production origins if not set
    allowed_origins = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://sync2cal.com",
        "https://www.sync2cal.com",
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

Add to Railway staging environment variables:
```bash
CORS_ORIGINS=https://sync2cal-staging.vercel.app,http://localhost:3000,http://127.0.0.1:3000
```

#### Step 1.5: Get Staging Backend URL
1. After deployment, Railway will provide a URL like: `sync2cal-backend-staging.up.railway.app`
2. Note this URL for frontend configuration

### Phase 2: Events API Staging Setup (`S2C-events-api`)

#### Step 2.1: Create Railway Staging Project
1. Create new Railway project: `sync2cal-events-api-staging`
2. Connect to GitHub repository: `S2C-events-api`
3. Configure deployment:
   - **Branch**: `staging` (or create a `staging` branch)
   - **Root Directory**: `/`
   - **Build Command**: (Railway auto-detects Python)
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}`

#### Step 2.2: Configure Staging Environment Variables
Set these in Railway staging project:

```bash
# CORS Origins (include staging frontend)
CORS_ORIGINS=https://sync2cal-staging.vercel.app,https://sync2cal.com,https://www.sync2cal.com,http://localhost:3000

# API Keys (can reuse production keys or use test keys)
TWITCH_CLIENT_ID=...
TWITCH_CLIENT_SECRET=...
GOOGLE_SHEETS_SERVICE_ACCOUNT_FILE=service_account.json
THE_TVDB_API_KEY=...
THE_TVDB_BEARER_TOKEN=...
SPORTSDB_API_KEY=...
OPENWEATHERMAP_API_KEY=...

# Port (auto-set by Railway)
PORT=8000
```

#### Step 2.3: Get Staging Events API URL
1. After deployment, Railway will provide a URL like: `sync2cal-events-api-staging.up.railway.app`
2. Note this URL (may not be needed immediately if frontend doesn't use it directly)

### Phase 3: Frontend Configuration Updates

#### Step 3.1: Update Vercel Staging Environment Variables
In Vercel dashboard → Project Settings → Environment Variables:

1. Add/Update `BACKEND_URL` for **Preview** environment:
   ```bash
   BACKEND_URL=https://sync2cal-backend-staging.up.railway.app
   ```

2. Verify other staging-specific variables are set:
   ```bash
   AUTH_URL=https://sync2cal-staging.vercel.app
   CANON=https://sync2cal-staging.vercel.app
   AUTH_APPLE_ID=com.sync2cal.signin.staging
   ```

#### Step 3.2: Update Events API Base URL (if needed)
If the frontend uses `NEXT_PUBLIC_EVENTS_API_BASE`, update it for staging:
```bash
NEXT_PUBLIC_EVENTS_API_BASE=https://sync2cal-events-api-staging.up.railway.app
```

### Phase 4: Testing & Verification

#### Step 4.1: Test Staging Backend Connectivity
```bash
# Test staging backend health
curl https://sync2cal-backend-staging.up.railway.app/

# Test authentication endpoint
curl -X POST https://sync2cal-backend-staging.up.railway.app/authentication/ \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com"}'
```

#### Step 4.2: Test Staging Frontend → Backend Integration
1. Deploy frontend to staging (or use preview deployment)
2. Visit `https://sync2cal-staging.vercel.app`
3. Test authentication flow
4. Verify API calls are going to staging backend (check browser network tab)
5. Test category sync functionality
6. Test payment flow (using Stripe test mode)

#### Step 4.3: Test Events API Staging
```bash
# Test events API health
curl https://sync2cal-events-api-staging.up.railway.app/

# Test an integration endpoint
curl "https://sync2cal-events-api-staging.up.railway.app/imdb/events?ics=false"
```

### Phase 5: Documentation & Maintenance

#### Step 5.1: Update Documentation
- Update `README.md` files with staging setup instructions
- Document environment variable differences
- Add staging URLs to relevant docs

#### Step 5.2: Set Up Monitoring
- Add staging URLs to monitoring/alerting (if applicable)
- Set up separate error tracking for staging (Sentry, Rollbar, etc.)

#### Step 5.3: Database Management
- Decide on staging database strategy:
  - **Option A**: Fresh database (clean slate for testing)
  - **Option B**: Periodic production snapshot (more realistic testing)
  - **Option C**: Shared read-only production DB (not recommended for staging)

## Environment Variable Summary

### Main Backend Staging (`sync2cal-ics-version`)
```bash
DB=<staging-postgresql-connection-string>
STRIPE_SECRET_KEY=sk_test_...  # Test key
RESEND_KEY=re_...  # Can use same or separate
JWT_SECRET=<staging-specific-secret>
CORS_ORIGINS=https://sync2cal-staging.vercel.app,http://localhost:3000
PORT=8000  # Auto-set by Railway
```

### Events API Staging (`S2C-events-api`)
```bash
CORS_ORIGINS=https://sync2cal-staging.vercel.app,https://sync2cal.com,http://localhost:3000
TWITCH_CLIENT_ID=...
TWITCH_CLIENT_SECRET=...
# ... other API keys (can reuse production)
PORT=8000  # Auto-set by Railway
```

### Frontend Staging (Vercel Preview Environment)
```bash
BACKEND_URL=https://sync2cal-backend-staging.up.railway.app
NEXT_PUBLIC_EVENTS_API_BASE=https://sync2cal-events-api-staging.up.railway.app  # If used
AUTH_URL=https://sync2cal-staging.vercel.app
CANON=https://sync2cal-staging.vercel.app
AUTH_APPLE_ID=com.sync2cal.signin.staging
# ... other existing staging variables
```

## Deployment Workflow

### For Main Backend
1. Create `staging` branch (or use existing branch)
2. Push changes to `staging` branch
3. Railway automatically deploys staging project
4. Test on staging URL
5. Merge `staging` → `main` when ready
6. Railway automatically deploys production project

### For Events API
1. Create `staging` branch (or use existing branch)
2. Push changes to `staging` branch
3. Railway automatically deploys staging project
4. Test on staging URL
5. Merge `staging` → `main` when ready
6. Railway automatically deploys production project

## Cost Considerations

- Railway charges per service/resource
- Staging will require:
  - 2 additional services (one per backend)
  - 1 additional PostgreSQL database (for main backend)
  - Bandwidth and compute usage
- Consider using Railway's free tier limits or pausing staging when not in use

## Security Considerations

1. **JWT Secrets**: Use different secrets for staging and production
2. **Stripe Keys**: Use test keys for staging to avoid real charges
3. **Database**: Keep staging database separate and isolated
4. **CORS**: Restrict CORS to only staging frontend URL
5. **Environment Variables**: Never commit secrets to git
6. **Access Control**: Limit who can access staging deployments

## Rollback Plan

If staging setup causes issues:

1. **Temporary**: Disable staging deployments in Railway
2. **Frontend**: Revert `BACKEND_URL` to production in Vercel
3. **Permanent**: Delete staging Railway projects if needed

## Next Steps

1. ✅ Review this plan
2. ⬜ Create staging branches in both backend repos
3. ⬜ Set up Railway staging projects
4. ⬜ Configure environment variables
5. ⬜ Update CORS configuration in main backend
6. ⬜ Deploy and test staging backends
7. ⬜ Update frontend Vercel configuration
8. ⬜ Test end-to-end staging flow
9. ⬜ Document staging URLs and access
10. ⬜ Set up monitoring/alerting for staging

## Questions to Consider

1. **Database Strategy**: Do you want a fresh staging database or periodic production snapshots?
2. **Branch Strategy**: Use a `staging` branch or deploy from `main` with different configs?
3. **Stripe Testing**: Will you use Stripe test mode keys for staging?
4. **Data Seeding**: Do you need test data in staging database?
5. **Monitoring**: Should staging errors be tracked separately or together with production?

## Estimated Time

- **Phase 1** (Main Backend): 1-2 hours
- **Phase 2** (Events API): 30 minutes - 1 hour
- **Phase 3** (Frontend Config): 15-30 minutes
- **Phase 4** (Testing): 1-2 hours
- **Phase 5** (Documentation): 30 minutes

**Total**: ~4-6 hours






