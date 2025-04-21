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
logging.basicConfig(level=logging.DEBUG)

# Download NLTK resources if not already downloaded
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

# Compile regex patterns for common data
EMAIL_REGEX = re.compile(r'[\w\.-]+@[\w\.-]+\.\w+')
PHONE_REGEX = re.compile(r'(\+\d{1,3}[- ]?)?\(?\d{3}\)?[- ]?\d{3}[- ]?\d{4}')

# Common skills list for extraction
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
        if file_extension == 'pdf':
            pdf_reader = PdfReader(file_path)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
            return clean_text(text)
        elif file_extension == 'docx':
            doc = docx.Document(file_path)
            full_text = []
            for para in doc.paragraphs:
                full_text.append(para.text)
            return clean_text('\n'.join(full_text))
        elif file_extension == 'txt':
            with open(file_path, 'r', encoding='utf-8') as file:
                text = file.read()
            return clean_text(text)
        else:
            logging.error(f"Unsupported file extension: {file_extension}")
            return None
    except Exception as e:
        logging.error(f"Error extracting text from {file_path}: {str(e)}")
        return None

def extract_contact_info(text):
    emails = EMAIL_REGEX.findall(text)
    email = emails[0] if emails else ""

    phones = PHONE_REGEX.findall(text)
    phone = phones[0] if phones else ""

    lines = text.strip().split('\n')
    potential_name = lines[0].strip() if lines else ""

    if len(potential_name.split()) > 4 or '@' in potential_name or any(char.isdigit() for char in potential_name):
        potential_name = ""

    return {
        "name": potential_name,
        "email": email,
        "phone": phone
    }

def extract_skills(text):
    doc = nlp(text.lower())
    found_skills = []
    for skill in COMMON_SKILLS:
        if re.search(r'\b' + re.escape(skill) + r'\b', text.lower()):
            found_skills.append(skill.title())

    for ent in doc.ents:
        if ent.label_ in ["ORG", "PRODUCT"] and ent.text.lower() not in [s.lower() for s in found_skills]:
            if ent.text.lower() in [s.lower() for s in COMMON_SKILLS]:
                found_skills.append(ent.text.title())

    return sorted(list(set(found_skills)))

def extract_education(text):
    return []

def extract_experience(text):
    experience = []
    experience_keywords = [
        'experience', 'employment', 'work history', 'professional experience',
        'career', 'job history'
    ]

    lines = text.split('\n')
    in_experience_section = False
    current_exp = {}

    for line in lines:
        line = line.strip()
        if not line:
            continue

        if any(keyword.lower() in line.lower() for keyword in experience_keywords):
            in_experience_section = True
            continue

        if in_experience_section:
            date_pattern = r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}\s*[-–—]\s*(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|January|February|March|April|May|June|July|August|September|October|November|December)?\s*\d{0,4}|(\d{4}\s*[-–—]\s*(\d{4}|present|current|now))'

            if re.search(date_pattern, line, re.IGNORECASE):
                if current_exp and 'title' in current_exp:
                    experience.append(current_exp)

                title_match = re.split(date_pattern, line, flags=re.IGNORECASE)[0].strip()
                date_match = re.search(date_pattern, line, re.IGNORECASE).group(0)

                title_parts = re.split(r'\s*[,|]\s*', title_match, 1)
                if len(title_parts) >= 2:
                    position, company = title_parts[0], title_parts[1]
                else:
                    position, company = title_match, ""

                current_exp = {
                    'title': position.strip(),
                    'company': company.strip(),
                    'date': date_match.strip(),
                    'description': []
                }

            elif current_exp and 'title' in current_exp:
                if line.startswith('•') or line.startswith('-') or re.match(r'^\d+[\.)]\s', line):
                    current_exp['description'].append(line)

    if current_exp and 'title' in current_exp:
        experience.append(current_exp)

    for exp in experience:
        exp['description'] = '\n'.join(exp['description'])

    return experience

def extract_summary(text):
    summary_keywords = ['summary', 'professional summary', 'profile', 'objective', 'about me']

    lines = text.split('\n')
    summary = ""
    in_summary = False

    for i, line in enumerate(lines):
        if any(keyword.lower() in line.lower() for keyword in summary_keywords):
            in_summary = True
            j = i + 1
            summary_lines = []
            while j < len(lines) and len(summary_lines) < 5:
                if lines[j].strip():
                    summary_lines.append(lines[j].strip())
                j += 1
            summary = " ".join(summary_lines)
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
    skills = extract_skills(text)
    education = extract_education(text)
    experience = extract_experience(text)
    summary = extract_summary(text)

    return {
        'name': contact_info['name'],
        'email': contact_info['email'],
        'phone': contact_info['phone'],
        'summary': summary,
        'skills': skills,
        'education': education,
        'experience': experience
    }
