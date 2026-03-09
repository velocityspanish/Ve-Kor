# 🔐 GitHub Secrets Setup Guide

## Required Secrets for Velocity French Bot

### Step-by-Step Instructions

1. **Go to your GitHub repository**
2. **Click Settings** (top right tab)
3. **Click "Secrets and variables" → "Actions"** (left sidebar)
4. **Click "New repository secret"** (top right)
5. **Add each secret below**

---

## 🎬 Required Secrets

### 1. Pollinations AI (Content Generation)

```
Name: POLLINATIONS_API_KEY
Value: sk_4zphLgWL41PgQM63uVA9LSFKm8BObgY5
```

**Get your key:** https://enter.pollinations.ai

---

### 2. Facebook (Reels Upload)

```
Name: FACEBOOK_ACCESS_TOKEN
Value: [Your Facebook Page Access Token]
```

**How to get:**
1. Go to https://developers.facebook.com/tools/explorer
2. Select your app
3. Get Page Access Token with permissions: `pages_manage_posts`, `pages_read_engagement`, `publish_video`
4. Token starts with `EAAG...`

```
Name: FACEBOOK_PAGE_ID
Value: [Your Facebook Page ID]
```

**How to get:**
1. Go to your Facebook Page
2. Click "About"
3. Find Page ID (or use https://findmyfbid.in/)

---

### 3. Instagram (Reels Upload)

```
Name: INSTAGRAM_ACCESS_TOKEN
Value: [Your Instagram Access Token]
```

**How to get:**
1. Connect Instagram to Facebook Page
2. Use Facebook Graph API Explorer
3. Get token with `instagram_basic`, `instagram_content_publish`
4. Token starts with `IGAA...` or `EAAG...`

```
Name: INSTAGRAM_ACCOUNT_ID
Value: [Your Instagram Business Account ID]
```

**How to get:**
1. Go to https://graph.instagram.com/me?fields=id,username&access_token=YOUR_TOKEN
2. Copy the `id` value

```
Name: IG_USER_ID
Value: [Same as INSTAGRAM_ACCOUNT_ID or leave empty]
```

---

## 📌 Optional Secrets (Other Platforms)

### VK (VKontakte)

```
Name: VK_ACCESS_TOKEN
Value: vk1.a.XXXXXX (from your .env file)

Name: VK_GROUP_ID
Value: -56 (from your .env file, keep the minus sign)
```

**Already configured!** ✅

---

### Telegram

```
Name: TELEGRAM_BOT_TOKEN
Value: [Get from @BotFather on Telegram]

Name: TELEGRAM_CHANNEL_ID
Value: [Your channel ID, e.g., @yourchannel or -100XXXXXXXXXX]
```

---

### Twitter/X

```
Name: TWITTER_API_KEY
Value: [Your Twitter API Key]

Name: TWITTER_API_SECRET
Value: [Your Twitter API Secret]

Name: TWITTER_ACCESS_TOKEN
Value: [Your Twitter Access Token]

Name: TWITTER_ACCESS_SECRET
Value: [Your Twitter Access Secret]
```

**Get keys:** https://developer.twitter.com/en/portal/dashboard

---

### TikTok

```
Name: TIKTOK_ACCESS_TOKEN
Value: [Your TikTok Access Token]
```

**Get token:** TikTok Developer Portal

---

### Threads

```
Name: THREADS_ACCESS_TOKEN
Value: [Your Threads Access Token]

Name: THREADS_USER_ID
Value: [Your Threads User ID]
```

---

## ✅ Verify Setup

After adding all secrets:

1. **Go to Actions tab**
2. **Click "Velocity French - Daily 4x Upload"**
3. **Click "Run workflow" (dropdown)**
4. **Select branch → Click "Run workflow"**

The workflow will:
- ✅ Generate a new French learning reel
- ✅ Upload to Facebook and Instagram
- ✅ Save artifacts for verification

---

## 🔍 Check Results

After workflow completes:

1. **Check "Upload video artifact"** - Download generated reel
2. **Check "Upload logs"** - View generation and upload results
3. **Check your Facebook/Instagram** - Verify posts are live

---

## ⚠️ Important Notes

### Token Expiry

- **Facebook tokens** expire every 60 days
- **Instagram tokens** may expire
- **Refresh tokens** before expiry to avoid downtime

### Token Permissions

Make sure tokens have these permissions:

**Facebook:**
- `pages_manage_posts`
- `pages_read_engagement`
- `publish_video`

**Instagram:**
- `instagram_basic`
- `instagram_content_publish`

### Security

- ✅ Never commit `.env` file to Git
- ✅ Use GitHub Secrets (encrypted)
- ✅ Rotate tokens periodically
- ✅ Don't share tokens publicly

---

## 🐛 Troubleshooting

### "Secret not found" Error

1. Check secret name spelling (case-sensitive!)
2. Verify secret is in repository settings (not organization)
3. Make sure workflow has access to secrets

### "Token expired" Error

1. Regenerate token from platform
2. Update GitHub secret
3. Re-run workflow

### "Permission denied" Error

1. Check token has required permissions
2. For Facebook: Ensure Page is connected to your app
3. For Instagram: Ensure it's a Business account

---

## 📞 Need Help?

1. Check workflow logs in Actions tab
2. Look for error messages in upload results
3. Verify all secrets are set correctly
4. Test with manual workflow trigger first

---

**Setup complete! Your bot will post 4x daily automatically! 🎉**
