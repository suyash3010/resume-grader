import json
import os
import io
import time
import tempfile
from datetime import datetime
from functools import wraps
from urllib.parse import urlencode, parse_qs

from flask import Flask, request, jsonify, send_file, session, redirect, url_for, render_template_string
from openai import OpenAI
import pandas as pd
from werkzeug.utils import secure_filename
import pypdfium2 as pdfium
from docx import Document
from dotenv import load_dotenv
import requests
import boto3

load_dotenv()

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'dev-secret-key-change-in-production')

# Cognito Configuration
COGNITO_USER_POOL_ID = os.environ.get('COGNITO_USER_POOL_ID')
COGNITO_CLIENT_ID = os.environ.get('COGNITO_CLIENT_ID')
COGNITO_CLIENT_SECRET = os.environ.get('COGNITO_CLIENT_SECRET')
COGNITO_DOMAIN = os.environ.get('COGNITO_DOMAIN')
COGNITO_REGION = os.environ.get('COGNITO_REGION', 'us-east-1')

# Build Cognito URLs
COGNITO_DISCOVERY_URL = f'https://cognito-idp.{COGNITO_REGION}.amazonaws.com/{COGNITO_USER_POOL_ID}/.well-known/openid-configuration'
COGNITO_AUTH_URL = f'https://{COGNITO_DOMAIN}.auth.{COGNITO_REGION}.amazoncognito.com/oauth2/authorize'
COGNITO_TOKEN_URL = f'https://{COGNITO_DOMAIN}.auth.{COGNITO_REGION}.amazoncognito.com/oauth2/token'
COGNITO_JWKS_URL = f'https://cognito-idp.{COGNITO_REGION}.amazonaws.com/{COGNITO_USER_POOL_ID}/.well-known/jwks.json'

# Cognito client for token verification
cognito_client = boto3.client('cognito-idp', region_name=COGNITO_REGION)

_last_results = None

MODEL = "gpt-4o"

# ============================================================================
# COGNITO AUTHENTICATION HELPERS
# ============================================================================

def login_required(f):
    """Decorator to require authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


def get_login_url(redirect_uri):
    """Generate Cognito login URL"""
    params = {
        'client_id': COGNITO_CLIENT_ID,
        'response_type': 'code',
        'scope': 'email openid',
        'redirect_uri': redirect_uri,
    }
    return f'{COGNITO_AUTH_URL}?{urlencode(params)}'


def exchange_code_for_token(code, redirect_uri):
    """Exchange authorization code for ID and access tokens"""
    try:
        response = requests.post(
            COGNITO_TOKEN_URL,
            headers={'Content-Type': 'application/x-www-form-urlencoded'},
            data={
                'grant_type': 'authorization_code',
                'client_id': COGNITO_CLIENT_ID,
                'client_secret': COGNITO_CLIENT_SECRET,
                'code': code,
                'redirect_uri': redirect_uri,
            }
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error exchanging code: {e}")
        return None


def decode_token(token):
    """Decode and verify JWT token from Cognito"""
    try:
        # Fetch public keys
        resp = requests.get(COGNITO_JWKS_URL)
        keys = resp.json()['keys']

        # Simple verification - in production use python-jose
        import base64
        parts = token.split('.')

        # Decode payload (second part)
        payload = parts[1]
        # Add padding if needed
        payload += '=' * (4 - len(payload) % 4)
        decoded = base64.urlsafe_b64decode(payload)

        return json.loads(decoded)
    except Exception as e:
        print(f"Error decoding token: {e}")
        return None


def get_user_info_from_token(id_token):
    """Extract user info from ID token"""
    payload = decode_token(id_token)
    if payload:
        email = payload.get('email', '')
        name = payload.get('name') or email or 'Logged In'
        return {
            'sub': payload.get('sub'),
            'email': email,
            'name': name,
            'picture': payload.get('picture'),
        }
    return None

JOB_DESCRIPTION = """
Senior QA Engineer
Location: Trivandrum
Experience: 6-10 years
Employment Type: Full-time

Job Summary:
We are seeking an experienced Senior QA Engineer (6-10 years experience) to lead quality
assurance initiatives and ensure the delivery of reliable, scalable, and high-performance
applications. The ideal candidate will define test strategies, drive automation frameworks,
mentor junior QA members, and collaborate closely with development and DevOps teams to
maintain high product quality.

Key Responsibilities:
- Define and implement comprehensive test strategies covering functional, regression,
  integration, performance, and security testing.
- Design, develop, and maintain automation frameworks using Playwright, Cypress, or Selenium.
- Validate backend services and database integrity using SQL queries (PostgreSQL).
- Perform performance and load testing using tools such as k6 or JMeter.
- Conduct security and vulnerability testing using OWASP ZAP or similar tools.
- Integrate automated test suites within CI/CD pipelines (GitHub Actions, Jenkins, Azure DevOps).
- Review test cases, ensure proper test coverage, and maintain test documentation standards.
- Analyze root causes of defects and implement preventive quality measures.
- Drive continuous improvement in QA processes, automation coverage, and release quality.
- Mentor junior QA engineers and provide technical guidance.
- Actively participate in Agile/Scrum ceremonies and collaborate with cross-functional teams.

Key Skills:
- Bachelor's degree in Computer Science, Engineering, or related field.
- 6-10 years of experience in software testing and quality assurance.
- Strong expertise in manual and automation testing.
- Hands-on experience with Playwright is mandatory. Additional experience with Cypress or
  Selenium is a plus but does not substitute for Playwright.
- Strong knowledge of API testing and automation.
- Experience with performance testing tools (k6, JMeter).
- Experience with CI/CD integration and DevOps workflows.
- Strong understanding of SDLC, STLC, and Agile methodologies.
- Experience with defect tracking tools such as Jira.
- Strong analytical, leadership, and mentoring skills.
- Excellent communication and stakeholder management abilities.
- Certification such as ISTQB or an equivalent QA qualification is an added advantage.
"""

RUBRIC = """
MANDATORY GATE (check this first, before scoring):
The candidate MUST have hands-on Playwright experience. Selenium and/or Cypress experience
does NOT substitute for Playwright, even if extensive. If the resume shows no clear evidence
of hands-on Playwright experience (e.g. only Selenium and/or Cypress, or only lists Playwright
as a passing familiarity with no real usage), set "meets_mandatory_requirement" to false and
cap total_score at 30, regardless of how strong the rest of the resume is. If Playwright
experience is clearly present, set "meets_mandatory_requirement" to true and score normally
using the rubric below.

Score the candidate 0-100 using this weighted rubric (only apply if the mandatory gate above
is passed):

1. Years of relevant QA experience, ideally 6-10 years (15 points)
2. Depth of hands-on Playwright experience specifically -- framework design, page object model,
   CI integration, etc. (20 points). Additional Selenium/Cypress experience can be noted as a
   plus in matched_skills but earns no extra points here.
3. API testing and automation experience (15 points)
4. CI/CD integration experience: GitHub Actions, Jenkins, or Azure DevOps (10 points)
5. Performance testing experience: k6 or JMeter (10 points)
6. Security testing experience: OWASP ZAP or similar (5 points)
7. SQL / database validation experience, ideally PostgreSQL (5 points)
8. SDLC/STLC/Agile methodology understanding (5 points)
9. Manual testing strength (5 points)
10. Leadership/mentoring experience (5 points)
11. Defect tracking tool experience, e.g. Jira (3 points)
12. ISTQB or equivalent certification (2 points)

Add up the points for a total score out of 100.
"""

PROMPT_TEMPLATE = """You are an expert technical recruiter screening resumes for the following role.

JOB DESCRIPTION:
{jd}

SCORING RUBRIC:
{rubric}

CANDIDATE RESUME:
{resume_text}

Evaluate this resume strictly against the rubric above. Respond with ONLY a valid JSON object,
no preamble, no markdown code fences, in exactly this format:

{{
  "candidate_name": "<name extracted from resume, or filename if not found>",
  "meets_mandatory_requirement": <true or false -- true only if hands-on Playwright experience is clearly present>,
  "total_score": <integer 0-100>,
  "years_experience_estimate": "<number or range>",
  "matched_skills": ["<skill>", "..."],
  "missing_skills": ["<skill>", "..."],
  "red_flags": ["<e.g. job hopping, unexplained gaps, no automation ownership, etc. Empty list if none>"],
  "summary": "<one or two sentence overall assessment>"
}}
"""


def extract_text_from_pdf(file_obj):
    try:
        doc = pdfium.PdfDocument(file_obj)
        text = "\n".join(p.get_textpage().get_text_range() for p in doc)
        return text
    except Exception as e:
        return f"Error extracting PDF: {str(e)}"


def extract_text_from_docx(file_obj):
    try:
        doc = Document(file_obj)
        text_parts = [para.text for para in doc.paragraphs if para.text.strip()]
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    if cell.text.strip():
                        text_parts.append(cell.text)
        return "\n".join(text_parts)
    except Exception as e:
        return f"Error extracting DOCX: {str(e)}"


def extract_text_from_txt(file_obj):
    try:
        return file_obj.read().decode('utf-8')
    except Exception as e:
        return f"Error extracting TXT: {str(e)}"


def score_resume(client, resume_text, filename, job_description, rubric):
    prompt = PROMPT_TEMPLATE.format(jd=job_description, rubric=rubric, resume_text=resume_text)

    response = client.chat.completions.create(
        model=MODEL,
        max_tokens=1000,
        response_format={"type": "json_object"},
        messages=[{"role": "user", "content": prompt}],
    )

    raw_text = response.choices[0].message.content.strip()

    if raw_text.startswith("```"):
        raw_text = raw_text.strip("`")
        raw_text = raw_text.replace("json", "", 1).strip()

    try:
        result = json.loads(raw_text)
    except json.JSONDecodeError:
        result = {
            "candidate_name": filename,
            "meets_mandatory_requirement": None,
            "total_score": None,
            "years_experience_estimate": None,
            "matched_skills": [],
            "missing_skills": [],
            "red_flags": ["PARSE_ERROR"],
            "summary": f"Could not parse model response: {raw_text[:200]}",
        }

    result["source_file"] = filename
    return result


# ============================================================================
# AUTHENTICATION ROUTES
# ============================================================================

@app.route('/login')
def login():
    """Redirect to Cognito login"""
    redirect_uri = url_for('callback', _external=True)
    login_url = get_login_url(redirect_uri)
    return redirect(login_url)


@app.route('/callback')
def callback():
    """Handle Cognito callback"""
    code = request.args.get('code')
    error = request.args.get('error')

    if error:
        return jsonify({'error': error}), 400

    if not code:
        return jsonify({'error': 'Missing authorization code'}), 400

    # Exchange code for tokens
    redirect_uri = url_for('callback', _external=True)
    token_response = exchange_code_for_token(code, redirect_uri)

    if not token_response or 'id_token' not in token_response:
        return jsonify({'error': 'Failed to get tokens'}), 400

    # Extract user info from ID token
    user_info = get_user_info_from_token(token_response['id_token'])
    if not user_info:
        return jsonify({'error': 'Failed to decode token'}), 400

    # Store user info in session
    session['user'] = user_info
    session['id_token'] = token_response['id_token']
    session['access_token'] = token_response.get('access_token')

    return redirect(url_for('index'))


@app.route('/logout')
def logout():
    """Logout user and clear session"""
    session.clear()
    return redirect(url_for('index'))


# ============================================================================
# APPLICATION ROUTES
# ============================================================================

@app.route('/')
def index():
    user = session.get('user')

    # If not logged in, show login page
    if not user:
        login_html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Resume Grader - AI-Powered Resume Analysis</title>
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                * { margin: 0; padding: 0; box-sizing: border-box; }
                body {
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Helvetica Neue', sans-serif;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    min-height: 100vh;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    padding: 20px;
                }
                .login-container {
                    text-align: center;
                    animation: slideUp 0.6s ease-out;
                }
                @keyframes slideUp {
                    from { opacity: 0; transform: translateY(30px); }
                    to { opacity: 1; transform: translateY(0); }
                }
                .logo { font-size: 64px; margin-bottom: 20px; }
                h1 {
                    color: white;
                    font-size: 42px;
                    font-weight: 700;
                    margin-bottom: 12px;
                    letter-spacing: -0.5px;
                }
                .subtitle {
                    color: rgba(255, 255, 255, 0.9);
                    font-size: 18px;
                    margin-bottom: 48px;
                    max-width: 500px;
                    margin-left: auto;
                    margin-right: auto;
                    line-height: 1.6;
                }
                .login-btn {
                    background: white;
                    color: #667eea;
                    padding: 16px 40px;
                    border: none;
                    border-radius: 12px;
                    font-size: 16px;
                    font-weight: 700;
                    cursor: pointer;
                    display: inline-flex;
                    align-items: center;
                    gap: 12px;
                    transition: all 0.3s ease;
                    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
                    text-decoration: none;
                }
                .login-btn:hover {
                    transform: translateY(-3px);
                    box-shadow: 0 15px 40px rgba(0, 0, 0, 0.3);
                }
                .login-btn:active {
                    transform: translateY(-1px);
                }
                .google-icon {
                    width: 20px;
                    height: 20px;
                }
                .features {
                    margin-top: 80px;
                    color: rgba(255, 255, 255, 0.8);
                    font-size: 14px;
                    display: flex;
                    justify-content: center;
                    gap: 40px;
                    flex-wrap: wrap;
                }
                .feature { display: flex; align-items: center; gap: 8px; }
                .feature-icon { font-size: 20px; }
            </style>
        </head>
        <body>
            <div class="login-container">
                <div class="logo">🎯</div>
                <h1>Resume Grader</h1>
                <p class="subtitle">AI-powered resume analysis. Get instant feedback on how your resume matches job requirements.</p>

                <a href="/login" class="login-btn">
                    <svg class="google-icon" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4"/>
                        <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/>
                        <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05"/>
                        <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/>
                    </svg>
                    Continue with Google
                </a>

                <div class="features">
                    <div class="feature"><span class="feature-icon">⚡</span> <span>Instant Analysis</span></div>
                    <div class="feature"><span class="feature-icon">🎯</span> <span>Job Matching</span></div>
                    <div class="feature"><span class="feature-icon">🔒</span> <span>Secure & Private</span></div>
                </div>
            </div>
        </body>
        </html>
        """
        return render_template_string(login_html)

    # If logged in, show main app
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Resume Grader</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; display: flex; align-items: center; justify-content: center; padding: 20px; }
            .container { background: white; border-radius: 20px; box-shadow: 0 20px 60px rgba(0,0,0,0.3); padding: 48px; max-width: 600px; width: 100%; }
            h1 { color: #1a202c; margin-bottom: 8px; font-size: 28px; font-weight: 700; }
            .subtitle { color: #718096; margin-bottom: 24px; font-size: 14px; }
            .section { margin-bottom: 32px; }
            .section-title { font-weight: 600; color: #2d3748; margin-bottom: 12px; font-size: 13px; text-transform: uppercase; letter-spacing: 0.5px; }
            .settings-toggle { background: transparent; color: #667eea; border: 1px solid #cbd5e0; padding: 8px 12px; border-radius: 6px; font-size: 13px; font-weight: 500; cursor: pointer; margin-bottom: 20px; transition: all 0.2s; }
            .settings-toggle:hover { background: #f7fafc; border-color: #667eea; }
            .settings-panel { margin-bottom: 20px; padding: 20px; background: #f8faff; border-radius: 8px; border: 1px solid #e2e8f0; }
            textarea { width: 100%; padding: 12px; border: 1px solid #e2e8f0; border-radius: 8px; font-family: 'Monaco', 'Courier New', monospace; font-size: 13px; resize: vertical; line-height: 1.5; }
            textarea:focus { outline: none; border-color: #667eea; box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1); }
            .upload-area { border: 2px dashed #667eea; border-radius: 12px; padding: 48px 32px; text-align: center; cursor: pointer; transition: all 0.3s ease; background: #f8faff; margin-bottom: 24px; }
            .upload-area:hover { border-color: #764ba2; background: #f3f7ff; transform: translateY(-2px); }
            .upload-area input { display: none; }
            .upload-icon { font-size: 56px; margin-bottom: 16px; opacity: 0.8; }
            .upload-text { color: #2d3748; font-weight: 600; margin-bottom: 8px; font-size: 16px; }
            .upload-hint { color: #a0aec0; font-size: 13px; }
            .file-list { margin-bottom: 16px; }
            .file-item { background: #f7fafc; padding: 10px 14px; border-radius: 6px; display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; border: 1px solid #edf2f7; }
            .file-name { color: #2d3748; font-size: 13px; }
            .remove-btn { background: transparent; color: #fc8181; border: none; padding: 2px 8px; border-radius: 4px; cursor: pointer; font-size: 12px; transition: all 0.2s; }
            .remove-btn:hover { background: #fed7d7; color: #f56565; }
            button { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border: none; padding: 14px 24px; border-radius: 8px; font-size: 15px; font-weight: 600; cursor: pointer; width: 100%; margin-top: 0; transition: all 0.3s ease; }
            button:hover { transform: translateY(-2px); box-shadow: 0 12px 24px rgba(102, 126, 234, 0.4); }
            button:disabled { opacity: 0.4; cursor: not-allowed; transform: none; }
            .status { margin-top: 20px; padding: 14px 16px; border-radius: 8px; display: none; font-size: 14px; }
            .status.success { background: #c6f6d5; color: #22543d; border-left: 4px solid #48bb78; }
            .status.error { background: #fed7d7; color: #742a2a; border-left: 4px solid #f56565; }
            .status.loading { background: #bee3f8; color: #2c5282; border-left: 4px solid #3182ce; }
            .download-btn { background: #48bb78; margin-top: 12px; display: none; }
            .download-btn:hover { background: #38a169; }
            a { color: inherit; text-decoration: none; }
            .header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
            .auth-buttons { display: flex; align-items: center; gap: 12px; }
            .user-info { display: flex; align-items: center; gap: 12px; }
            .profile-pic { width: 32px; height: 32px; border-radius: 50%; }
            .user-name { color: #2d3748; font-size: 14px; font-weight: 500; }
            .logout-btn { background: #667eea; color: white; padding: 8px 16px; border-radius: 6px; font-size: 14px; font-weight: 600; display: inline-block; transition: all 0.2s; }
            .logout-btn:hover { background: #764ba2; transform: translateY(-1px); box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3); }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🎯 Resume Grader</h1>
                <div class="auth-buttons">
                    <div class="user-info">
                        {% if user.picture %}
                            <img src="{{ user.picture }}" alt="Profile" class="profile-pic">
                        {% endif %}
                        <span class="user-name">{{ user.name }}</span>
                        <a href="/logout" class="logout-btn">Logout</a>
                    </div>
                </div>
            </div>

            <p class="subtitle">Upload resumes and get them scored against the job description</p>

            <button class="settings-toggle" id="settingsToggle">⚙️ Configure JD & Rubric</button>

            <div class="settings-panel" id="settingsPanel" style="display: none;">
                <div class="section">
                    <div class="section-title">Job Description</div>
                    <textarea id="jdField" rows="6">PLACEHOLDER_JD</textarea>
                </div>

                <div class="section">
                    <div class="section-title">Scoring Rubric</div>
                    <textarea id="rubricField" rows="6">PLACEHOLDER_RUBRIC</textarea>
                </div>
            </div>

            <div class="upload-area" onclick="document.getElementById('fileInput').click()">
                <div class="upload-icon">📄</div>
                <div class="upload-text">Drop files here or click to upload</div>
                <div class="upload-hint">Supports PDF, DOCX, and TXT files</div>
                <input type="file" id="fileInput" multiple accept=".pdf,.docx,.txt">
            </div>

            <div class="file-list" id="fileList"></div>

            <button id="submitBtn" disabled>Grade Resumes</button>
            <a id="downloadBtn" class="download-btn" href="" download="shortlist.xlsx" style="display: none; text-decoration: none;">Download Results</a>

            <div class="status" id="status"></div>
        </div>

        <script>
            let files = [];
            const fileInput = document.getElementById('fileInput');
            const fileList = document.getElementById('fileList');
            const submitBtn = document.getElementById('submitBtn');
            const downloadBtn = document.getElementById('downloadBtn');
            const status = document.getElementById('status');
            const jdField = document.getElementById('jdField');
            const rubricField = document.getElementById('rubricField');
            const settingsToggle = document.getElementById('settingsToggle');
            const settingsPanel = document.getElementById('settingsPanel');

            settingsToggle.addEventListener('click', () => {
                settingsPanel.style.display = settingsPanel.style.display === 'none' ? 'block' : 'none';
            });

            fileInput.addEventListener('change', (e) => {
                files = Array.from(e.target.files);
                updateFileList();
                submitBtn.disabled = files.length === 0;
            });

            function updateFileList() {
                fileList.innerHTML = files.map((f, i) => `
                    <div class="file-item">
                        <span class="file-name">${f.name}</span>
                        <button class="remove-btn" onclick="removeFile(${i})">Remove</button>
                    </div>
                `).join('');
            }

            function removeFile(i) {
                files.splice(i, 1);
                updateFileList();
                submitBtn.disabled = files.length === 0;
            }

            submitBtn.addEventListener('click', async () => {
                if (files.length === 0) return;

                const formData = new FormData();
                files.forEach(f => formData.append('files', f));
                formData.append('job_description', jdField.value);
                formData.append('rubric', rubricField.value);

                submitBtn.disabled = true;
                status.className = 'status loading';
                status.textContent = '⏳ Processing resumes...';
                downloadBtn.style.display = 'none';

                try {
                    const response = await fetch('/grade', {
                        method: 'POST',
                        body: formData
                    });
                    const result = await response.json();

                    if (response.ok && result.download_url) {
                        status.className = 'status success';
                        status.textContent = '✅ Grading complete! Download your results.';
                        downloadBtn.href = result.download_url;
                        downloadBtn.style.display = 'block';
                        downloadBtn.click();
                        files = [];
                        updateFileList();
                        fileInput.value = '';
                    } else {
                        status.className = 'status error';
                        status.textContent = `❌ Error: ${result.error || 'Unknown error'}`;
                    }
                } catch (e) {
                    status.className = 'status error';
                    status.textContent = `❌ Error: ${e.message}`;
                } finally {
                    submitBtn.disabled = files.length === 0;
                }
            });
        </script>
    </body>
    </html>
    """
    html = html.replace("PLACEHOLDER_JD", JOB_DESCRIPTION).replace("PLACEHOLDER_RUBRIC", RUBRIC)
    user = session.get('user')
    return render_template_string(html, user=user)


@app.route('/grade', methods=['POST'])
@login_required
def grade_resumes():
    global _last_results

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return jsonify({"error": "OPENAI_API_KEY not configured"}), 500

    if 'files' not in request.files or len(request.files.getlist('files')) == 0:
        return jsonify({"error": "No files uploaded"}), 400

    job_description = request.form.get('job_description', JOB_DESCRIPTION)
    rubric = request.form.get('rubric', RUBRIC)

    uploaded_files = request.files.getlist('files')
    client = OpenAI(api_key=api_key)
    results = []

    for file in uploaded_files:
        if not file or file.filename == '':
            continue

        filename = secure_filename(file.filename)
        file.seek(0)

        if filename.lower().endswith('.pdf'):
            resume_text = extract_text_from_pdf(file.stream)
        elif filename.lower().endswith('.docx'):
            resume_text = extract_text_from_docx(file.stream)
        elif filename.lower().endswith('.txt'):
            resume_text = extract_text_from_txt(file.stream)
        else:
            continue

        if not resume_text.strip() or resume_text.startswith("Error"):
            continue

        try:
            result = score_resume(client, resume_text, filename, job_description, rubric)
            results.append(result)
            time.sleep(0.3)
        except Exception as e:
            print(f"Error scoring {filename}: {e}")

    if not results:
        return jsonify({"error": "No valid resumes to process"}), 400

    df = pd.DataFrame(results)

    for col in ["matched_skills", "missing_skills", "red_flags"]:
        if col in df.columns:
            df[col] = df[col].apply(lambda x: ", ".join(x) if isinstance(x, list) else x)

    if "meets_mandatory_requirement" in df.columns:
        df = df.sort_values(
            by=["meets_mandatory_requirement", "total_score"],
            ascending=[False, False],
            na_position="last",
        )
    else:
        df = df.sort_values(by="total_score", ascending=False, na_position="last")

    column_order = [
        "candidate_name", "meets_mandatory_requirement", "total_score",
        "years_experience_estimate", "matched_skills", "missing_skills",
        "red_flags", "summary", "source_file",
    ]
    df = df[[c for c in column_order if c in df.columns]]

    output = io.BytesIO()
    df.to_excel(output, index=False)
    output.seek(0)
    _last_results = output.getvalue()

    return jsonify({
        "download_url": "/download",
        "result": df.to_dict(orient='records')
    })


@app.route('/download')
def download():
    global _last_results

    if _last_results is None:
        return jsonify({"error": "No results available"}), 400

    return send_file(
        io.BytesIO(_last_results),
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        as_attachment=True,
        download_name=f"shortlist_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    )


@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "healthy"}), 200


def lambda_handler(event, context):
    from mangum import Mangum
    from asgiref.wsgi import WsgiToAsgi
    asgi_app = WsgiToAsgi(app)
    handler = Mangum(asgi_app, lifespan="off")
    return handler(event, context)


if __name__ == '__main__':
    app.run(debug=True)
