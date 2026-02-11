# 🚀 PrepIQ Production Launch Checklist

Use this checklist to ensure a successful production deployment.

## Phase 1: Pre-Deployment Preparation

### Repository Setup
- [ ] All code committed to GitHub
- [ ] `.env.production.example` files created
- [ ] No secrets in repository (verify with `git log --all --full-history -- .env`)
- [ ] `.gitignore` properly configured (node_modules, __pycache__, .env, etc.)
- [ ] README.md updated with production instructions

### Code Quality
- [ ] All TypeScript errors resolved (or `ignoreBuildErrors: false` in next.config.js)
- [ ] Backend starts successfully locally: `cd backend && python -m app.main`
- [ ] Frontend builds successfully locally: `cd frontend && npm run build`
- [ ] No `console.log` statements in production code (frontend)
- [ ] No `print()` statements in production code (backend)

### Required Files Present
- [ ] `backend/.env.production.example`
- [ ] `frontend/.env.production.example`
- [ ] `Procfile` (in root)
- [ ] `render.yaml` (in root)
- [ ] `supabase-migration.sql` (in root)
- [ ] `deploy.md` (in root)
- [ ] `.dockerignore` (in root)
- [ ] `frontend/vercel.json`
- [ ] `frontend/next.config.js` (not .mjs)

---

## Phase 2: Supabase Setup

### Project Creation
- [ ] Supabase account created
- [ ] New project created with strong database password
- [ ] Project region selected (closest to users)
- [ ] Project is active (not paused)

### Connection Strings
- [ ] Copied Connection Pooler URL (port 6543)
- [ ] Copied Direct Connection URL (port 5432, for migrations)
- [ ] Saved Project URL
- [ ] Saved `anon` public key
- [ ] Saved `service_role` secret key

### Database Migration
- [ ] SQL Editor opened
- [ ] `supabase-migration.sql` pasted completely
- [ ] Migration executed successfully
- [ ] All tables created (verify in Database → Tables)
- [ ] All indexes created
- [ ] All RLS policies applied (verify in each table)

### Auth Configuration
- [ ] Email provider enabled
- [ ] Email confirmation configured (recommended: ON)
- [ ] (Optional) Google OAuth configured
- [ ] (Optional) Other providers configured

---

## Phase 3: Google AI Setup

### Gemini API
- [ ] Google AI Studio account created
- [ ] API key generated
- [ ] API key saved securely
- [ ] Billing enabled (if required, has free tier)

---

## Phase 4: Backend Deployment (Render)

### Account & Repository
- [ ] Render account created
- [ ] GitHub account connected to Render
- [ ] Repository connected

### Service Configuration
- [ ] New Web Service created
- [ ] Service name set (e.g., `prepiq-backend`)
- [ ] Python 3 environment selected
- [ ] Build command: `cd backend && pip install -r requirements.txt`
- [ ] Start command: `cd backend && uvicorn app.main:app --host 0.0.0.0 --port $PORT --workers 1`
- [ ] Free plan selected

### Environment Variables Set
- [ ] `DATABASE_URL` (Supabase connection pooler)
- [ ] `SUPABASE_URL`
- [ ] `SUPABASE_SERVICE_KEY`
- [ ] `JWT_SECRET` (generated with `openssl rand -base64 32`)
- [ ] `JWT_ALGORITHM` = `HS256`
- [ ] `ACCESS_TOKEN_EXPIRE_MINUTES` = `1440`
- [ ] `ALLOWED_ORIGINS` (temporary: will update after Vercel deploy)
- [ ] `GEMINI_API_KEY`
- [ ] `ENVIRONMENT` = `production`
- [ ] `DEBUG` = `false`
- [ ] `LOG_LEVEL` = `INFO`

### Deployment Verification
- [ ] First deployment successful
- [ ] Health endpoint responding: `GET /health`
- [ ] Logs show "✅ Database connection verified"
- [ ] No startup errors in logs
- [ ] Service status: Live

---

## Phase 5: Frontend Deployment (Vercel)

### Account & Repository
- [ ] Vercel account created
- [ ] GitHub account connected to Vercel
- [ ] Repository imported

### Project Configuration
- [ ] Project name set (e.g., `prepiq-frontend`)
- [ ] Framework preset: Next.js
- [ ] Root directory: `frontend`
- [ ] Build command: `next build` (or default)
- [ ] Output directory: `.next` (or default)

### Environment Variables Set
- [ ] `NEXT_PUBLIC_API_URL` = Render backend URL
- [ ] `NEXT_PUBLIC_SUPABASE_URL`
- [ ] `NEXT_PUBLIC_SUPABASE_ANON_KEY`
- [ ] `NEXT_PUBLIC_APP_NAME` = `PrepIQ`
- [ ] `NEXT_PUBLIC_APP_DESCRIPTION`

### Deployment Verification
- [ ] First deployment successful
- [ ] Homepage loads without errors
- [ ] Browser console shows no errors
- [ ] Network tab shows successful API calls (if CORS configured)

---

## Phase 6: CORS & Integration

### Update CORS Origins
- [ ] Copied Vercel deployment URL
- [ ] Updated `ALLOWED_ORIGINS` in Render
  - Format: `https://your-app.vercel.app`
  - No trailing slash
  - No spaces
- [ ] Restarted Render service
- [ ] Verified CORS works (check browser console)

### Custom Domain (Optional)
- [ ] Domain registered
- [ ] Domain added to Vercel
- [ ] DNS configured (A/CNAME records)
- [ ] SSL certificate issued
- [ ] Domain added to `ALLOWED_ORIGINS`

---

## Phase 7: End-to-End Testing

### Authentication Flow
- [ ] User can register
- [ ] User receives confirmation email (if enabled)
- [ ] User can confirm email
- [ ] User can login
- [ ] User can logout
- [ ] JWT token works correctly
- [ ] Token expiration works

### Core Features
- [ ] Create subject works
- [ ] Subject list displays correctly
- [ ] Upload PDF works (< 5MB test file)
- [ ] PDF processing completes
- [ ] View papers works
- [ ] Generate predictions works
- [ ] View predictions works
- [ ] Chat with AI works
- [ ] Take mock test works
- [ ] View test results works

### Edge Cases
- [ ] Large file upload handled (> 10MB should fail gracefully)
- [ ] Invalid file type rejected
- [ ] Unauthorized access blocked
- [ ] Session expiration handled
- [ ] Network errors handled

### Mobile Testing
- [ ] Test on mobile browser
- [ ] Test responsive design
- [ ] Test touch interactions
- [ ] Test file upload on mobile

---

## Phase 8: Security Verification

### Security Headers
- [ ] `X-Content-Type-Options: nosniff`
- [ ] `X-Frame-Options: DENY`
- [ ] `X-XSS-Protection: 1; mode=block`
- [ ] `Strict-Transport-Security` present
- [ ] `Referrer-Policy` set

### Data Protection
- [ ] No passwords in logs
- [ ] No JWT tokens in logs
- [ ] No sensitive data in error messages
- [ ] HTTPS enforced (no HTTP access)

### Authentication Security
- [ ] Passwords hashed (bcrypt)
- [ ] JWT tokens have expiration
- [ ] Refresh tokens implemented (if applicable)
- [ ] RLS policies active

---

## Phase 9: Performance & Monitoring

### Performance Checks
- [ ] Page load time < 3 seconds
- [ ] API response time < 1 second (health check)
- [ ] File upload time reasonable (< 30 seconds for 5MB)
- [ ] No memory leaks (monitor over time)

### Monitoring Setup
- [ ] UptimeRobot account created
- [ ] Monitor added for backend health endpoint
- [ ] Ping interval: 10 minutes
- [ ] (Optional) Sentry configured for error tracking
- [ ] (Optional) Google Analytics configured

### Logging
- [ ] Backend logs viewable in Render dashboard
- [ ] Frontend errors visible in browser console
- [ ] Log rotation configured (if needed)

---

## Phase 10: Documentation & Handoff

### Documentation
- [ ] `deploy.md` reviewed and accurate
- [ ] Environment variable list complete
- [ ] Troubleshooting section covers common issues
- [ ] Support contacts documented

### Team Handoff (if applicable)
- [ ] Credentials shared securely (password manager)
- [ ] Access granted to team members
- [ ] Documentation walkthrough completed
- [ ] Runbook created for common operations

---

## Phase 11: Launch Day

### Pre-Launch (T-30 minutes)
- [ ] Final health check on all services
- [ ] Database backup created
- [ ] Error monitoring active
- [ ] Support channels ready

### Launch (T-0)
- [ ] Announce to users (if applicable)
- [ ] Monitor error rates
- [ ] Monitor performance
- [ ] Monitor user feedback

### Post-Launch (T+1 hour)
- [ ] Review error logs
- [ ] Check user registrations
- [ ] Verify all features working
- [ ] Document any issues

### Post-Launch (T+24 hours)
- [ ] Daily usage review
- [ ] Performance review
- [ ] User feedback review
- [ ] Plan improvements

---

## Quick Reference

### Important URLs
- **Frontend:** `https://your-app.vercel.app`
- **Backend:** `https://your-api.onrender.com`
- **Health Check:** `https://your-api.onrender.com/health`
- **Supabase:** `https://app.supabase.com/project/[project-id]`
- **Render Dashboard:** `https://dashboard.render.com`
- **Vercel Dashboard:** `https://vercel.com/dashboard`

### Emergency Contacts
- Render Status: https://status.render.com
- Vercel Status: https://www.vercel-status.com
- Supabase Status: https://status.supabase.com

### Useful Commands
```bash
# Test backend health
curl https://your-api.onrender.com/health

# Test CORS
curl -H "Origin: https://your-app.vercel.app" \
     -I https://your-api.onrender.com/health

# Check security headers
curl -I https://your-app.vercel.app

# Database connection test (local)
psql $DATABASE_URL -c "SELECT 1"
```

---

## Post-Launch Maintenance Schedule

### Daily
- [ ] Check error logs
- [ ] Monitor uptime (UptimeRobot)
- [ ] Check user registrations

### Weekly
- [ ] Review performance metrics
- [ ] Check resource usage (bandwidth, storage)
- [ ] Update dependencies (security patches)

### Monthly
- [ ] Database backup verification
- [ ] Security review
- [ ] Cost review (ensure staying in free tier)
- [ ] Feature usage analysis

### Quarterly
- [ ] Full security audit
- [ ] Performance optimization review
- [ ] User feedback analysis
- [ ] Roadmap planning

---

## Sign-Off

**Deployed By:** _________________  
**Date:** _________________  
**Version:** _________________

### Verification Signatures

| Role | Name | Signature | Date |
|------|------|-----------|------|
| Developer | | | |
| QA Tester | | | |
| DevOps | | | |
| Product Owner | | | |

---

## Notes

_Add any additional notes, issues encountered, or special configurations here:_





---

🎉 **Congratulations! PrepIQ is now production-ready!**

Remember:
- Monitor your usage to stay within free tier limits
- Keep backups of your database
- Update dependencies regularly
- Listen to user feedback
- Keep improving!

**Questions?** Refer to `deploy.md` for detailed instructions.
