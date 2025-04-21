import os
import re
import logging
import spacy
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
PHONE_REGEX = re.compile(r'(\+\d{1,3}[-\s]?)?\(?\d{3}\)?[-\s]?\d{3}[-\s]?\d{4}')

# Common skills
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
    
    lines = text.splitlines()
    potential_name = next((line for line in lines if line.strip()), "")
    if (len(potential_name.split()) > 5 or '@' in potential_name or any(char.isdigit() for char in potential_name)):
        potential_name = ""

    return {
        'name': potential_name.strip(),
        'email': email.group(0) if email else "",
        'phone': phone.group(0) if phone else ""
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
    # Placeholder (future implementation)
    return []

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
        # fallback: first paragraph without email/phone
        paragraphs = text.split('\n\n')
        if paragraphs:
            first_para = paragraphs[0].strip()
            if len(first_para) > 50 and '@' not in first_para and not PHONE_REGEX.search(first_para):
                summary = first_para

    return summary

def parse_resume(text):
    contact_info = extract_contact_info(text)
    return {
        'name': contact_info['name'],
        'email': contact_info['email'],
        'phone': contact_info['phone'],
        'summary': extract_summary(text),
        'skills': extract_skills(text),
        'education': extract_education(text),
        'experience': extract_experience(text)
    }
