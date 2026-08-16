# Local Testing Guide

Test the Resume Grader app locally before deploying to AWS.

## Setup

### 1. Create a virtual environment
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Set your OpenAI API key
```bash
export OPENAI_API_KEY="sk-..."  # Your OpenAI API key
```

On Windows (Command Prompt):
```bash
set OPENAI_API_KEY=sk-...
```

## Run the app

```bash
python app.py
```

You should see:
```
 * Running on http://127.0.0.1:5000
```

## Test in browser

1. Open http://localhost:5000 in your browser
2. Click the upload area and select some resume files (.pdf, .docx, or .txt)
3. Click "Grade Resumes"
4. Wait for processing (should take 5-30 seconds per resume)
5. Click "Download Results" to get the Excel file

## Test with cURL (API testing)

### Check health
```bash
curl http://localhost:5000/health
```

### Upload and grade resumes
```bash
curl -X POST http://localhost:5000/grade \
  -F "files=@resume1.pdf" \
  -F "files=@resume2.docx"
```

## Sample Resume for Testing

If you don't have resumes handy, create a test file:

**test_resume.txt:**
```
John Doe
Senior QA Engineer

Experience:
- 8 years in software testing and QA
- Expert in Playwright automation framework
- Advanced SQL and PostgreSQL experience
- CI/CD pipeline integration with GitHub Actions
- Performance testing using k6
- Security testing with OWASP ZAP
- Led QA team of 5 engineers
- ISTQB Certified

Skills:
- Playwright (expert)
- Selenium (advanced)
- Cypress (intermediate)
- Python, JavaScript
- Git, Docker
- Jira, Confluence
```

## Troubleshooting

### "OPENAI_API_KEY not found"
Make sure you exported the API key:
```bash
echo $OPENAI_API_KEY
```

Should print your key, not blank.

### ModuleNotFoundError
Make sure virtual environment is activated:
```bash
source venv/bin/activate
```

### Port 5000 already in use
```bash
python app.py --port 8000
```

Then visit http://localhost:8000

### Resume processing fails
- Check that your OpenAI API key is valid
- Check your OpenAI account has credits
- Check internet connection
- Look at console output for error messages

## Performance Tips

- Test with 2-3 resumes first
- Each resume takes ~3-10 seconds to grade
- Processing time depends on resume length and OpenAI API response time

## Next: Deploy to AWS

Once testing looks good, follow the deployment guide:
- **Zappa**: See `QUICK_START.md` Option 1
- **SAM**: See `QUICK_START.md` Option 2 or `DEPLOYMENT_GUIDE.md`
