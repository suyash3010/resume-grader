# Resume Grader - Deployment Guide

## Prerequisites

### AWS Setup
1. AWS Account (with billing enabled)
2. AWS CLI configured: `aws configure`
3. SAM CLI installed: `sam --version` (should be 1.50+)
4. Git (for cloning if needed)

### OpenAI Setup
1. OpenAI account at https://platform.openai.com
2. API key with gpt-4o access (requires paid plan, not free trial)
3. Active billing/payment method
4. Verify access: Run `python3 test_openai.py`

## Step-by-Step Deployment

### 1. Prepare Your Environment

```bash
cd /Users/suyashshukla/PyCharmMiscProject
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Test Locally First

```bash
# Create .env with your OpenAI key
echo "OPENAI_API_KEY=sk-proj-YOUR-KEY" > .env

# Run the app
python3 app.py

# In browser: http://localhost:5000
# Test with a sample resume
```

### 3. Verify OpenAI Access

```bash
python3 test_openai.py
# Output should show: "✓ gpt-4o access confirmed: gpt-4o"
```

### 4. Build SAM Application

```bash
sam build
```

This creates `.aws-sam/build/` directory with Lambda package.

### 5. Deploy to AWS

```bash
sam deploy --stack-name resume-grader-httpapi \
  --parameter-overrides OpenAIApiKey="sk-proj-YOUR-KEY"
```

Follow prompts:
- Stack name: `resume-grader-httpapi`
- AWS Region: `eu-west-1` (or your preferred region)
- Confirm changes: Yes (y)
- Capabilities: Yes (y)

### 6. Get Your Endpoint

After deployment completes:

```bash
aws cloudformation describe-stacks \
  --stack-name resume-grader-httpapi \
  --query 'Stacks[0].Outputs'
```

Copy the API endpoint URL. This is your public Resume Grader URL.

## Monitoring

### View Logs
```bash
aws logs tail /aws/lambda/resume-grader-function --follow
```

### View Stack Status
```bash
aws cloudformation describe-stacks \
  --stack-name resume-grader-httpapi \
  --query 'Stacks[0].StackStatus'
```

### View Costs
CloudWatch → Billing → View usage by service

## Updating the Application

### Update Code
```bash
# Edit app.py or other files
# ...

# Rebuild and deploy
sam build
sam deploy --stack-name resume-grader-httpapi
```

### Update API Key (if needed)
```bash
sam deploy --stack-name resume-grader-httpapi \
  --parameter-overrides OpenAIApiKey="sk-proj-NEW-KEY"
```

## Scaling

### Increase Memory/Timeout
Edit `template.yaml`:
```yaml
Properties:
  MemorySize: 2048  # Default 1024
  Timeout: 600      # Default 300
```

Then redeploy:
```bash
sam build && sam deploy --stack-name resume-grader-httpapi
```

## Cost Estimation

### AWS Lambda
- Free tier: 1M requests, 400k GB-seconds/month
- Typical usage: 0.25 GB-seconds per resume
- Cost: ~$0.0000016 per resume

### OpenAI API
- gpt-4o pricing: ~$0.015 per 1k input tokens
- Typical resume: 2-5k tokens
- Cost: ~$0.03-0.075 per resume

### Estimated Monthly (100 resumes/month)
- AWS: <$1
- OpenAI: $3-8
- **Total: ~$4-9/month**

## Troubleshooting

### Deployment Fails with "Stack already exists"

```bash
# Delete the old stack
aws cloudformation delete-stack --stack-name resume-grader-httpapi

# Wait for deletion
aws cloudformation wait stack-delete-complete --stack-name resume-grader-httpapi

# Retry deployment
sam deploy --stack-name resume-grader-httpapi \
  --parameter-overrides OpenAIApiKey="sk-proj-YOUR-KEY"
```

### Lambda Function Timeout

If grading takes too long (>300s):
1. Increase timeout in template.yaml (max 900s)
2. Process resumes in batches
3. Use async processing

### API Returns 403

Check:
1. OpenAI API key is valid
2. Account has paid plan (not free trial)
3. gpt-4o model access is enabled
4. No usage limits exceeded

Run: `python3 test_openai.py`

### High AWS Bills

Check:
1. Lambda invocation count
2. Storage usage (should be minimal)
3. Data transfer costs
4. Consider setting up CloudWatch alarms

## Rollback

If deployment breaks your app:

```bash
# Rollback to previous version
aws cloudformation cancel-update-stack \
  --stack-name resume-grader-httpapi
```

## Cleanup

To delete everything and stop costs:

```bash
# Delete stack
aws cloudformation delete-stack --stack-name resume-grader-httpapi

# Wait for completion
aws cloudformation wait stack-delete-complete \
  --stack-name resume-grader-httpapi
```

This will:
- Delete Lambda function
- Delete API Gateway
- Delete CloudWatch logs
- Stop all AWS charges

Note: OpenAI API charges are billed separately by OpenAI.

## Next Steps

1. Share the API endpoint with your team
2. Customize job description/rubric for your needs
3. Test with real resumes
4. Set up CloudWatch alarms for errors
5. Monitor costs and usage

## Support

- AWS: https://console.aws.amazon.com/
- OpenAI: https://platform.openai.com/account
- SAM: https://aws.amazon.com/serverless/sam/
