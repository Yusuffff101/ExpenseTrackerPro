# Deploy ExpenseTracker Pro

Recommended stack:

- Frontend: Vercel
- Backend: Render
- PostgreSQL: Neon

Deploy in this order: Neon, Render, Vercel, then Telegram.

## 1. Create the Neon database

1. Create a Neon project.
2. Open **Connect** and enable **Connection pooling**.
3. Copy the full connection string. Keep its query parameters intact.
4. Save it privately; it becomes Render's `DATABASE_URL`.

Do not put this value in Git or in the Vercel project.

## 2. Deploy the FastAPI backend to Render

The repository includes `render.yaml`, so Render can create the service as a Blueprint.

1. Push this repository to GitHub.
2. In Render, select **New > Blueprint** and connect the repository.
3. Render reads the root `render.yaml` file.
4. Enter these environment values when prompted:

| Variable | Value |
| --- | --- |
| `DATABASE_URL` | The pooled Neon connection string |
| `FRONTEND_URLS` | `https://your-project.vercel.app` (a placeholder is fine initially) |
| `TELEGRAM_BOT_TOKEN` | Optional until Telegram setup |
| `TELEGRAM_WEBHOOK_URL` | Optional until Telegram setup |

`SECRET_KEY` is generated automatically. Do not change it after users begin logging in, because changing it invalidates existing tokens.

The service startup command runs the idempotent database migration and then starts Uvicorn. When the deployment finishes, verify:

```text
https://YOUR-RENDER-SERVICE.onrender.com/health
https://YOUR-RENDER-SERVICE.onrender.com/docs
```

The health URL should return `{"status":"healthy"}`.

### Manual Render setup

If you do not use the Blueprint, create a Python Web Service with:

| Setting | Value |
| --- | --- |
| Root directory | `backend` |
| Build command | `pip install -r requirements.txt` |
| Start command | `python migrate_all.py && uvicorn main:app --host 0.0.0.0 --port $PORT` |
| Health check | `/health` |

Add the same environment variables listed above.

## 3. Deploy the React frontend to Vercel

1. Import the same GitHub repository into Vercel.
2. Set **Root Directory** to `frontend`.
3. Vercel should detect Vite automatically. Confirm:

| Setting | Value |
| --- | --- |
| Build command | `npm run build` |
| Output directory | `dist` |
| Install command | `npm install` |

4. Add this environment variable for Production and Preview:

```text
VITE_API_URL=https://YOUR-RENDER-SERVICE.onrender.com
```

5. Deploy the project.

The included `vercel.json` enables React Router deep links such as `/login` and `/dashboard`.

## 4. Finalize CORS

Copy the final Vercel production URL. In Render, change:

```text
FRONTEND_URLS=https://YOUR-PROJECT.vercel.app
```

Then redeploy the Render service. Preview deployments are covered by the configured `CORS_ORIGIN_REGEX`.

## 5. Activate Telegram

1. Create a bot with `@BotFather` and copy the token.
2. In Render, set:

```text
TELEGRAM_BOT_TOKEN=your-bot-token
TELEGRAM_WEBHOOK_URL=https://YOUR-RENDER-SERVICE.onrender.com/telegram/webhook
```

3. Redeploy Render.
4. Locally create `backend/.env` with those same two values and run:

```powershell
cd backend
.\venv\Scripts\python.exe set_telegram_webhook.py
```

Never expose the bot token in Vercel or commit it to the repository.

## Common failures

### Browser reports a CORS error

- Check that `FRONTEND_URLS` exactly matches the Vercel origin, with no path.
- Do not include a trailing slash.
- Redeploy Render after changing environment values.

### Backend cannot connect to Neon

- Copy the entire pooled Neon connection string again.
- Check that `DATABASE_URL` is set on Render, not Vercel.
- Confirm the password was not truncated or URL-decoded manually.

### Frontend still calls localhost

- Confirm `VITE_API_URL` is set in Vercel.
- Redeploy the frontend; Vite environment variables are embedded during the build.

### Render says a module cannot be found

- Confirm the service root directory is `backend`.
- Confirm the build command uses `backend/requirements.txt` through that root directory.

### `/login` returns a Vercel 404 after refresh

- Confirm `frontend/vercel.json` was included in the deployed commit.

### Telegram does not respond

- Verify the Render backend is awake and `/health` succeeds.
- Check that the webhook URL ends in `/telegram/webhook` and uses HTTPS.
- Rerun `set_telegram_webhook.py` after changing the token or service URL.
