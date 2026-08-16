# Cognito + Google OAuth Setup - Simplified Step-by-Step (Updated 2026)

## Part 1: Create OAuth Credentials in Google Cloud

### Step 1.1: Create Google Project
1. Go to: https://console.cloud.google.com/
2. Click the project dropdown at the top
3. Click "New Project"
4. Name: "Resume Grader"
5. Click "Create"
6. Wait for project to be created (takes ~30 seconds)

### Step 1.2: Enable Google+ API
1. In the left sidebar, click "APIs & Services" → "Library"
2. Search for "Google+ API"
3. Click on it
4. Click "Enable"
5. Wait for it to enable

### Step 1.3: Create OAuth Credentials
1. Click "APIs & Services" → "Credentials" (left sidebar)
2. Click "Create Credentials" (blue button at top)
3. Choose "OAuth 2.0 Client ID"
4. If prompted to create consent screen:
   - Click "Create Consent Screen"
   - Choose "External"
   - Click "Create"
   - Fill in:
     - App name: "Resume Grader"
     - User support email: your email
     - Scroll down, add your email again in "Developer contact"
     - Click "Save and Continue"
   - Click "Continue" for scopes
   - Click "Continue" for test users
   - Click "Back to Dashboard"

5. Now click "Create Credentials" again → "OAuth 2.0 Client ID"
6. Choose "Web application"
7. Under "Authorized JavaScript origins", add:
   ```
   http://localhost:5000
   https://your-lambda-url.lambda-url.us-east-1.on.aws
   ```
8. Under "Authorized redirect URIs", add:
   ```
   http://localhost:5000/callback
   https://your-lambda-url.lambda-url.us-east-1.on.aws/callback
   https://resume-grader-xxxxx.auth.us-east-1.amazoncognito.com/oauth2/idpresponse
   ```
   (Use your Cognito domain from Step 3.3)

9. Click "Create"

**IMPORTANT**: A popup will show your credentials. Copy these two values:
- **Client ID** (looks like: `xxxx.apps.googleusercontent.com`)
- **Client Secret** (looks like: `GOCSPX-xxxxx`)

**SAVE THESE - YOU'LL NEED THEM!**

---

## Part 2: Create AWS Cognito User Pool

### Step 2.1: Go to AWS Cognito
1. Go to: https://console.aws.amazon.com/cognito/
2. Make sure you're in the correct AWS region (top right) - recommend `us-east-1`
3. Click "User Pools" (left sidebar)
4. Click "Create user pool" (orange button)

### Step 2.2: Create User Pool (Quick Setup)
1. User pool name: `resume-grader-pool`
2. Click "Next"

### Step 2.3-2.7: Configure Settings (Accept Defaults)
- Just click "Next" through all remaining steps:
  - Sign-in experience
  - Security requirements
  - Sign-up experience
  - Message delivery
  - Integrate your app
3. On final review, click "Create user pool"
4. Wait ~30 seconds for creation

**IMPORTANT**: After creation, find and save:
- **User Pool ID** (in "User Pools" list or "General Settings")
- Looks like: `us-east-1_xxxxx`

---

## Part 3: Add Google as Identity Provider (AFTER Pool Creation)

### Step 3.1: Go to Identity Providers
1. Click on your new user pool: `resume-grader-pool`
2. Left sidebar → "Sign-in experience"
3. Click "Identity providers"
4. You should see a "Google" button - click it

### Step 3.2: Configure Google Provider
A form will appear:
- **App client ID**: Paste your Google Client ID (from Part 1.3)
  - Example: `123456789.apps.googleusercontent.com`
- **App client secret**: Paste your Google Client Secret (from Part 1.3)
  - Example: `GOCSPX-xxxxx`
- **Scopes**: Keep as `email openid profile`
- Click "Save"

---

## Part 4: Create App Client

### Step 4.1: Create App Client
1. Left sidebar → "App integration"
2. Click "App clients and analytics"
3. Click "Create app client" (blue button)
4. Settings:
   - App client name: `resume-grader-client`
   - Uncheck "Generate client secret" (for public client)
   - Click "Create app client"

**SAVE THIS**: Note your **Client ID**
- You'll see it in the app client details

### Step 4.2: Configure Redirect URIs
1. Still in App integration, click "App client settings"
2. Find "Allowed redirect URIs"
3. Add both:
   ```
   http://localhost:5000/callback
   https://your-lambda-url/callback
   ```
   (Lambda URL comes after deployment)
4. Find "Allowed sign-out URLs"
5. Add:
   ```
   http://localhost:5000/logout
   https://your-lambda-url/logout
   ```
6. Click "Save"

---

## Part 5: Create Cognito Domain

### Step 5.1: Create Domain
1. Left sidebar → "App integration"
2. Click "Domain name"
3. Click "Create Cognito domain"
4. Domain prefix: `resume-grader-<your-name>`
   - Must be unique globally
   - Use your last name or add numbers: `resume-grader-smith-2026`
5. Click "Create domain"
6. Wait ~1 minute for creation

**SAVE THIS**: Your Cognito domain:
```
https://resume-grader-<your-name>.auth.us-east-1.amazoncognito.com
```

---

## Part 6: Collect All Your Credentials

You should now have all of these. Write them down:

```
# FROM GOOGLE CLOUD (Part 1)
GOOGLE_CLIENT_ID = xxxxx.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET = GOCSPX-xxxxx

# FROM AWS COGNITO (Parts 2-5)
COGNITO_USER_POOL_ID = us-east-1_xxxxx
COGNITO_CLIENT_ID = xxxxxxxxxxxxxxx
COGNITO_DOMAIN = resume-grader-xxxx
COGNITO_REGION = us-east-1

# GENERATE YOURSELF
FLASK_SECRET_KEY = any-random-string-here
```

---

## Part 7: Update Your .env File

Edit or create `.env` in your project:

```bash
OPENAI_API_KEY=sk-proj-your-key
COGNITO_USER_POOL_ID=us-east-1_xxxxx
COGNITO_CLIENT_ID=your-cognito-client-id
COGNITO_CLIENT_SECRET=your-cognito-client-secret
COGNITO_DOMAIN=resume-grader-xxxxx
COGNITO_REGION=us-east-1
FLASK_SECRET_KEY=any-random-string-here
```

---

## Part 8: Test Locally

```bash
pip install -r requirements.txt
python3 app.py
```

Open browser: http://localhost:5000

**You should see:**
- "Continue with Google" button (if not logged in)
- Your profile + logout button (if logged in)

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| "Google button not appearing" | Make sure you added Google provider AFTER creating pool |
| "Invalid redirect_uri" | Add `http://localhost:5000/callback` to Cognito redirect URIs |
| "Client not found" | Copy Client ID/Secret carefully without extra spaces |
| "Domain already exists" | Use different suffix (add numbers or initials) |
| "Cannot find Identity providers" | Click on your pool first, then "Sign-in experience" → "Identity providers" |
| "App client not created" | Make sure you're in "App integration" → "App clients and analytics" |

---

## Key Differences from Old Guide

✅ Google is added AFTER pool creation (not during)
✅ Simpler setup flow with fewer steps
✅ Clear separation of Google Cloud vs AWS Cognito
✅ Actual current AWS UI (as of 2026)
✅ Step-by-step with exact button locations

---

## Quick Checklist

- [ ] Part 1: Google OAuth credentials created
- [ ] Part 2: Cognito User Pool created
- [ ] Part 3: Google added as identity provider
- [ ] Part 4: App client created
- [ ] Part 5: Cognito domain created
- [ ] Part 6: All credentials saved
- [ ] Part 7: .env file updated
- [ ] Part 8: Testing locally - "Continue with Google" button appears

---

## Next Steps

1. ✅ Follow all 8 parts above
2. Test locally (Part 8)
3. If login works, ready to deploy!
4. If stuck, share the exact error message

**Need help?** Share which step you're stuck on and what you see!
