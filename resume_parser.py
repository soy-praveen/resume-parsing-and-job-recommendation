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
logger = logging.getLogger(_name_)

# Constants
EMAIL_REGEX = re.compile(r'[\w\.-]+@[\w\.-]+\.\w+')
PHONE_REGEX = re.compile(r'(\+\d{1,3}[- ]?)?\(?\d{3}\)?[- ]?\d{3}[- ]?\d{4}')
DATE_PATTERN = r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}\s*[-–—]\s*(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|January|February|March|April|May|June|July|August|September|October|November|December)?\s*\d{0,4}|(\d{4}\s*[-–—]\s*(\d{4}|present|current|now))'

# Common skills list for extraction (converted to set for faster lookups)
COMMON_SKILLS = {
    # Programming Languages
    "python", "java", "javascript", "c++", "c#", "ruby", "php", "swift", "kotlin", "go", "rust",
    # Web Development
    "html", "css", "react", "angular", "vue", "node.js", "express", "django", "flask", "spring",
    # Data Science
    "machine learning", "deep learning", "data analysis", "pandas", "numpy", "scikit-learn",
    "tensorflow", "pytorch", "data visualization", "statistics", "r", "tableau", "power bi",
    # Cloud & DevOps
    "aws", "azure", "gcp", "docker", "kubernetes", "jenkins", "ci/cd", "terraform", "ansible",
    # Databases
    "sql", "mysql", "postgresql", "mongodb", "oracle", "nosql", "firebase", "redis",
    # General Skills
    "problem solving", "teamwork", "communication", "leadership", "project management",
    "agile", "scrum", "critical thinking", "time management", "creativity",
    # Other Technical Skills
    "git", "api", "rest", "graphql", "microservices", "linux", "unix", "bash"
}

# Initialize NLP resources
def _init_nlp_resources():
    """Initialize NLP resources (spaCy and NLTK)"""
    try:
        nltk.data.find('tokenizers/punkt')
    except LookupError:
        nltk.download('punkt')
    
    try:
        return spacy.load("en_core_web_sm")
    except OSError:
        logger.info("Downloading spaCy model...")
        os.system("python -m spacy download en_core_web_sm")
        return spacy.load("en_core_web_sm")

nlp = _init_nlp_resources()

def extract_text_from_resume(file_path, file_extension):
    """Extract text from a resume file (PDF, DOCX, or TXT)"""
    try:
        if file_extension.lower() == 'pdf':
            with open(file_path, 'rb') as file:
                pdf_reader = PdfReader(file)
                text = "\n".join(page.extract_text() or "" for page in pdf_reader.pages)
                return clean_text(text)
                
        elif file_extension.lower() == 'docx':
            doc = docx.Document(file_path)
            return clean_text("\n".join(para.text for para in doc.paragraphs))
            
        elif file_extension.lower() == 'txt':
            with open(file_path, 'r', encoding='utf-8') as file:
                return clean_text(file.read())
                
        else:
            logger.error(f"Unsupported file extension: {file_extension}")
            return None
            
    except Exception as e:
        logger.error(f"Error extracting text from {file_path}: {str(e)}", exc_info=True)
        return None

def extract_contact_info(text):
    """Extract name, email, and phone number from text"""
    # Extract email
    email = next(iter(EMAIL_REGEX.findall(text)), "")
    
    # Extract phone number (take first match and join if it's a tuple)
    phone_match = PHONE_REGEX.search(text)
    phone = "".join(phone_match.groups()) if phone_match else ""
    
    # Extract name (using first non-empty line that doesn't contain contact info)
    for line in text.strip().split('\n'):
        line = line.strip()
        if line and not (EMAIL_REGEX.search(line) and PHONE_REGEX.search(line)):
            # Simple heuristic: name is usually 2-4 words
            if 2 <= len(line.split()) <= 4:
                return {
                    "name": line,
                    "email": email,
                    "phone": phone
                }
    
    return {"name": "", "email": email, "phone": phone}

def extract_skills(text):
    """Extract skills from text using spaCy and a predefined skills list"""
    text_lower = text.lower()
    found_skills = set()
    
    # Check for exact matches from COMMON_SKILLS
    for skill in COMMON_SKILLS:
        if re.search(r'\b' + re.escape(skill) + r'\b', text_lower):
            found_skills.add(skill.title())
    
    # Use spaCy to find potential skills in named entities
    doc = nlp(text)
    for ent in doc.ents:
        if ent.label_ in ["ORG", "PRODUCT"]:
            normalized_ent = ent.text.lower()
            if normalized_ent in COMMON_SKILLS and normalized_ent not in found_skills:
                found_skills.add(ent.text.title())
    
    return sorted(found_skills)

def extract_experience(text):
    """Extract work experience from text"""
    experience = []
    current_exp = {}
    experience_keywords = {'experience', 'employment', 'work history', 'professional experience', 'career', 'job history'}
    
    for line in text.split('\n'):
        line = line.strip()
        if not line:
            continue
        
        # Check for experience section header
        if any(keyword in line.lower() for keyword in experience_keywords):
            continue
        
        # Check for date pattern indicating a new experience entry
        date_match = re.search(DATE_PATTERN, line, re.IGNORECASE)
        if date_match:
            if current_exp:
                experience.append(current_exp)
            
            # Extract position and company
            line_before_date = line[:date_match.start()].strip()
            parts = re.split(r'\s*[,|]\s*', line_before_date, 1)
            
            current_exp = {
                'title': parts[0].strip() if parts else "",
                'company': parts[1].strip() if len(parts) > 1 else "",
                'date': date_match.group().strip(),
                'description': []
            }
        elif current_exp:
            # Add bullet points to current experience
            if line.startswith(('•', '-')) or re.match(r'^\d+[\.\)]\s', line):
                current_exp['description'].append(line)
    
    # Add the last experience if it exists
    if current_exp and current_exp.get('title'):
        experience.append(current_exp)
    
    # Clean descriptions
    for exp in experience:
        exp['description'] = '\n'.join(exp['description'])
    
    return experience

def extract_summary(text):
    """Extract a professional summary from the resume"""
    summary_keywords = {'summary', 'professional summary', 'profile', 'objective', 'about me'}
    lines = text.split('\n')
    
    # Try to find explicit summary section
    for i, line in enumerate(lines):
        if any(keyword in line.lower() for keyword in summary_keywords):
            summary_lines = [
                next_line.strip() 
                for next_line in lines[i+1:i+6] 
                if next_line.strip()
            ]
            if summary_lines:
                return " ".join(summary_lines)
    
    # Fallback to first meaningful paragraph
    paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
    if paragraphs and len(paragraphs[0]) > 50:
        first_para = paragraphs[0]
        if not (EMAIL_REGEX.search(first_para) or PHONE_REGEX.search(first_para)):
            return first_para
    
    return ""

def parse_resume(text):
    """Parse resume text and extract structured information"""
    if not text:
        return {
            'name': '',
            'email': '',
            'phone': '',
            'summary': '',
            'skills': [],
            'education': [],
            'experience': []
        }
    
    return {
        'name': extract_contact_info(text)['name'],
        'email': extract_contact_info(text)['email'],
        'phone': extract_contact_info(text)['phone'],
        'summary': extract_summary(text),
        'skills': extract_skills(text),
        'education': [],
        'experience': extract_experience(text)
    }
