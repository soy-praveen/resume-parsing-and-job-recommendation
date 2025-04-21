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

# Common skills list - expanded
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

    # Use NLP for additional skill extraction
    doc = nlp(text)
    
    # Extract entities that might be skills
    for ent in doc.ents:
        if ent.label_ in ["ORG", "PRODUCT", "GPE"]:
            normalized_ent = ent.text.lower()
            if normalized_ent in COMMON_SKILLS and normalized_ent not in [s.lower() for s in found_skills]:
                found_skills.add(ent.text.title())
    
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

def extract_education(text):
    """Extract education information from the resume"""
    education = []
    lines = text.split('\n')
    in_education_section = False
    current_edu = {}
    
    for i, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue
            
        # Detect education section
        if re.search(EDUCATION_PATTERN, line.lower()) and not in_education_section:
            in_education_section = True
            continue
            
        # End of education section
        if in_education_section and re.search(r'\b(experience|work|project|skill|certification|language)\b', line.lower()) and not re.search(r'education', line.lower()):
            in_education_section = False
            if current_edu:
                education.append(current_edu)
                current_edu = {}
            continue
            
        if in_education_section:
            # New education entry
            if line and (re.search(r'\b(university|college|institute|school)\b', line.lower()) or 
                         re.search(r'\b(B\.?Tech|M\.?Tech|PhD|Bachelor|Master|Diploma)\b', line, re.IGNORECASE)):
                if current_edu:
                    education.append(current_edu)
                    
                current_edu = {'institution': line, 'degree': '', 'date': '', 'details': []}
                
            # Look for degree information
            elif current_edu and re.search(r'\b(B\.?Tech|M\.?Tech|PhD|Bachelor|Master|Diploma|Degree)\b', line, re.IGNORECASE):
                current_edu['degree'] = line
                
            # Look for dates
            elif current_edu and re.search(r'\b\d{4}\b', line):
                if not current_edu['date']:
                    current_edu['date'] = line
                    
            # Additional details
            elif current_edu and line.startswith(('•', '-', '*')) or re.match(r'^\d+[\.\)]\s', line):
                current_edu['details'].append(line)
    
    # Add the last education entry if it exists
    if in_education_section and current_edu:
        education.append(current_edu)
        
    # Process CGPA/GPA if present in details
    for edu in education:
        edu['details'] = '\n'.join(edu['details'])
    
    return education

def extract_experience(text):
    """Extract work experience from text"""
    experience = []
    current_exp = {}
    experience_keywords = {'experience', 'employment', 'work history', 'professional experience', 'career', 'job history'}
    
    lines = text.split('\n')
    in_exp_section = False
    
    for i, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue
            
        # Detect experience section
        if any(keyword in line.lower() for keyword in experience_keywords) and not in_exp_section:
            in_exp_section = True
            continue
            
        # End of experience section
        if in_exp_section and any(section in line.lower() for section in ['education', 'skills', 'project', 'certification', 'publication']):
            in_exp_section = False
            if current_exp and current_exp.get('title'):
                experience.append(current_exp)
                current_exp = {}
            continue
        
        if in_exp_section:
            date_match = re.search(DATE_PATTERN, line, re.IGNORECASE)
            if date_match:
                if current_exp and current_exp.get('title'):
                    experience.append(current_exp)
                
                line_before_date = line[:date_match.start()].strip()
                parts = re.split(r'\s*[,|]\s*', line_before_date, 1)
                
                current_exp = {
                    'title': parts[0].strip() if parts else "",
                    'company': parts[1].strip() if len(parts) > 1 else "",
                    'date': date_match.group().strip(),
                    'description': []
                }
            elif current_exp:
                if line.startswith(('•', '-', '*')) or re.match(r'^\d+[\.\)]\s', line):
                    current_exp['description'].append(line)
    
    # Extract projects as experience if no work experience found
    if not experience:
        project_section = extract_projects(text)
        for project in project_section:
            exp_entry = {
                'title': project.get('name', ''),
                'company': project.get('type', 'Project'),
                'date': project.get('date', ''),
                'description': project.get('description', [])
            }
            if exp_entry['title']:
                experience.append(exp_entry)
    
    # Finalize the descriptions
    for exp in experience:
        if isinstance(exp['description'], list):
            exp['description'] = '\n'.join(exp['description'])
    
    return experience

def extract_projects(text):
    """Extract project information"""
    projects = []
    current_project = {}
    in_project_section = False
    
    lines = text.split('\n')
    for i, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue
            
        # Detect project section
        if re.search(r'\bprojects?\b', line.lower()) and not in_project_section:
            in_project_section = True
            continue
            
        # End of project section
        if in_project_section and any(section in line.lower() for section in ['experience', 'education', 'skills', 'certification', 'publication']):
            if current_project and current_project.get('name'):
                projects.append(current_project)
            in_project_section = False
            continue
            
        if in_project_section:
            # New project - typically a highlighted title
            if line and not line.startswith(('•', '-', '*')) and not re.match(r'^\d+[\.\)]\s', line) and i < len(lines) - 1:
                if current_project and current_project.get('name'):
                    projects.append(current_project)
                
                # Initial project entry
                current_project = {'name': line, 'date': '', 'type': 'Project', 'description': []}
                
                # Check next line for date
                next_line = lines[i+1].strip() if i+1 < len(lines) else ""
                date_match = re.search(r'\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}\b', next_line)
                if date_match:
                    current_project['date'] = date_match.group()
                    
                # If next line has "Individual Project" or similar, extract it
                type_match = re.search(r'\b(Individual|Team|Group|Database|Computer Vision|AI|ML)\s+Project\b', next_line)
                if type_match:
                    current_project['type'] = type_match.group()
                    
            # Project details
            elif current_project and (line.startswith(('•', '-', '*')) or re.match(r'^\d+[\.\)]\s', line)):
                current_project['description'].append(line)
    
    # Add the last project if it exists
    if in_project_section and current_project and current_project.get('name'):
        projects.append(current_project)
        
    # Process descriptions
    for project in projects:
        if isinstance(project['description'], list):
            project['description'] = '\n'.join(project['description'])
    
    return projects

def extract_certifications(text):
    """Extract certification information"""
    certifications = []
    current_cert = {}
    in_cert_section = False
    
    lines = text.split('\n')
    for i, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue
            
        # Detect certification section
        if re.search(r'\bcertifications?\b|\bcertificates?\b', line.lower()) and not in_cert_section:
            in_cert_section = True
            continue
            
        # End of certification section
        if in_cert_section and any(section in line.lower() for section in ['experience', 'education', 'skills', 'project', 'publication']):
            if current_cert and current_cert.get('name'):
                certifications.append(current_cert)
            in_cert_section = False
            continue
            
        if in_cert_section:
            # New certification entry
            if line and not line.startswith(('•', '-', '*')) and not re.match(r'^\d+[\.\)]\s', line):
                if current_cert and current_cert.get('name'):
                    certifications.append(current_cert)
                    
                current_cert = {'name': line, 'issuer': '', 'date': '', 'details': []}
                
                # Check next line for issuer
                next_line = lines[i+1].strip() if i+1 < len(lines) else ""
                if next_line and not next_line.startswith(('•', '-', '*')):
                    current_cert['issuer'] = next_line
                    
                # Look for date in current or next line
                date_match = re.search(r'\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}\b', line)
                if not date_match and next_line:
                    date_match = re.search(r'\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}\b', next_line)
                    
                if date_match:
                    current_cert['date'] = date_match.group()
                    
            # Certification details
            elif current_cert and (line.startswith(('•', '-', '*')) or re.match(r'^\d+[\.\)]\s', line)):
                current_cert['details'].append(line)
    
    # Add the last certification if it exists
    if in_cert_section and current_cert and current_cert.get('name'):
        certifications.append(current_cert)
        
    # Process details
    for cert in certifications:
        if isinstance(cert['details'], list):
            cert['details'] = '\n'.join(cert['details'])
    
    return certifications

def extract_summary(text):
    """Extract a professional summary from the resume"""
    summary_keywords = {'summary', 'professional summary', 'profile', 'objective', 'about me'}
    lines = text.split('\n')
    
    # Look for a dedicated summary section
    for i, line in enumerate(lines):
        line_lower = line.lower().strip()
        if any(keyword in line_lower for keyword in summary_keywords):
            summary_lines = []
            for j in range(i+1, min(i+6, len(lines))):
                next_line = lines[j].strip()
                if next_line and not any(section in next_line.lower() for section in 
                                      ['education', 'experience', 'skills', 'project']):
                    summary_lines.append(next_line)
                else:
                    break
                    
            if summary_lines:
                return " ".join(summary_lines)
    
    # If no dedicated summary, check the first paragraph
    paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
    if paragraphs and 50 <= len(paragraphs[0]) <= 500:
        first_para = paragraphs[0]
        if not (EMAIL_REGEX.search(first_para) or PHONE_REGEX.search(first_para) or 
                any(keyword in first_para.lower() for keyword in ['education', 'experience'])):
            return first_para
    
    return ""

def extract_publications(text):
    """Extract publication information"""
    publications = []
    current_pub = {}
    in_pub_section = False
    
    lines = text.split('\n')
    for i, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue
            
        # Detect publications section
        if re.search(r'\bpublications?\b|\bpapers?\b|\bjournal\b', line.lower()) and not in_pub_section:
            in_pub_section = True
            continue
            
        # End of publications section
        if in_pub_section and any(section in line.lower() for section in ['experience', 'education', 'skills', 'project', 'certification']):
            if current_pub and current_pub.get('title'):
                publications.append(current_pub)
            in_pub_section = False
            continue
            
        if in_pub_section:
            # New publication entry
            if line and not line.startswith(('•', '-', '*')) and not re.match(r'^\d+[\.\)]\s', line):
                if current_pub and current_pub.get('title'):
                    publications.append(current_pub)
                    
                current_pub = {'title': line, 'venue': '', 'date': '', 'details': []}
                
            # Publication details
            elif current_pub and (line.startswith(('•', '-', '*')) or re.match(r'^\d+[\.\)]\s', line)):
                current_pub['details'].append(line)
                
                # Look for publication identifiers like arXiv
                if 'arxiv' in line.lower():
                    current_pub['venue'] = 'arXiv'
                    # Extract date if present
                    date_match = re.search(r'\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}\b', line)
                    if date_match:
                        current_pub['date'] = date_match.group()
    
    # Add the last publication if it exists
    if in_pub_section and current_pub and current_pub.get('title'):
        publications.append(current_pub)
        
    # Process details
    for pub in publications:
        if isinstance(pub['details'], list):
            pub['details'] = '\n'.join(pub['details'])
    
    return publications

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

    contact_info = extract_contact_info(text)
    
    # Extract all resume components
    return {
        'name': contact_info['name'],
        'email': contact_info['email'],
        'phone': contact_info['phone'],
        'summary': extract_summary(text),
        'skills': extract_skills(text),
        'education': extract_education(text),
        'experience': extract_experience(text),
        'projects': extract_projects(text),
        'certifications': extract_certifications(text),
        'publications': extract_publications(text)
    }
