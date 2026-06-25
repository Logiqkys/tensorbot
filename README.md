# Discord Premium Role Bot

A small Discord bot for **Tensor Works** that posts a button in `#verify-here`. When a user clicks **Get your Premium Role**, they receive the **Premium** role and can see the **Premium Workflow** channels.

## What it does

1. Admin runs `/setup` in `#verify-here`
2. Bot posts an embed with a **Get your Premium Role** button
3. User clicks the button and gets the **Premium** role
4. Discord channel permissions show the **Premium Workflow** category to that user

## One-time Discord setup

### 1. Create the Premium role

1. Open your server **Server Settings** → **Roles**
2. Create a role named exactly: `Premium`
3. Save it (no special permissions needed on the role itself)

### 2. Lock the Premium Workflow category

1. Right-click the **Premium Workflow** category → **Edit Category**
2. Go to **Permissions**
3. For `@everyone`: turn **View Channel** off
4. Add the **Premium** role and turn **View Channel** on
5. Save

Do the same for each channel in that category if they have their own permission overrides.

### 3. Create the bot application

1. Go to [discord.com/developers/applications](https://discord.com/developers/applications)
2. Click **New Application** and give it a name
3. Open **Bot** → **Add Bot**
4. Copy the **Token** (you will add this to Render)
5. Under **Privileged Gateway Intents**, enable **Server Members Intent**
6. Save

### 4. Invite the bot to your server

Use this invite URL (replace `YOUR_CLIENT_ID` with your Application ID from the Developer Portal):

```
https://discord.com/api/oauth2/authorize?client_id=YOUR_CLIENT_ID&permissions=268435456&scope=bot%20applications.commands
```

Permissions included: **Manage Roles**, **Send Messages**, **Use Slash Commands**

### 5. Move the bot role above Premium

In **Server Settings** → **Roles**, drag the bot's role **above** the **Premium** role. The bot must be higher in the list to assign that role.

---

## Host for free on Render

[Render](https://render.com) has a **free web service** tier with **clear logs** in the dashboard. This bot includes a small health server so Render can keep it running.

**Free tier note:** Render free services sleep after ~15 minutes without HTTP traffic. Step 6 below sets up a free ping so the bot stays online 24/7.

### Step 1 — Push code to GitHub

1. Create a repo at [github.com/new](https://github.com/new)
2. In this folder, run:

```powershell
cd "c:\Users\My PC\Documents\discord bot"
git init
git add bot.py requirements.txt render.yaml .gitignore README.md
git commit -m "Add premium role bot"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
git push -u origin main
```

Do **not** commit `.env` — your token stays off GitHub.

### Step 2 — Create a Render account

1. Go to [render.com](https://render.com)
2. Sign up with **GitHub**

### Step 3 — Create the web service

1. Click **New +** → **Blueprint**
2. Connect your GitHub repo
3. Render reads `render.yaml` automatically
4. When asked for `DISCORD_TOKEN`, paste your bot token
5. Click **Apply**

Or create manually:

1. **New +** → **Web Service**
2. Connect your GitHub repo
3. Settings:
   - **Name:** `premium-role-bot`
   - **Runtime:** Python 3
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `python bot.py`
   - **Instance Type:** **Free**
4. Open **Environment** → add:
   - Key: `DISCORD_TOKEN`
   - Value: your bot token
5. Click **Create Web Service**

### Step 4 — Check logs

1. Open your service in the Render dashboard
2. Click the **Logs** tab
3. Wait for deploy to finish — you should see:

```
Health server listening on port 10000
Starting bot...
Logged in as YourBotName#1234
Synced 1 slash command(s)
```

Logs stay visible here anytime — unlike Discloud.

### Step 5 — Use the bot in Discord

1. Confirm the bot is **online** in your Discord server
2. Go to `#verify-here`
3. Run `/setup` (admin only)

### Step 6 — Keep it awake for free (important)

Render free tier sleeps without incoming HTTP requests. Keep the bot online with [UptimeRobot](https://uptimerobot.com) (free):

1. Sign up at [uptimerobot.com](https://uptimerobot.com)
2. Click **Add New Monitor**
3. Type: **HTTP(s)**
4. URL: your Render URL, e.g. `https://premium-role-bot.onrender.com/health`
5. Monitoring interval: **5 minutes**
6. Save

UptimeRobot pings your bot every 5 minutes so Render does not sleep it.

---

## Troubleshooting

| Problem | Fix |
|--------|-----|
| `/setup` does not appear | Wait 1–2 minutes after deploy, or re-invite with `applications.commands` scope |
| `DISCORD_TOKEN is missing` in Logs | Add `DISCORD_TOKEN` in Render **Environment**, then **Manual Deploy** |
| `Invalid bot token` in Logs | Reset token in Developer Portal, update Render Environment, redeploy |
| Bot goes offline after ~15 min | Set up UptimeRobot ping on `/health` (Step 6) |
| `No module named 'audioop'` | Render used Python 3.13+. Add `runtime.txt` (included) or set `PYTHON_VERSION=3.11.9` in Environment, then redeploy |
| "I cannot assign that role" | Move bot role above **Premium** in Server Settings → Roles |
| User still cannot see channels | Check **Premium Workflow** category permissions |

## Files

| File | Purpose |
|------|---------|
| `bot.py` | Bot logic, slash command, button, and health server |
| `requirements.txt` | Python packages |
| `render.yaml` | Render deploy config (free web service) |
| `runtime.txt` | Pins Python 3.11 (required for discord.py on Render) |
| `.env` | Local testing only — not used on Render |
| `.gitignore` | Keeps secrets out of git |
