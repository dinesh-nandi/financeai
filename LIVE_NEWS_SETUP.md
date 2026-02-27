# Live News Setup Guide

Your app shows **live financial news** from [NewsAPI.org](https://newsapi.org). Without an API key, it falls back to **demo/sample** articles. To get real headlines:

---

## Step 1: Get a free API key

1. Go to **https://newsapi.org/register**
2. Sign up (free)
3. After login, open **Dashboard** → copy your **API key**

---

## Step 2: Add the key to your project

1. In your project root (same folder as `manage.py`), create or edit the **`.env`** file.
2. Add this line (replace with your actual key):

   ```
   NEWS_API_KEY=your_api_key_here
   ```

   Example:
   ```
   NEWS_API_KEY=a1b2c3d4e5f6789012345678abcdef12
   ```

3. Save the file.

---

## Step 3: Restart the Django server

- Stop the server (Ctrl+C), then start it again:

  ```bash
  python manage.py runserver
  ```

---

## Verify

- Open the **News** page or wait for the **notification popup** (polls every 30 seconds).
- If the key is valid, you’ll see real business headlines and the source will show as **"live"** instead of **"demo"**.

---

## Notes

- **Free tier**: NewsAPI free plan has a limited number of requests per day (e.g. 100). Your app polls every 30 seconds, so stay within the limit or reduce polling if needed.
- **Localhost**: The free key works for requests from `localhost` / `127.0.0.1`. For production on a public domain, check NewsAPI’s plan and domain rules.
- **No .env?** If you don’t have a `.env` file, copy `.env.example` to `.env`, then add `NEWS_API_KEY=your_key` and restart the server.
