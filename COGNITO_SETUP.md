# AWS Cognito + Google Login Implementation Guide

## Overview
This guide walks through setting up AWS Cognito with Google OAuth for the Resume Grader app.

## Step 1: Create Cognito User Pool

### A. Create User Pool in AWS Console

1. Go to AWS Console → Cognito
2. Click "Create user pool"
3. Choose authentication providers:
   - ☑ Google
   - ☑ Email
   - ☑ Username
4. Click "Next"

### B. Configure Password Policy
- Leave default password requirements
- Click "Next"

### C. Configure MFA and Account Recovery
- Choose "No MFA" for now
- Click "Next"

### D. Configure Message Delivery
- Choose "Send email with Cognito"
- Click "Next"

### E. Integrate Your App
- User pool name: `resume-grader-users`
- App client name: `resume-grader-client`
- Generate client secret: ☑ (checked)
- Click "Create user pool"

## Step 2: Configure Google OAuth Provider

### A. Create Google OAuth Credentials

1. Go to Google Cloud Console: https://console.cloud.google.com/
2. Create a new project: "Resume Grader"
3. Enable Google+ API
4. Go to "Credentials" → "Create Credentials" → "OAuth 2.0 Client ID"
5. Choose "Web Application"
6. Add Authorized redirect URIs:
   ```
   https://<your-cognito-domain>.auth.<region>.amazoncognito.com/oauth2/idpresponse
   ```
   (You'll get the domain in Step 3)

7. Copy the Client ID and Client Secret

### B. Add Google as Identity Provider in Cognito

1. Go to AWS Cognito → Your User Pool
2. Click "Identity providers" → "Google"
3. Paste Google Client ID and Client Secret
4. Scopes: Keep default (email, profile, openid)
5. Click "Save"

## Step 3: Configure Hosted UI

1. Go to "App integration" → "App client settings"
2. Set Callback URL(s):
   ```
   https://your-lambda-url/
   https://localhost:5000/
   ```
3. Set Sign out URL(s):
   ```
   https://your-lambda-url/logout
   https://localhost:5000/logout
   ```
4. Enable identity providers: Google, Cognito User Pool
5. OAuth 2.0 grant types: Authorization code grant
6. Scopes: email, openid, profile
7. Save

## Step 4: Create Cognito Domain

1. Go to "App integration" → "Domain name"
2. Create domain: `resume-grader-<random>`
3. Note the full domain URL

## Step 5: Environment Variables

Add to `.env` and CloudFormation:

```
COGNITO_USER_POOL_ID=us-east-1_xxxxx
COGNITO_CLIENT_ID=xxxxxxxxxxxx
COGNITO_CLIENT_SECRET=xxxxxxxxxxxxx
COGNITO_DOMAIN=resume-grader-xxxx
COGNITO_REGION=us-east-1
```

## Step 6: Update Template.yaml

Add Cognito environment variables to Lambda function:

```yaml
Environment:
  Variables:
    OPENAI_API_KEY: !Ref OpenAIApiKey
    COGNITO_USER_POOL_ID: !Ref CognitoUserPoolId
    COGNITO_CLIENT_ID: !Ref CognitoClientId
    COGNITO_CLIENT_SECRET: !Ref CognitoClientSecret
    COGNITO_DOMAIN: !Ref CognitoDomain
    COGNITO_REGION: !Ref CognitoRegion
```

Add Parameters to template.yaml:

```yaml
Parameters:
  CognitoUserPoolId:
    Type: String
    Description: AWS Cognito User Pool ID
  CognitoClientId:
    Type: String
    Description: AWS Cognito Client ID
  CognitoClientSecret:
    Type: String
    NoEcho: true
    Description: AWS Cognito Client Secret
  CognitoDomain:
    Type: String
    Description: AWS Cognito Domain name
  CognitoRegion:
    Type: String
    Default: us-east-1
    Description: AWS Region for Cognito
```

## Architecture

```
┌─────────────┐
│   User      │
└──────┬──────┘
       │
       ▼ Click "Login with Google"
┌─────────────────────────┐
│  Flask App              │
│  /login endpoint        │
└──────┬──────────────────┘
       │
       ▼ Redirect to
┌─────────────────────────────────┐
│  AWS Cognito Hosted UI          │
│  (Shows Google login button)     │
└──────┬──────────────────────────┘
       │
       ▼ User clicks Google
┌─────────────────────────────────┐
│  Google OAuth Consent Screen    │
└──────┬──────────────────────────┘
       │
       ▼ Grant permission
┌──────────────────────────────────┐
│  Cognito receives Google token   │
│  Creates session/ID token        │
└──────┬───────────────────────────┘
       │
       ▼ Redirect back to
┌────────────────────────────────────┐
│  /login/callback endpoint          │
│  (Exchange code for tokens)        │
└──────┬─────────────────────────────┘
       │
       ▼ Store in session
┌────────────────────────────────────┐
│  Flask app                         │
│  User authenticated & logged in    │
└────────────────────────────────────┘
```

## Implementation Steps

1. ✅ Create Cognito User Pool
2. ✅ Configure Google OAuth provider
3. ✅ Update template.yaml with Cognito parameters
4. ⬜ Update app.py with login/logout logic
5. ⬜ Protect /grade endpoint (require auth)
6. ⬜ Update HTML with login button
7. ⬜ Add user info display
8. ⬜ Add logout button
9. ⬜ Test locally
10. ⬜ Deploy to Lambda

## Testing Locally

```bash
export COGNITO_USER_POOL_ID=us-east-1_xxxxx
export COGNITO_CLIENT_ID=xxxxxxxxx
export COGNITO_CLIENT_SECRET=xxxxxxxxx
export COGNITO_DOMAIN=resume-grader-xxxx
export COGNITO_REGION=us-east-1

python3 app.py
# Visit http://localhost:5000/login
```

## Troubleshooting

**Issue: Invalid redirect_uri**
- Solution: Add localhost:5000 to Cognito Callback URLs

**Issue: CORS errors**
- Solution: Check Cognito domain allows your origin

**Issue: Token validation fails**
- Solution: Verify Client ID and Secret match

## Cost
- Cognito: Free tier includes 50k MAU
- Google OAuth: Free
- Total: ~$0 for small teams
