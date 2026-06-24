"""LLM prompt builder service."""

from services.logger import get_logger

log = get_logger("prompbuilder")


def build_prompt(resume_text, jd_text):
    log.debug("Building prompt (resume=%d chars, jd=%d chars)", len(resume_text), len(jd_text))
    prompt = f"""
you are an expert ATS (Application Tracking System ) and resume reviewer . 

your task is to compare the candidate's resume with the job description . 

Analyze the resume and provide : 
1. match score (0-100)
2. Matching skills 
3. missing skills 
4. strengths 
5. weaknesses 
6. recommendations to improve the resume to match the job description
7. extract candidate's full name 
8. extract candidate's current role or more relevant proffessional role 

JOB DESCRIPTION :
{jd_text}
CANDIDATE RESUME :
{resume_text}

OUTPUT FORMAT :
return ONLY valid JSON .
do not include explainations . 
do not use markdown . 
do not use code blocks .

EXAMPLE OUTPUT STRUCTURE :
{{
    "candidate_name": "",
    "candidate_role": "",
    "match_score": 0,
    "matching_skills": [],
    "missing_skills": [],
    "strengths": [],
    "weaknesses": [],
    "recommendations": []
}}
"""
    result = prompt.strip()
    log.info("Prompt built: %d chars", len(result))
    return result