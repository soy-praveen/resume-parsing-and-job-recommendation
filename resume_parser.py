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
    # If model not found, we'll download it
    os.system("python -m spacy download en_core_web_sm")
    nlp = spacy.load("en_core_web_sm")

# Compile regex patterns for common data
EMAIL_REGEX = re.compile(r'[\w\.-]+@[\w\.-]+\.\w+')
PHONE_REGEX = re.compile(r'(\+\d{1,3}[- ]?)?\(?\d{3}\)?[- ]?\d{3}[- ]?\d{4}')

# Common skills list for extraction
COMMON_SKILLS = [
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
]

def extract_text_from_resume(file_path, file_extension):
    """Extract text from a resume file (PDF, DOCX, or TXT)"""
    try:
        if file_extension == 'pdf':
            # Extract text from PDF
            pdf_reader = PdfReader(file_path)
            text = ""
            
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
            
            return clean_text(text)
            
        elif file_extension == 'docx':
            # Extract text from DOCX
            doc = docx.Document(file_path)
            full_text = []
            
            for para in doc.paragraphs:
                full_text.append(para.text)
            
            return clean_text('\n'.join(full_text))
        
        elif file_extension == 'txt':
            # Extract text from TXT file
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
    """Extract name, email, and phone number from text"""
    # Extract email using regex
    emails = EMAIL_REGEX.findall(text)
    email = emails[0] if emails else ""
    
    # Extract phone number using regex
    phones = PHONE_REGEX.findall(text)
    phone = phones[0] if phones else ""
    
    # Extract name (we'll use the first line of the resume as a heuristic)
    lines = text.strip().split('\n')
    potential_name = lines[0].strip() if lines else ""
    
    # Check if the potential name seems reasonable (not too long, doesn't contain email or phone)
    if len(potential_name.split()) > 4 or '@' in potential_name or any(char.isdigit() for char in potential_name):
        potential_name = ""
    
    return {
        "name": potential_name,
        "email": email,
        "phone": phone
    }

def extract_skills(text):
    """Extract skills from text using spaCy and a predefined skills list"""
    doc = nlp(text.lower())
    
    # Extract skills from text based on common skills list
    found_skills = []
    for skill in COMMON_SKILLS:
        if re.search(r'\b' + re.escape(skill) + r'\b', text.lower()):
            found_skills.append(skill.title())  # Capitalize skill
    
    # Extract any potential skills that might be named entities (like programming languages)
    for ent in doc.ents:
        if ent.label_ in ["ORG", "PRODUCT"] and ent.text.lower() not in [s.lower() for s in found_skills]:
            # Check if it's likely a tech or skill
            if ent.text.lower() in [s.lower() for s in COMMON_SKILLS]:
                found_skills.append(ent.text.title())
    
    return sorted(list(set(found_skills)))  # Remove duplicates and sort

def extract_education(text):
    """Education section is removed as requested, returns an empty list"""
    # This function has been simplified to return an empty list as education section is no longer needed
    return []

def extract_experience(text):
    """Extract work experience from text"""
    experience = []
    
    # Keywords that might indicate work experience sections
    experience_keywords = ['experience', 'employment', 'work history', 'professional experience',
                          'career', 'job history']
    
    # Split text into lines and try to identify experience sections
    lines = text.split('\n')
    
    in_experience_section = False
    current_exp = {}
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # Check if this line starts an experience section
        if any(keyword.lower() in line.lower() for keyword in experience_keywords):
            in_experience_section = True
            continue
        
        if in_experience_section:
            # Check for company/position line (often has a date range)
            date_pattern = r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}\s*[-–—]\s*(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|January|February|March|April|May|June|July|August|September|
::contentReference[oaicite:2]{index=2}
 
