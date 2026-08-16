"""
Resume Scorer against JD (Senior QA Engineer) -- OpenAI version
-----------------------------------------------------------------
Reads all .txt resumes from a folder, sends each one + the JD + a weighted
rubric to an OpenAI model, and outputs a ranked shortlist as a CSV/Excel file.

Setup:
    pip install openai pandas openpyxl

    Set your API key as an environment variable before running:
        export OPENAI_API_KEY="your-key-here"      (Mac/Linux)
        set OPENAI_API_KEY=your-key-here            (Windows cmd)

Usage:
    python score_resumes_openai.py --input_dir ./resume_texts --output_file ./shortlist.xlsx
"""

import argparse
import json
import os
import sys
import time

import pandas as pd
from openai import OpenAI

MODEL = "gpt-4o"

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


def score_resume(client: OpenAI, resume_text: str, filename: str) -> dict:
    prompt = PROMPT_TEMPLATE.format(jd=JOB_DESCRIPTION, rubric=RUBRIC, resume_text=resume_text)

    response = client.chat.completions.create(
        model=MODEL,
        max_tokens=1000,
        response_format={"type": "json_object"},
        messages=[{"role": "user", "content": prompt}],
    )

    raw_text = response.choices[0].message.content.strip()

    # Strip markdown fences just in case
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


def process_folder(input_dir: str, output_file: str) -> None:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("ERROR: Set the OPENAI_API_KEY environment variable before running this script.")
        sys.exit(1)

    client = OpenAI(api_key=api_key)

    txt_files = [f for f in os.listdir(input_dir) if f.lower().endswith(".txt")]
    if not txt_files:
        print(f"No .txt files found in {input_dir}")
        return

    print(f"Scoring {len(txt_files)} resume(s) against the JD...\n")

    results = []
    for i, filename in enumerate(txt_files, start=1):
        filepath = os.path.join(input_dir, filename)
        with open(filepath, "r", encoding="utf-8") as f:
            resume_text = f.read()

        if not resume_text.strip():
            print(f"[{i}/{len(txt_files)}] SKIPPED (empty file): {filename}")
            continue

        try:
            result = score_resume(client, resume_text, filename)
            score_display = result.get("total_score", "N/A")
            print(f"[{i}/{len(txt_files)}] {filename} -> score: {score_display}")
            results.append(result)
        except Exception as e:
            print(f"[{i}/{len(txt_files)}] FAILED: {filename}: {e}")

        time.sleep(0.5)  # small pause to avoid rate limit bursts

    if not results:
        print("No results generated.")
        return

    df = pd.DataFrame(results)

    # Convert list fields to readable comma-separated strings for spreadsheet display
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
        "candidate_name", "meets_mandatory_requirement", "total_score", "years_experience_estimate",
        "matched_skills", "missing_skills", "red_flags", "summary", "source_file",
    ]
    df = df[[c for c in column_order if c in df.columns]]

    if output_file.lower().endswith(".xlsx"):
        df.to_excel(output_file, index=False)
    else:
        df.to_csv(output_file, index=False)

    print(f"\nDone. Ranked shortlist saved to: {os.path.abspath(output_file)}")


def main():
    parser = argparse.ArgumentParser(description="Score resumes against a JD using OpenAI.")
    parser.add_argument("--input_dir", required=True, help="Folder containing resume .txt files")
    parser.add_argument("--output_file", default="./shortlist.xlsx", help="Output file (.xlsx or .csv)")
    args = parser.parse_args()

    if not os.path.isdir(args.input_dir):
        print(f"Input directory not found: {args.input_dir}")
        sys.exit(1)

    process_folder(args.input_dir, args.output_file)


if __name__ == "__main__":
    main()