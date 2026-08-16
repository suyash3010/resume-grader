# Quick Start: Deploy Resume Grader to AWS

Choose one of the two deployment methods below. **Zappa is easier for beginners.**

## Option 1: Zappa Deployment (⭐ Recommended - Easier)

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Create an S3 bucket for Zappa (one-time setup)
```bash
aws s3api create-bucket --bucket zappa-deployments-resume-grader --region us-east-1
```

Replace `us-east-1` with your preferred AWS region.

### 3. Set your OpenAI API key
```bash
export OPENAI_API_KEY="sk-..."  # Your OpenAI API key
```

### 4. Deploy to AWS Lambda
```bash
zappa deploy dev
```

Wait for deployment to complete. You'll see output like:
```
Your API Gateway URL is https://xxxxxxxx.execute-api.us-east-1.amazonaws.com/dev
```

### 5. Open in browser
Visit the URL from step 4 in your browser!

### Later: Update after code changes
```bash
zappa update dev
```

### Cleanup: Remove from AWS
```bash
zappa undeploy dev --remove-logs
```

---

## Option 2: AWS SAM Deployment (More Control)

### 1. Install SAM CLI
```bash
brew install aws-sam-cli  # macOS
# or visit: https://aws.amazon.com/serverless/sam/
```

### 2. Build the application
```bash
sam build
```

### 3. Deploy with guided setup
```bash
sam deploy --guided
```

Answer the prompts:
- Stack Name: `resume-grader`
- Region: `us-east-1` (or your preferred region)
- Parameter OpenAIApiKey: Paste your OpenAI API key
- Confirm changes before deploy: `y`
- Allow SAM CLI IAM role creation: `Y`
- Save parameters: `Y`

### 4. Get your API endpoint
After deployment, you'll see:
```
Key             ResumeGraderApiEndpoint
Value           https://xxxxxxxx.execute-api.us-east-1.amazonaws.com/prod
```

Visit that URL in your browser!

### Later: Update after code changes
```bash
sam build
sam deploy
```

### Cleanup: Remove from AWS
```bash
aws cloudformation delete-stack --stack-name resume-grader
```

---

## Troubleshooting

### "OPENAI_API_KEY not configured"
Make sure you set the environment variable before deploying:
```bash
export OPENAI_API_KEY="sk-..."
```

For Zappa, update `zappa_settings.json` with:
```json
"environment_variables": {
    "OPENAI_API_KEY": "sk-..."
}
```

### Function timeout (takes >5 minutes)
Processing too many resumes at once. Increase timeout in settings or split uploads.

### Out of memory
Zappa: Increase `memory_size` in `zappa_settings.json`
SAM: Increase `MemorySize` in `template.yaml`

### Need to check logs
```bash
# Zappa
zappa tail dev

# SAM
sam logs -n ResumeGraderFunction --stack-name resume-grader -t
```

---

## Estimated Costs

- **Lambda**: $0.20/month (free tier covers 1M requests)
- **API Gateway**: $0.35/month (free tier covers 1M requests)  
- **OpenAI API**: $0.001-0.01 per resume
- **S3 (if needed)**: $0.023/GB/month

**Total: ~$1-20/month for low usage**

---

## Next Steps

1. Test the app by uploading some resumes
2. Download the ranked shortlist as Excel
3. Share the URL with your team!

For questions or issues, check AWS CloudWatch Logs or run `zappa tail dev` for Zappa users.
