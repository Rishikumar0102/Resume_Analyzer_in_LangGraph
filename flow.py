from langgraph.graph import StateGraph
from typing import TypedDict
from openai import OpenAI
import os
import re

# Initialize client with direct API key
client = OpenAI(
    api_key="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",  # Replace with your actual Groq API key
    base_url="https://api.groq.com/openai/v1"
)

MODEL_NAME = "llama3-8b-8192"

class ResumeState(TypedDict):
    resume_text: str
    job_description: str
    feedback: str
    strengths: str
    areas_for_improvement: str

def parse_response(content: str) -> dict:
    """Improved parsing logic with multiple fallback patterns"""
    sections = {
        "feedback": "",
        "strengths": [],
        "areas_for_improvement": []
    }
    
    section_pattern = re.compile(
        r'### Feedback\n(.*?)(?=### Key Strengths|\Z)(.*?)'
        r'### Key Strengths\n(.*?)(?=### Areas for Improvement|\Z)(.*?)'
        r'### Areas for Improvement\n(.*)',
        re.DOTALL
    )
    
    match = section_pattern.search(content)
    if match:
        sections["feedback"] = match.group(1).strip()
        sections["strengths"] = [s.strip() for s in match.group(3).split('\n') if s.strip() and not s.startswith('-')]
        sections["areas_for_improvement"] = [s.strip() for s in match.group(5).split('\n') if s.strip() and not s.startswith('-')]
        return sections
    
    loose_pattern = re.compile(
        r'(Feedback|Overall Assessment)[:\n]*(.*?)(?=(Key Strengths|Strengths)|\Z)(.*?)'
        r'(Key Strengths|Strengths)[:\n]*(.*?)(?=(Areas for Improvement|Improvements)|\Z)(.*?)'
        r'(Areas for Improvement|Improvements)[:\n]*(.*)',
        re.IGNORECASE | re.DOTALL
    )
    
    match = loose_pattern.search(content)
    if match:
        sections["feedback"] = match.group(2).strip()
        sections["strengths"] = [s.strip() for s in match.group(6).split('\n') if s.strip()]
        sections["areas_for_improvement"] = [s.strip() for s in match.group(9).split('\n') if s.strip()]
        return sections
    
    bullets = re.findall(r'(?:^|\n)\s*[-•*]\s*(.*)', content)
    if bullets:
        mid_point = len(bullets) // 2
        sections["strengths"] = bullets[:mid_point]
        sections["areas_for_improvement"] = bullets[mid_point:]
        sections["feedback"] = "Automatic analysis completed (format detection)"
        return sections
    
    return {
        "feedback": content.strip() or "No analysis could be generated",
        "strengths": [],
        "areas_for_improvement": []
    }

def analyze_resume(state: ResumeState) -> ResumeState:
    try:
        prompt = f"""
**Resume Analysis Task - Technical Skills Focus**

**Resume Content:**
{state['resume_text'][:6000]}

**Job Description:**
{state['job_description'][:2000]}

**Instructions:**
1. Analyze HARD SKILLS first (programming languages, tools, frameworks)
2. Compare against job requirements
3. Provide SPECIFIC feedback in this exact format:

### Technical Skills Match
[List specific technologies that match between resume and job description]

### Key Strengths (Must be resume-specific)
1. [Specific technical skill from resume relevant to job]
2. [Specific project/experience relevant to job]
3. [Specific achievement/certification relevant to job]

### Missing Requirements
1. [Key requirement from job missing from resume]
2. [Secondary missing skill]
3. [Any other gaps]

### Suitability Assessment
[Direct answer: "Highly Suitable", "Potentially Suitable", or "Not Suitable"] 
[Brief 1-sentence justification]
"""

        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": "You are a technical recruiter analyzing skill matches."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=1024
        )

        content = response.choices[0].message.content

        result = {
            "feedback": "",
            "strengths": [],
            "missing_skills": [],
            "suitability": "Unknown"
        }

        current_section = None
        for line in content.split('\n'):
            line = line.strip()
            if not line:
                continue

            if line.startswith("### Technical Skills Match"):
                current_section = "feedback"
            elif line.startswith("### Key Strengths"):
                current_section = "strengths"
            elif line.startswith("### Missing Requirements"):
                current_section = "missing"
            elif line.startswith("### Suitability Assessment"):
                current_section = "suitability"
            elif current_section == "feedback":
                result["feedback"] += line + "\n"
            elif current_section == "strengths" and line[0].isdigit():
                result["strengths"].append(line.split(". ", 1)[1])
            elif current_section == "missing" and line[0].isdigit():
                result["missing_skills"].append(line.split(". ", 1)[1])
            elif current_section == "suitability":
                if "Highly Suitable" in line:
                    result["suitability"] = ("Highly Suitable", "green")
                elif "Potentially Suitable" in line:
                    result["suitability"] = ("Potentially Suitable", "orange")
                else:
                    result["suitability"] = ("Not Suitable", "red")

        return {
            **state,
            "feedback": result["feedback"].strip(),
            "strengths": "\n".join(f"- {s}" for s in result["strengths"]),
            "areas_for_improvement": "\n".join(f"- {s}" for s in result["missing_skills"]),
            "suitability": result["suitability"][0],
            "suitability_color": result["suitability"][1]
        }

    except Exception as e:
        print(f"Analysis error: {str(e)}")
        return {
            **state,
            "feedback": f"Analysis error: {str(e)}",
            "strengths": "",
            "areas_for_improvement": "",
            "suitability": "Analysis Failed",
            "suitability_color": "gray"
        }

def build_flow():
    workflow = StateGraph(ResumeState)
    workflow.add_node("analyze_resume", analyze_resume)
    workflow.set_entry_point("analyze_resume")
    workflow.set_finish_point("analyze_resume")
    return workflow.compile()