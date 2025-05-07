from flask import Flask, render_template, request, redirect, url_for
import fitz  # PyMuPDF
import os
from flow import build_flow
from typing import Dict, Any, List, Tuple
import re

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5MB limit
app.secret_key = '0418c707450aa1afa2ade3d58e71bf7232128ce9b123828ee3fff839d616df4c'  # Replace with a strong secret key

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Compile the workflow
flow = build_flow()

def extract_text_from_pdf(pdf_path: str) -> str:
    """Extract text from PDF file with error handling."""
    try:
        text = ""
        with fitz.open(pdf_path) as doc:
            for page in doc:
                text += page.get_text()
        return text.strip()
    except Exception as e:
        print(f"Error extracting PDF text: {e}")
        raise ValueError("Failed to extract text from PDF")

def validate_inputs(resume_text: str, job_description: str) -> bool:
    """Lenient validation that accepts minimal inputs."""
    if not resume_text or len(resume_text.strip()) < 50:
        return False
    if not job_description or len(job_description.strip()) < 10:
        return False
    return True

def clean_text(text: str) -> str:
    """Clean and normalize text input."""
    text = re.sub(r'\s+', ' ', text).strip()
    return text.encode('ascii', 'ignore').decode('ascii')

def extract_skills(text: str) -> List[str]:
    """Extract technical skills from text with comprehensive mapping."""
    skills_mapping = {
    'python': ['python', 'django', 'flask', 'fastapi', 'pandas', 'numpy', 'scikit-learn', 'matplotlib', 'seaborn', 'tkinter', 'pyqt'],
    'java': ['java', 'spring', 'hibernate', 'j2ee', 'jakarta ee', 'javafx', 'maven', 'gradle'],
    'javascript': ['javascript', 'node', 'react', 'angular', 'vue', 'typescript', 'express', 'jquery', 'next.js', 'nuxt.js'],
    'sql': ['sql', 'mysql', 'postgresql', 'oracle', 'sql server', 'sqlite', 'pl/sql', 'tsql'],
    'aws': ['aws', 'amazon web services', 's3', 'lambda', 'ec2', 'rds', 'cloudwatch', 'cloudformation', 'ecr', 'ecs', 'iam'],
    'azure': ['azure', 'microsoft azure', 'azure functions', 'azure devops', 'cosmos db', 'azure blob', 'aks'],
    'gcp': ['gcp', 'google cloud platform', 'bigquery', 'cloud functions', 'firebase', 'gke', 'app engine'],
    'devops': ['devops', 'docker', 'kubernetes', 'jenkins', 'ansible', 'terraform', 'ci/cd', 'helm', 'prometheus', 'grafana'],
    'machine_learning': ['machine learning', 'ml', 'sklearn', 'xgboost', 'lightgbm', 'mlops'],
    'deep_learning': ['deep learning', 'cnn', 'rnn', 'lstm', 'transformers', 'autoencoders', 'tensorflow', 'keras', 'pytorch'],
    'data_science': ['data science', 'data analyst', 'data wrangling', 'data visualization', 'exploratory data analysis', 'eda', 'statistical modeling'],
    'ai': ['artificial intelligence', 'ai', 'nlp', 'langchain', 'langgraph', 'chatbot', 'openai', 'gpt', 'llm', 'agents'],
    'hr': ['hr', 'recruitment', 'payroll', 'talent acquisition', 'employee engagement', 'interviewing', 'hiring'],
    'cloud': ['cloud', 'cloud computing', 'cloud engineer', 'cloud infrastructure', 'aws', 'azure', 'gcp'],
    'cybersecurity': ['cybersecurity', 'network security', 'penetration testing', 'ethical hacking', 'firewalls', 'siem', 'nmap', 'burp suite'],
    'frontend': ['html', 'css', 'javascript', 'bootstrap', 'sass', 'react', 'vue', 'angular'],
    'backend': ['node', 'express', 'django', 'flask', 'spring boot', 'ruby on rails', 'php', 'laravel'],
    'mobile': ['android', 'ios', 'flutter', 'react native', 'kotlin', 'swift'],
    'testing': ['software testing', 'unit testing', 'selenium', 'pytest', 'junit', 'testng', 'automation testing'],
    'c_c++': ['c', 'c++', 'stl', 'oop', 'embedded c'],
    'r_language': ['r', 'r programming', 'ggplot2', 'tidyverse', 'caret'],
    'big_data': ['big data', 'hadoop', 'spark', 'hive', 'pig', 'kafka'],
    'blockchain': ['blockchain', 'ethereum', 'solidity', 'smart contracts', 'web3'],
    'ui_ux': ['ui/ux', 'figma', 'adobe xd', 'prototyping', 'wireframing', 'user experience'],
}

    
    
    
    text_lower = text.lower()
    found_skills = []
    
    for skill, keywords in skills_mapping.items():
        if any(f' {keyword} ' in f' {text_lower} ' for keyword in keywords):
            found_skills.append(skill)
    
    return list(set(found_skills))

def analyze_match(resume_text: str, job_description: str) -> Dict[str, Any]:
    """Perform detailed analysis with accurate suitability scoring."""
    result = {
        'feedback': '',
        'strengths': [],
        'improvements': [],
        'suitability': 'Unknown',
        'suitability_color': 'gray',
        'match_score': 0,
        'matched_skills': [],
        'missing_skills': []
    }
    
    try:
        # Get analysis from LangGraph flow
        analysis_result = flow.invoke({
            "resume_text": resume_text,
            "job_description": job_description,
            "feedback": "",
            "strengths": "",
            "areas_for_improvement": ""
        })
        
        # Process results
        result['feedback'] = analysis_result.get('feedback', 'No feedback generated')
        
        # Process strengths
        strengths = analysis_result.get('strengths', '')
        if isinstance(strengths, str):
            result['strengths'] = [s.strip() for s in strengths.split('\n') if s.strip()]
        elif isinstance(strengths, list):
            result['strengths'] = strengths
        
        # Process improvements
        improvements = analysis_result.get('areas_for_improvement', '')
        if isinstance(improvements, str):
            result['improvements'] = [i.strip() for i in improvements.split('\n') if i.strip()]
        elif isinstance(improvements, list):
            result['improvements'] = improvements
        
        # Skill-based matching
        required_skills = extract_skills(job_description)
        resume_skills = extract_skills(resume_text)
        result['matched_skills'] = [skill for skill in required_skills if skill in resume_skills]
        result['missing_skills'] = [skill for skill in required_skills if skill not in resume_skills]
        
        # Calculate match score (0-100)
        if required_skills:
            result['match_score'] = int((len(result['matched_skills']) / len(required_skills)) * 100)
        
        # Determine suitability
        if result['match_score'] >= 75:
            result['suitability'] = "Highly Suitable"
            result['suitability_color'] = "green"
        elif result['match_score'] >= 40:
            result['suitability'] = "Potentially Suitable"
            result['suitability_color'] = "orange"
        else:
            result['suitability'] = "Not Suitable"
            result['suitability_color'] = "red"
            
    except Exception as e:
        print(f"Analysis error: {str(e)}")
        result['feedback'] = f"Analysis error: {str(e)}"
    
    return result

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    if 'resume' not in request.files:
        return render_template('error.html', message="No file uploaded")
    
    file = request.files['resume']
    job_description = request.form.get('job_description', '').strip()
    
    if file.filename == '':
        return render_template('error.html', message="No selected file")
    
    if not file.filename.lower().endswith('.pdf'):
        return render_template('error.html', message="Only PDF files are accepted")
    
    if not job_description:
        return render_template('error.html', message="Job description is required")
    
    try:
        # Process uploaded file
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(filepath)
        resume_text = clean_text(extract_text_from_pdf(filepath))
        job_description = clean_text(job_description)
        
        # Clean up
        if os.path.exists(filepath):
            os.remove(filepath)
        
        if not validate_inputs(resume_text, job_description):
            return render_template('error.html', 
                message="Resume or job description is too short")
        
        # Perform detailed analysis
        analysis = analyze_match(resume_text, job_description)
        
        return render_template('results.html',
            feedback=analysis['feedback'],
            strengths=analysis['strengths'],
            improvements=analysis['improvements'],
            suitable=analysis['suitability'],
            suitability_color=analysis['suitability_color'],
            match_score=analysis['match_score'],
            matched_skills=analysis['matched_skills'],
            missing_skills=analysis['missing_skills']
        )
        
    except ValueError as e:
        return render_template('error.html', message=str(e))
    except Exception as e:
        print(f"Error: {str(e)}")
        return render_template('error.html', 
            message="An error occurred during analysis")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)