# Resume Grader - Getting Started

## Overview
Resume Grader is a serverless Flask application that uses OpenAI's GPT-4o model to automatically score and grade resumes against a customizable job description and rubric.

## Features
- Upload PDF, DOCX, and TXT resumes
- Customize job description and scoring rubric
- Automatic resume scoring using GPT-4o
- Export results to Excel spreadsheet
- Modern, responsive web UI
- Serverless deployment on AWS Lambda + API Gateway

## Prerequisites
- Python 3.11+
- AWS Account with SAM CLI installed
- OpenAI API key with gpt-4o access (paid plan required)

## Local Setup

### 1. Setup Environment
```bash
cd /Users/suyashshukla/PyCharmMiscProject
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure API Key
Create `.env` file:
```bash
echo "OPENAI_API_KEY=sk-proj-YOUR-KEY" > .env
```

### 3. Run Locally
```bash
python3 app.py
```
Visit `http://localhost:5000`

## Deploy to AWS Lambda

```bash
sam build
sam deploy --stack-name resume-grader-httpapi \
  --parameter-overrides OpenAIApiKey="sk-proj-YOUR-KEY"
```

## Usage

1. Access the web UI
2. (Optional) Click "⚙️ Configure JD & Rubric" to customize scoring
3. Upload resumes (PDF, DOCX, or TXT)
4. Click "Grade Resumes"
5. Download results when complete

## Architecture

- **Frontend**: Modern HTML/CSS/JavaScript UI
- **Backend**: Flask microframework
- **Serverless**: AWS Lambda + API Gateway
- **AI Engine**: OpenAI GPT-4o
- **File Processing**: pypdfium2, python-docx
- **Output**: Excel spreadsheet via openpyxl & pandas

## Troubleshooting

**API Key not configured**: Verify `.env` file and run `echo $OPENAI_API_KEY`

**403 Unauthorized**: Check OpenAI account has gpt-4o access and active billing

**Download not working**: Clear cache, try different browser, check F12 console

**Lambda deployment fails**: Delete stack and redeploy
```bash
aws cloudformation delete-stack --stack-name resume-grader-httpapi
aws cloudformation wait stack-delete-complete --stack-name resume-grader-httpapi
sam deploy --stack-name resume-grader-httpapi --parameter-overrides OpenAIApiKey="..."
```

## File Types Supported
- PDF (via pypdfium2)
- DOCX (via python-docx)  
- TXT (plain text)

## Performance
- Resume extraction: 1-2 seconds
- GPT-4o scoring: 5-10 seconds per resume
- Lambda timeout: 300 seconds
- Max file size: 50 MB
