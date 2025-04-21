import os
import re
import logging
import spacy
from datetime import datetime
from dateutil import parser as date_parser
from PyPDF2 import PdfReader
import docx
import nltk
from nltk.tokenize import word_tokenize, sent_tokenize
from utils import clean_text

# Configure logging
logging.basicConfig(level=logging.INFO)

# Download NLTK resources if missing
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

# Load spaCy model
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    os.system("python -m spacy download en_core_web_sm")
    nlp = spacy.load("en_core_web_sm")

# Regex patterns
EMAIL_REGEX = re.compile(r'[\w\.-]+@[\w\.-]+\.\w+')
PHONE_REGEX = re.compile(r'(\+\d{1,3}[-\s]?)?\(?\d{2,4}\)?[-\s]?\d{3,5}[-\s]?\d{4}')
LINKEDIN_REGEX = re.compile(r'(https?://)?(www\.)?linkedin\.com/in/[a-zA-Z0-9\-\_]+')
GITHUB_REGEX = re.compile(r'(https?://)?(www\.)?github\.com/[a-zA-Z0-9\-\_]+')
LOCATION_REGEX = re.compile(r'\b(?:[A-Z][a-z]+(?:,)?\s?){1,3}(India|USA|UK|Canada|Germany|Australia|France|Singapore)?\b')

# Skills list (expandable)
COMMON_SKILLS = [
    "python", "java", "javascript", "c++", "c#", "ruby", "php", "swift", "kotlin", "go", "rust",
    "html", "css", "react", "angular", "vue", "node.js", "express", "django", "flask", "spring",
    "machine learning", "deep learning", "data analysis", "pandas", "numpy", "scikit-learn",
    "tensorflow", "pytorch", "data visualization", "statistics", "r", "tableau", "power bi",
    "aws", "azure", "gcp", "docker", "kubernetes", "jenkins", "ci/cd", "terraform", "ansible",
    "sql", "mysql", "postgresql", "mongodb", "oracle", "nosql", "firebase", "redis",
    "problem solving", "teamwork", "communication", "leadership", "project management",
    "agile", "scrum", "critical thinking", "time management", "creativity",
    "git", "api", "rest", "graphql", "microservices", "linux", "unix", "bash"
]

# Degree and Cert patterns
DEGREE_KEYWORDS = ['bachelor', 'master', 'b.sc', 'b.tech', 'm.sc', 'm.tech', 'mba', 'phd']
CERTIFICATION_KEYWORDS = ['certified', 'certification', 'completed course', 'diploma']

def extract_text_from_resume(file_path, file_extension):
    try:
        if file_extension.lower() == 'pdf':
            text = ''
            reader = PdfReader(file_path)
            for page in reader.pages:
                text += page.extract_text() + '\n'
            return clean_text(text)
        elif file_extension.lower() == 'docx':
            doc = docx.Document(file_path)
            return clean_text('\n'.join(para.text for para in doc.paragraphs))
        elif file_extension.lower() == 'txt':
            with open(file_path, 'r', encoding='utf-8') as f:
                return clean_text(f.read())
        else:
            logging.error(f"Unsupported file extension: {file_extension}")
            return None
    except Exception as e:
        logging.error(f"Failed to extract text from {file_path}: {e}")
        return None

def extract_contact_info(text):
    email = EMAIL_REGEX.search(text)
    phone = PHONE_REGEX.search(text)
    linkedin = LINKEDIN_REGEX.search(text)
    github = GITHUB_REGEX.search(text)
    location = LOCATION_REGEX.search(text)
    
    lines = text.splitlines()
    potential_name = next((line for line in lines if line.strip()), "")
    if (len(potential_name.split()) > 5 or '@' in potential_name or any(char.isdigit() for char in potential_name)):
        potential_name = ""

    return {
        'name': potential_name.strip(),
        'email': email.group(0) if email else "",
        'phone': phone.group(0) if phone else "",
        'linkedin': linkedin.group(0) if linkedin else "",
        'github': github.group(0) if github else "",
        'location': location.group(0) if location else ""
    }

def extract_skills(text):
    text_lower = text.lower()
    found_skills = [skill.title() for skill in COMMON_SKILLS if re.search(r'\b' + re.escape(skill) + r'\b', text_lower)]
    
    doc = nlp(text_lower)
    for ent in doc.ents:
        if ent.label_ in {"ORG", "PRODUCT"}:
            if ent.text.strip().lower() in COMMON_SKILLS and ent.text.title() not in found_skills:
                found_skills.append(ent.text.title())
    
    return sorted(set(found_skills))

def extract_education(text):
    education = []
    for line in text.splitlines():
        if any(degree in line.lower() for degree in DEGREE_KEYWORDS):
            education.append(line.strip())
    return education

def extract_certifications(text):
    certifications = []
    for line in text.splitlines():
        if any(cert in line.lower() for cert in CERTIFICATION_KEYWORDS):
            certifications.append(line.strip())
    return certifications

def extract_languages(text):
    languages_list = ['english', 'hindi', 'french', 'german', 'spanish', 'mandarin', 'tamil', 'telugu']
    found = [lang.title() for lang in languages_list if lang in text.lower()]
    return sorted(found)

def extract_projects(text):
    projects = []
    for line in text.splitlines():
        if any(word in line.lower() for word in ['project', 'portfolio', 'system']):
            projects.append(line.strip())
    return projects

def extract_experience(text):
    experience = []
    lines = text.splitlines()
    in_experience_section = False
    current_exp = {}
    
    experience_keywords = [
        'experience', 'employment', 'work history', 'professional experience', 'career', 'job history'
    ]
    date_pattern = r'(Jan(uary)?|Feb(ruary)?|Mar(ch)?|Apr(il)?|May|Jun(e)?|Jul(y)?|Aug(ust)?|Sep(tember)?|Oct(ober)?|Nov(ember)?|Dec(ember)?)[\s,]*\d{4}[-–—to\s]*(Jan(uary)?|Feb(ruary)?|Mar(ch)?|Apr(il)?|May|Jun(e)?|Jul(y)?|Aug(ust)?|Sep(tember)?|Oct(ober)?|Nov(ember)?|Dec(ember)?|\d{4}|present|current|now)?'

    for line in lines:
        line = line.strip()
        if not line:
            continue

        if not in_experience_section and any(keyword in line.lower() for keyword in experience_keywords):
            in_experience_section = True
            continue
        
        if in_experience_section:
            if re.search(date_pattern, line, re.IGNORECASE):
                if current_exp:
                    experience.append(current_exp)
                title_company_part = re.split(date_pattern, line, flags=re.IGNORECASE)[0].strip()
                date_match = re.search(date_pattern, line, re.IGNORECASE)
                
                position, company = (title_company_part.split(',', 1) + [""])[:2]
                current_exp = {
                    'title': position.strip(),
                    'company': company.strip(),
                    'date': date_match.group(0).strip() if date_match else '',
                    'description': []
                }
            elif current_exp:
                if line.startswith(('-', '•')) or re.match(r'^\d+[\).]', line):
                    current_exp['description'].append(line)
    
    if current_exp:
        experience.append(current_exp)

    # Join descriptions
    for exp in experience:
        exp['description'] = '\n'.join(exp['description'])

    return experience

def calculate_total_experience(experience):
    total_months = 0
    for exp in experience:
        date_range = exp.get('date', '').lower()
        dates = re.split(r'[-–—to\s]+', date_range)
        try:
            start = date_parser.parse(dates[0], fuzzy=True)
            end = datetime.now() if len(dates) < 2 or dates[1] in ['present', 'current', 'now'] else date_parser.parse(dates[1], fuzzy=True)
            total_months += (end.year - start.year) * 12 + (end.month - start.month)
        except Exception:
            continue
    years = total_months // 12
    months = total_months % 12
    return f"{years} years {months} months" if years else f"{months} months"

def extract_summary(text):
    summary_keywords = ['summary', 'professional summary', 'profile', 'objective', 'about me']
    lines = text.splitlines()
    in_summary = False
    summary = ""
    
    for i, line in enumerate(lines):
        if any(keyword in line.lower() for keyword in summary_keywords):
            in_summary = True
            summary_lines = []
            for j in range(i+1, min(i+6, len(lines))):
                if lines[j].strip():
                    summary_lines.append(lines[j].strip())
            summary = ' '.join(summary_lines)
            break

    if not summary:
        paragraphs = text.split('\n\n')
        if paragraphs:
            first_para = paragraphs[0].strip()
            if len(first_para) > 50 and '@' not in first_para and not PHONE_REGEX.search(first_para):
                summary = first_para

    return summary

def parse_resume(text):
    contact_info = extract_contact_info(text)
    experience = extract_experience(text)
    return {
        'name': contact_info['name'],
        'email': contact_info['email'],
        'phone': contact_info['phone'],
        'location': contact_info['location'],
        'linkedin': contact_info['linkedin'],
        'github': contact_info['github'],
        'summary': extract_summary(text),
        'skills': extract_skills(text),
        'experience': experience,
        'total_experience': calculate_total_experience(experience),
        'degrees': extract_education(text),
        'certifications': extract_certifications(text),
        'languages': extract_languages(text),
        'projects': extract_projects(text)
    }
