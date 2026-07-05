# JHD Hotel — Vercel Deployment Checklist

## WHY YOU GOT A 500

The most common causes (in order):

1. ❌ Missing environment variables in Vercel dashboard
2. ❌ No PostgreSQL database connected (SQLite doesn't work on Vercel)
3. ❌ Old vercel.json with @vercel/static conflict (now fixed)
4. ❌ psycopg2-binary build failure (now fixed with 2.9.10)

---

## STEP-BY-STEP FIX

### Step 1 — Get a Free PostgreSQL Database (5 minutes)

Go to **neon.tech** → Sign up free → New Project → name it "jhd-hotel"

You'll see a connection string like:
```
postgresql://user:pass@ep-xxx.us-east-2.aws.neon.tech/neondb?sslmode=require
```

Copy this — you'll need it in Step 3.

---

### Step 2 — Push updated code to GitHub

```bash
git add .
git commit -m "Fix Vercel deployment"
git push
```

Vercel will auto-redeploy when you push.

---

### Step 3 — Set Environment Variables in Vercel

Go to: vercel.com → Your Project → **Settings** → **Environment Variables**

Add ALL of these (without quotes):

| Variable | Value |
|---|---|
| `FLASK_ENV` | `production` |
| `SECRET_KEY` | any long random string e.g. `jhd2025xYz9mQ7kL3nP` |
| `DATABASE_URL` | your Neon connection string from Step 1 |
| `NORMAL_PRICE` | `4000` |
| `PEAK_PRICE` | `7000` |
| `SUPER_DELUXE_EXTRA` | `1500` |
| `PEAK_SEASON_RANGES` | `10-01:12-31,01-01:03-31` |
| `ADMIN_USERNAME` | `admin` |
| `ADMIN_PASSWORD` | your chosen password |
| `PAYPAL_CLIENT_ID` | from developer.paypal.com |
| `PAYPAL_CLIENT_SECRET` | from developer.paypal.com |
| `PAYPAL_MODE` | `live` |
| `RAZORPAY_KEY_ID` | from razorpay.com |
| `RAZORPAY_KEY_SECRET` | from razorpay.com |
| `MAIL_USERNAME` | `Hoteljhd@gmail.com` |
| `MAIL_PASSWORD` | your Gmail App Password |

---

### Step 4 — Trigger a redeploy

In Vercel dashboard → Deployments → click the 3 dots on the latest → **Redeploy**

---

### Step 5 — Seed the database (one time only)

Run this on your local machine, with `DATABASE_URL` in your `.env` pointing to Neon:

```bash
# In your .env file, temporarily set:
DATABASE_URL=postgresql://user:pass@your-neon-host/neondb?sslmode=require

# Then run:
python seed_data.py
```

This creates the 33 rooms in your live Postgres database.

---

### Step 6 — Test your live site

Visit these URLs:

- `https://your-site.vercel.app/health` → should return `{"status":"ok","db":true}`
- `https://your-site.vercel.app/` → homepage
- `https://your-site.vercel.app/admin/login` → admin panel

If `/health` shows `"db": false`, your DATABASE_URL is wrong or Neon isn't set up yet.

---

## CHECKING LOGS

Go to: vercel.com → Your Project → **Deployments** → click latest → **Functions** tab

You'll see the actual Python error that caused the 500.

Common errors and fixes:

| Error in logs | Fix |
|---|---|
| `sqlalchemy.exc.OperationalError` | DATABASE_URL wrong or not set |
| `KeyError: 'SECRET_KEY'` | SECRET_KEY not set in env vars |
| `ModuleNotFoundError` | pip install failed — check Build logs |
| `CSRF token missing` | SECRET_KEY not set (WTF needs it) |

---

## ALTERNATIVE: USE RENDER INSTEAD

If Vercel keeps causing issues, Render.com is easier for Flask:

1. render.com → New Web Service → connect GitHub
2. Add Postgres add-on (free, auto-sets DATABASE_URL)
3. Add env vars in Settings
4. Uses `render.yaml` which is already in your project

Render is designed for long-running servers (like Flask), while Vercel is designed for serverless (like Next.js). Either works, but Render is simpler for Flask.

