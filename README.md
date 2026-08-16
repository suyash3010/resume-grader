# Resume Grader - AWS Deployment

A web application that grades resumes against a job description using OpenAI's GPT-4o model. Deploy it to AWS Lambda + API Gateway in minutes.

## What's Included

- **Web UI**: Beautiful drag-and-drop interface for uploading resumes
- **Resume Processing**: Supports PDF, DOCX, and TXT files
- **AI-Powered Scoring**: Uses OpenAI GPT-4o to score resumes based on a customizable rubric
- **Excel Export**: Downloads ranked shortlist as an Excel file
- **Serverless Deployment**: Runs on AWS Lambda (only pay for what you use)

## Features

✅ Upload multiple resumes at once  
✅ AI-powered candidate scoring  
✅ Ranked shortlist with detailed analysis  
✅ Mandatory requirement gates (e.g., "must have Playwright experience")  
✅ Extract matched and missing skills  
✅ Identify red flags  
✅ Download results as Excel file  
✅ Low-cost serverless architecture  

## Quick Start (5 minutes)

### Prerequisites
- AWS account with CLI configured
- OpenAI API key (from https://platform.openai.com/api-keys)

### Option 1: Zappa Deployment (Recommended)

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Create S3 bucket for Zappa
aws s3api create-bucket --bucket zappa-deployments-resume-grader --region us-east-1

# 3. Set OpenAI API key
export OPENAI_API_KEY="sk-..."

# 4. Deploy
zappa deploy dev

# 5. You're done! Check the output for your API URL
```

Visit your API Gateway URL in the browser to use the app!

### Option 2: AWS SAM Deployment

```bash
# 1. Install SAM CLI
brew install aws-sam-cli

# 2. Build
sam build

# 3. Deploy with guided setup
sam deploy --guided
# - Stack Name: resume-grader
# - Region: us-east-1
# - Parameter OpenAIApiKey: sk-...

# 4. Get your URL from CloudFormation outputs
```

## Testing Locally

Test before deploying:

```bash
# 1. Create virtual environment
python3 -m venv venv
source venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set API key
export OPENAI_API_KEY="sk-..."

# 4. Run
python app.py

# 5. Open http://localhost:5000
```

See `LOCAL_TESTING.md` for more details.

## File Structure

```
.
├── app.py                    # Flask web application
├── requirements.txt          # Python dependencies
├── zappa_settings.json       # Zappa deployment config
├── template.yaml             # AWS SAM template
├── lambda_handler.py         # AWS Lambda entry point
├── QUICK_START.md            # Fast deployment guide
├── DEPLOYMENT_GUIDE.md       # Detailed deployment (SAM)
├── LOCAL_TESTING.md          # Local testing guide
└── README.md                 # This file
```

## Architecture

```
Browser
   ↓
API Gateway (AWS)
   ↓
Lambda Function (AWS)
   ↓
OpenAI API
   ↓
Excel File (downloaded)
```

**Cost**: ~$1-20/month for low usage (with free tier credits)

## Configuration

### Customizing the Job Description and Rubric

Edit these in `app.py`:
- `JOB_DESCRIPTION` - The role description for grading
- `RUBRIC` - The scoring rubric with point values
- `PROMPT_TEMPLATE` - The evaluation prompt sent to OpenAI

### Changing AWS Region

Zappa: Edit `zappa_settings.json` → `"aws_region"`
SAM: Run `sam deploy --guided` and select a different region

### Adjusting Memory/Timeout

Zappa: Edit `zappa_settings.json` → `"memory_size"` and `"timeout"`
SAM: Edit `template.yaml` → `MemorySize` and `Timeout`

## Monitoring

### View Logs

```bash
# Zappa
zappa tail dev

# SAM
sam logs -n ResumeGraderFunction --stack-name resume-grader -t
```

### Check Health
```bash
curl https://your-api-url/health
```

## Troubleshooting

### "OPENAI_API_KEY not configured"
Make sure the API key was set during deployment and saved to configuration.

### Timeout errors
Processing takes time. Increase `timeout` in config or process fewer resumes at once.

### Out of memory
Increase `memory_size` in config (costs slightly more).

### Resume extraction fails
Make sure files are readable PDFs/DOCX. Scanned images won't work—needs searchable text.

See `QUICK_START.md` for more troubleshooting.

## Cleanup

Remove all AWS resources and stop charges:

```bash
# Zappa
zappa undeploy dev --remove-logs

# SAM
aws cloudformation delete-stack --stack-name resume-grader
```

## Cost Breakdown

| Service | Free Tier | Cost |
|---------|-----------|------|
| Lambda | 1M requests/month | $0.20/month typical |
| API Gateway | 1M requests/month | $0.35/month typical |
| OpenAI API | — | $0.001-0.01 per resume |
| **Total** | — | **~$1-20/month** |

Your free tier covers most of this for the first year.

## Next Steps

1. ✅ Deploy using QUICK_START.md
2. ✅ Test with sample resumes
3. ✅ Share the URL with your team
4. ✅ Customize JD and rubric as needed
5. ✅ Monitor costs in AWS Console

## Support

- Check logs: `zappa tail dev` or AWS CloudWatch
- Debug locally: Run `python app.py` and test at `http://localhost:5000`
- AWS Docs: https://docs.aws.amazon.com/lambda/
- OpenAI Docs: https://platform.openai.com/docs/

## License

This project is provided as-is for your use.

---

**Ready to deploy?** Start with `QUICK_START.md` →
