# Deployment Guide for Recipe Telegram Bot

This guide covers multiple free/cheap deployment options for running your bot 24/7.

## Prerequisites

1. Create a Telegram bot via [@BotFather](https://t.me/botfather)
2. Get an OpenAI API key from [OpenAI Platform](https://platform.openai.com/)
3. Fork/clone this repository

## Deployment Options

### 1. AWS Lambda (Free Tier) ⭐ Recommended

AWS Lambda offers 1 million free requests per month, perfect for a Telegram bot.

#### Setup Steps:

1. **Install Serverless Framework:**
   ```bash
   npm install -g serverless
   npm install --save-dev serverless-python-requirements
   ```

2. **Configure AWS credentials:**
   ```bash
   serverless config credentials --provider aws --key YOUR_KEY --secret YOUR_SECRET
   ```

3. **Deploy:**
   ```bash
   # Set environment variables
   export TELEGRAM_BOT_TOKEN=your_token
   export OPENAI_API_KEY=your_key
   
   # Deploy
   serverless deploy
   ```

4. **Set Telegram webhook:**
   ```bash
   curl -F "url=https://YOUR_LAMBDA_URL/prod/webhook" \
        https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook
   ```

**Pros:** 
- Truly serverless, no maintenance
- Scales automatically
- 1M requests free/month
- No cold start issues for bots

**Cons:**
- 15-minute execution limit
- Storage is temporary (use DynamoDB for persistence)

### 2. Railway (Simple & Free)

Railway offers $5 free credit monthly, enough for a small bot.

#### Setup Steps:

1. **Connect GitHub repo** to Railway
2. **Add environment variables** in Railway dashboard:
   - `TELEGRAM_BOT_TOKEN`
   - `OPENAI_API_KEY`
3. **Deploy** (automatic from GitHub)
4. **Set webhook** using Railway's provided URL

**Pros:**
- Dead simple deployment
- Auto-deploys from GitHub
- Good free tier
- Persistent storage

**Cons:**
- Limited free credits
- May need paid plan for heavy usage

### 3. Render (Free with limitations)

Render offers free hosting but with spin-down after 15 minutes of inactivity.

#### Setup Steps:

1. **Create a new Web Service** on Render
2. **Connect your GitHub repository**
3. **Configure:**
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `python webhook_server.py`
4. **Add environment variables**
5. **Deploy**

**Pros:**
- Completely free tier
- Easy GitHub integration
- Good for testing

**Cons:**
- Spins down after 15 min (slow cold starts)
- Limited to 750 hours/month

### 4. Fly.io (Generous Free Tier)

Fly.io offers great free tier with 3 shared-cpu-1x VMs.

#### Setup Steps:

1. **Install flyctl:**
   ```bash
   curl -L https://fly.io/install.sh | sh
   ```

2. **Launch app:**
   ```bash
   fly launch
   ```

3. **Set secrets:**
   ```bash
   fly secrets set TELEGRAM_BOT_TOKEN=your_token
   fly secrets set OPENAI_API_KEY=your_key
   ```

4. **Deploy:**
   ```bash
   fly deploy
   ```

**Pros:**
- 3 free VMs
- Global deployment
- Great performance
- Persistent storage

**Cons:**
- Requires credit card (but won't charge)
- More complex than others

### 5. Google Cloud Run (Pay-per-use)

Cloud Run charges only for actual usage, often free for small bots.

#### Setup Steps:

1. **Build container:**
   ```bash
   gcloud builds submit --tag gcr.io/YOUR_PROJECT/recipe-bot
   ```

2. **Deploy:**
   ```bash
   gcloud run deploy --image gcr.io/YOUR_PROJECT/recipe-bot \
     --platform managed \
     --set-env-vars TELEGRAM_BOT_TOKEN=token,OPENAI_API_KEY=key
   ```

**Pros:**
- Scales to zero
- Pay only for usage
- Usually free for small bots
- Fast cold starts

**Cons:**
- Requires GCP account
- More complex setup

## Setting Webhook URL

After deployment, set your bot's webhook:

```bash
curl -F "url=https://YOUR_DEPLOYMENT_URL/webhook" \
     https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook
```

## Environment Variables

All deployments need these environment variables:
- `TELEGRAM_BOT_TOKEN` - Your bot token from BotFather
- `OPENAI_API_KEY` - Your OpenAI API key
- `WEBHOOK_URL` - Your deployment URL + /webhook (optional, for webhook mode)
- `STORAGE_PATH` - Path for storing recipes (default: /tmp/recipe_data)

## Storage Considerations

- **AWS Lambda**: Use DynamoDB or S3 for persistent storage
- **Railway/Fly.io**: Local storage works fine
- **Render**: Storage resets on redeploy
- **Cloud Run**: Use Cloud Storage or Firestore

## Monitoring

1. **AWS Lambda**: CloudWatch Logs
2. **Railway**: Built-in logs in dashboard
3. **Render**: Log streams in dashboard
4. **Fly.io**: `fly logs`
5. **Cloud Run**: Cloud Logging

## Cost Optimization Tips

1. Use webhook mode instead of polling
2. Implement caching for repeated requests
3. Use smaller OpenAI models (gpt-4o-mini)
4. Set up billing alerts
5. Monitor usage regularly

## Troubleshooting

### Bot not responding?
- Check webhook is set correctly
- Verify environment variables
- Check deployment logs
- Test with curl: `curl https://YOUR_URL/health`

### Storage issues?
- For serverless, use external storage
- Check write permissions on storage path
- Consider using cloud storage services

### Rate limiting?
- Implement request queuing
- Add retry logic with exponential backoff
- Consider caching responses