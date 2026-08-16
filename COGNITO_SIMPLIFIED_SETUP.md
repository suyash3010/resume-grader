# Cognito + Google OAuth Setup - Simplified Step-by-Step

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
7. Click "Create"

**IMPORTANT**: A popup will show your credentials. Click "Download JSON" and save it locally.

Or copy these two values and save them:
- **Client ID** (looks like: `xxxx.apps.googleusercontent.com`)
- **Client Secret** (looks like: `GOCSPX-xxxxx`)

**SAVE THESE - YOU'LL NEED THEM!**

---

## Part 2: Create AWS Cognito User Pool

### Step 2.1: Go to AWS Cognito
1. Go to: https://console.aws.amazon.com/cognito/
2. Make sure you're in the correct AWS region (top right)
3. Click "User Pools" (left sidebar)
4. Click "Create user pool"

### Step 2.2: Configure Authentication
1. Under "Authentication providers":
   - Check ☑ "Cognito user pool"
   - Check ☑ "Google"
   - Leave others unchecked
2. Click "Next"

### Step 2.3: Password & Recovery Settings
- Keep default settings
- Click "Next"

### Step 2.4: MFA & Recovery
- MFA: "No MFA" (for simplicity)
- Click "Next"

### Step 2.5: Email Configuration
- Keep as "Send email with Cognito"
- Click "Next"

### Step 2.6: App Integration
1. User pool name: `resume-grader-pool`
2. Click "Next"

### Step 2.7: Review & Create
- Review the settings
- Click "Create user pool"
- Wait a few seconds for creation

---

## Part 3: Configure Google as Identity Provider

### Step 3.1: Add Google Provider
1. In your user pool, go to "Sign-in experience" (left menu)
2. Click "Identity providers"
3. Click "Google" button
4. A form will appear:
   - **App client ID**: Paste your Google Client ID (from Step 1.3)
   - **App client secret**: Paste your Google Client Secret (from Step 1.3)
   - **Scopes**: Keep as `email openid profile`
5. Click "Save"

---

## Part 4: Create App Client & Domain

### Step 4.1: Create App Client
1. In your user pool, go to "App integration" (left menu)
2. Click "App clients" (or "App client settings")
3. Click "Create app client" (if button visible) or create in next steps
4. App name: `resume-grader-client`
5. App type: "Public client"
6. Click "Create"

**SAVE THIS**: Note your **Client ID**

### Step 4.2: Configure App Client
1. Click on your app client name
2. Scroll to "Allowed redirect URIs"
3. Click "Add another redirect URI"
4. Add these:
   ```
   http://localhost:5000/callback
   https://your-lambda-url.lambda-url.us-east-1.on.aws/callback
   ```
   (You'll get the Lambda URL after deployment)
5. Click "Save"

### Step 4.3: Create Cognito Domain
1. Go to "App integration" → "Domain" (or "Domain name")
2. Click "Create Cognito domain"
3. Domain prefix: `resume-grader-<your-name>` (must be unique)
4. Click "Create domain"
5. Wait for it to be created (takes ~1 minute)

**SAVE THIS**: Your domain will be:
```
https://resume-grader-<your-name>.auth.us-east-1.amazoncognito.com
```

---

## Part 5: Get Your Credentials

You should now have:

```
COGNITO_USER_POOL_ID = us-east-1_xxxxx
COGNITO_CLIENT_ID = xxxxxxxxxxxxx
COGNITO_CLIENT_SECRET = (leave empty for public client, or copy if private)
COGNITO_DOMAIN = resume-grader-xxxxx
COGNITO_REGION = us-east-1
GOOGLE_CLIENT_ID = xxxxx.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET = GOCSPX-xxxxx
```

---

## Part 6: Update Your .env File

Create/Update `.env`:

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

## Part 7: Test Locally

```bash
pip install -r requirements.txt
python3 app.py
```

Visit: http://localhost:5000

You should see "Continue with Google" button!

---

## Troubleshooting

**"Cannot find Google+ API"**
- Make sure you're in Google Cloud Console, not AWS

**"Invalid redirect_uri"**
- Add http://localhost:5000/callback to Cognito app client redirect URIs

**"Client not found"**
- Make sure Client ID and Client Secret are correct
- Copy carefully without extra spaces

**"Domain already exists"**
- Use a different suffix (add numbers or your initials)

---

## Quick Reference Map

| What | Where | How to Find |
|------|-------|------------|
| Google Credentials | Google Cloud Console | APIs & Services → Credentials |
| User Pool ID | AWS Cognito | User Pools → Your Pool → General Settings |
| Client ID | AWS Cognito | App integration → App clients → Your Client → Client ID |
| Domain | AWS Cognito | App integration → Domain |
| Redirect URIs | AWS Cognito | App integration → App clients → Your Client → Redirect URIs |

---

## Next Steps

1. ✅ Complete steps above
2. Update `.env` with credentials
3. Run `python3 app.py`
4. Click "Continue with Google"
5. Sign in with your Google account
6. If it works, you're done!

If stuck, DM me the exact error message!
