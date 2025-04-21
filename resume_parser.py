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
logger = logging.getLogger(__name__)

# Constants - Improved regex patterns
EMAIL_REGEX = re.compile(r'[\w\.-]+@[\w\.-]+\.\w+')
PHONE_REGEX = re.compile(r'(\+\d{1,3}\s?)?(\d{1,4}[\s\.-]?)?(\d{5,10})')  # Updated to match international formats
DATE_PATTERN = r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}\s*[-–—]\s*(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|January|February|March|April|May|June|July|August|September|October|November|December)?\s*\d{0,4}|(\d{4}\s*[-–—]\s*(\d{4}|present|current|now))'
EDUCATION_PATTERN = r'(?:education|academic|qualification|degree|university|college|school|institute|certification)'

# Expanded common skills list
COMMON_SKILLS = {
    # Programming Languages
    "python", "java", "javascript", "c++", "c#", "ruby", "php", "swift", "kotlin", "go", "rust", "c",
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
    "git", "api", "rest", "graphql", "microservices", "linux", "unix", "bash", "opencv", 
    "mediapipe", "object-oriented programming", "computer vision", "seaborn", "algorithms",
    "data structures", "federated learning", "relational database"
}

# Initialize NLP resources
def _init_nlp_resources():
    """Initialize NLP resources (spaCy and NLTK)"""
    try:
        nltk.data.find('tokenizers/punkt')
    except LookupError:
        nltk.download('punkt', quiet=True)
    
    try:
        return spacy.load("en_core_web_sm")
    except OSError:
        logger.info("Downloading spaCy model...")
        os.system("python -m spacy download en_core_web_sm")
        return spacy.load("en_core_web_sm")

# Initialize NLP with exception handling
try:
    nlp = _init_nlp_resources()
except Exception as e:
    logger.error(f"Error initializing NLP resources: {str(e)}", exc_info=True)
    # Fallback to a simpler approach if NLP initialization fails
    nlp = None

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
            with open(file_path, 'r', encoding='utf-8', errors='replace') as file:
                return clean_text(file.read())
        else:
            logger.error(f"Unsupported file extension: {file_extension}")
            return None
    except Exception as e:
        logger.error(f"Error extracting text from {file_path}: {str(e)}", exc_info=True)
        return None

def extract_contact_info(text):
    """Extract name, email, and phone number from text"""
    contact_info = {"name": "", "email": "", "phone": ""}
    
    # Extract email
    email_matches = EMAIL_REGEX.findall(text)
    if email_matches:
        contact_info["email"] = email_matches[0]
    
    # Extract phone number - improved to catch more formats
    lines = text.split('\n')
    for line in lines:
        phone_matches = PHONE_REGEX.findall(line)
        if phone_matches:
            # Combine all parts of the phone number
            for match in phone_matches:
                full_number = ''.join(part for part in match if part)
                if len(full_number) >= 10:  # Only consider matches with enough digits
                    contact_info["phone"] = line.strip()
                    break
    
    # Extract name - usually at the beginning of the resume
    first_lines = [line.strip() for line in lines[:5] if line.strip()]
    for line in first_lines:
        # If line doesn't contain common resume headers and isn't an email/phone
        if (not re.search(r'resume|cv|curriculum|vitae|profile|contact', line.lower()) and
            not EMAIL_REGEX.search(line) and
            not PHONE_REGEX.search(line) and
            2 <= len(line.split()) <= 5):
            contact_info["name"] = line
            break
    
    # If we still don't have a name, try another approach for single name formats
    if not contact_info["name"] and first_lines:
        potential_name = first_lines[0]
        if len(potential_name.split()) <= 3 and not any(char.isdigit() for char in potential_name):
            contact_info["name"] = potential_name
    
    return contact_info

def extract_skills(text):
    """Extract skills from text using spaCy and a predefined skills list"""
    text_lower = text.lower()
    found_skills = set()

    # Check for common skills
    for skill in COMMON_SKILLS:
        if re.search(r'\b' + re.escape(skill) + r'\b', text_lower):
            found_skills.add(skill.title())

    # Use NLP for additional skill extraction if available
    if nlp:
        try:
            doc = nlp(text)
            
            # Extract entities that might be skills
            for ent in doc.ents:
                if ent.label_ in ["ORG", "PRODUCT", "GPE"]:
                    normalized_ent = ent.text.lower()
                    if normalized_ent in COMMON_SKILLS and normalized_ent not in [s.lower() for s in found_skills]:
                        found_skills.add(ent.text.title())
        except Exception as e:
            logger.warning(f"Error in NLP processing for skills: {str(e)}")
    
    # Look for skills in "skill" sections
    lines = text.split('\n')
    in_skills_section = False
    for i, line in enumerate(lines):
        if re.search(r'\bskills?\b|\btechnical\b|\bproficienc(y|ies)\b', line.lower()):
            in_skills_section = True
            continue
        
        if in_skills_section:
            if re.search(r'\b(education|experience|project|certification|publication)\b', line.lower()):
                in_skills_section = False
                continue
                
            # Look for bullet points or comma-separated skills
            skill_candidates = re.split(r'[,•\-:]', line)
            for candidate in skill_candidates:
                candidate = candidate.strip().lower()
                if candidate in COMMON_SKILLS:
                    found_skills.add(candidate.title())
    
    return sorted(found_skills)

# The rest of your functions remain the same...

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
            'experience': [],
            'projects': [],
            'certifications': [],
            'publications': []
        }

    try:
        contact_info = extract_contact_info(text)
        
        # Extract all resume components with error handling for each section
        result = {
            'name': contact_info['name'],
            'email': contact_info['email'],
            'phone': contact_info['phone'],
            'summary': '',
            'skills': [],
            'education': [],
            'experience': [],
            'projects': [],
            'certifications': [],
            'publications': []
        }
        
        # Extract each section with individual try-except blocks
        try:
            result['summary'] = extract_summary(text)
        except Exception as e:
            logger.error(f"Error extracting summary: {str(e)}", exc_info=True)
            
        try:
            result['skills'] = extract_skills(text)
        except Exception as e:
            logger.error(f"Error extracting skills: {str(e)}", exc_info=True)
            
        try:
            result['education'] = extract_education(text)
        except Exception as e:
            logger.error(f"Error extracting education: {str(e)}", exc_info=True)
            
        try:
            result['experience'] = extract_experience(text)
        except Exception as e:
            logger.error(f"Error extracting experience: {str(e)}", exc_info=True)
            
        try:
            result['projects'] = extract_projects(text)
        except Exception as e:
            logger.error(f"Error extracting projects: {str(e)}", exc_info=True)
            
        try:
            result['certifications'] = extract_certifications(text)
        except Exception as e:
            logger.error(f"Error extracting certifications: {str(e)}", exc_info=True)
            
        try:
            result['publications'] = extract_publications(text)
        except Exception as e:
            logger.error(f"Error extracting publications: {str(e)}", exc_info=True)
            
        return result
        
    except Exception as e:
        logger.error(f"Error parsing resume: {str(e)}", exc_info=True)
        return {
            'name': '',
            'email': '',
            'phone': '',
            'summary': '',
            'skills': [],
            'education': [],
            'experience': [],
            'projects': [],
            'certifications': [],
            'publications': []
        }
