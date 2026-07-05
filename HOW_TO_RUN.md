# JHD Hotel & Bar — Run & Deploy Guide

## 🖥️ RUN LOCALLY (Testing)

```bash
pip install -r requirements.txt
# copy .env.example → .env and fill in your values
python seed_data.py
python app.py
```
Visit → http://localhost:5000

---

## 🚀 DEPLOY ON VERCEL

### ⚠️ IMPORTANT: Vercel needs a real database

Vercel's servers have **no persistent file storage** — every request may run
on a fresh container, so SQLite (a local file) will NOT work. You need a
free hosted Postgres database first:

1. Go to **neon.tech** → Sign up free → Create a project
2. Copy the connection string shown (starts with `postgresql://...`)
3. You'll paste this into Vercel as `DATABASE_URL` (see step 4 below)

### Step 1 — Push your code to GitHub
```bash
git init
git add .
git commit -m "JHD Hotel website"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/jhd-hotel.git
git push -u origin main
```

### Step 2 — Import into Vercel
1. Go to **vercel.com** → Sign up / Log in
2. Click **Add New** → **Project**
3. Import your GitHub repo
4. Vercel will detect `vercel.json` automatically

### Step 3 — Add Environment Variables
In Vercel dashboard → your project → **Settings** → **Environment Variables**, add:

| Key | Value |
|---|---|
| `FLASK_ENV` | `production` |
| `SECRET_KEY` | any long random string |
| `DATABASE_URL` | your Neon/Supabase Postgres connection string |
| `PAYPAL_CLIENT_ID` | from developer.paypal.com |
| `PAYPAL_CLIENT_SECRET` | from developer.paypal.com |
| `PAYPAL_MODE` | `live` (once ready for real payments) |
| `RAZORPAY_KEY_ID` | from razorpay.com |
| `RAZORPAY_KEY_SECRET` | from razorpay.com |
| `MAIL_USERNAME` | your Gmail address |
| `MAIL_PASSWORD` | Gmail 16-char App Password |
| `ADMIN_USERNAME` | pick your own |
| `ADMIN_PASSWORD` | pick your own |
| `NORMAL_PRICE` | `4000` |
| `PEAK_PRICE` | `7000` |
| `PEAK_SEASON_RANGES` | `10-01:12-31,01-01:03-31` |

### Step 4 — Deploy
Click **Deploy**. Vercel builds and gives you a live URL like
`https://jhd-hotel.vercel.app`

### Step 5 — Seed the database (one-time)
Vercel doesn't give you a persistent shell, so run the seed script **locally**
pointed at your live database:
```bash
# In your local .env, temporarily set DATABASE_URL to your Neon connection string
python seed_data.py
```
This creates the 33 rooms directly in your live Postgres database — done once.

---

## 🚀 ALTERNATIVE: Render.com (simpler — supports SQLite-free Postgres add-on built in)

If Vercel's database requirement feels like extra hassle, **Render.com** is
easier for Flask apps — it gives you a free Postgres database in the same
dashboard with no separate sign-up needed.

1. render.com → New → Web Service → connect your GitHub repo
2. Render reads `render.yaml` automatically
3. Add a free Postgres database from Render's "+ New" — `DATABASE_URL` is
   set automatically
4. Add the same environment variables as above
5. Deploy → run `python seed_data.py` once via Render's Shell tab

---

## 🌸 AUTOMATIC SEASONAL PRICING — How It Works

The price is **never set manually**. It's calculated automatically from the
guest's selected check-in date:

- Guest picks a check-in date → price instantly shown (no page reload)
- If that date falls inside `PEAK_SEASON_RANGES` → peak price applies
- Otherwise → normal price applies
- The booking is created with whichever rate matches the actual check-in date

**To change your peak season dates**, edit `PEAK_SEASON_RANGES` in your
environment variables. Format: `MM-DD:MM-DD,MM-DD:MM-DD`

Example — if your peak season is only December and January:
```
PEAK_SEASON_RANGES=12-01:12-31,01-01:01-31
```

No code changes needed — just update the environment variable and redeploy.

---

## 🖼️ ADD YOUR PHOTOS

Place images in `static/images/` and `static/images/rooms/`.
Open `templates/index.html` and `search.html` — replace the dashed-border
placeholder blocks (marked with `👇`) with real `<img src="...">` tags.

## 🍹 SKYBAR PAGE

The restaurant/bar page is now at `/skybar` — update menu photos in
`templates/skybar.html` (marked with `👇` comments).

