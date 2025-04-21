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
    
    # Fixed date pattern - properly terminated string
    date_pattern = r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}\s*[-–—]\s*(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|January|February|March|April|May|June|July|August|September|October|November|December)?\s*\d{0,4}|(\d{4}\s*[-–—]\s*(\d{4}|present|current|now))'
    
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
            date_match = re.search(date_pattern, line, re.IGNORECASE)
            
            if date_match:
                # If we found a date, this is likely a new position
                if current_exp:
                    # Save the previous experience entry if it exists
                    experience.append(current_exp)
                
                # Extract company and title from the line
                company_title_text = line[:date_match.start()].strip()
                
                # Try to split company and title (often separated by a comma, pipe, or at)
                if '|' in company_title_text:
                    parts = company_title_text.split('|', 1)
                    title = parts[0].strip()
                    company = parts[1].strip()
                elif ',' in company_title_text:
                    parts = company_title_text.split(',', 1)
                    title = parts[0].strip()
                    company = parts[1].strip()
                elif ' at ' in company_title_text.lower():
                    parts = company_title_text.lower().split(' at ', 1)
                    title = parts[0].strip()
                    company = parts[1].strip()
                else:
                    # If no clear separator, assume the whole text is the title
                    title = company_title_text
                    company = ""
                
                # Create new experience entry
                current_exp = {
                    "title": title,
                    "company": company,
                    "date": date_match.group(0),
                    "description": []
                }
            
            # If we're in an experience entry, add bullet points to the description
            elif current_exp and (line.startswith(('•', '-', '*')) or re.match(r'^\d+[\.\)]\s', line)):
                current_exp["description"].append(line)
            
            # Check if we've reached the end of the experience section
            elif any(keyword.lower() in line.lower() for keyword in ['education', 'skills', 'projects', 'certifications']):
                in_experience_section = False
                if current_exp:
                    experience.append(current_exp)
                    current_exp = {}
    
    # Add the last experience entry if it exists
    if current_exp:
        experience.append(current_exp)
    
    # Convert description lists to strings
    for exp in experience:
        if "description" in exp and isinstance(exp["description"], list):
            exp["description"] = "\n".join(exp["description"])
    
    return experience

def extract_projects(text):
    """Extract project information from text"""
    projects = []
    
    # Keywords that might indicate project sections
    project_keywords = ['projects', 'personal projects', 'academic projects', 'key projects']
    
    # Split text into lines and try to identify project sections
    lines = text.split('\n')
    
    in_project_section = False
    current_project = {}
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # Check if this line starts a project section
        if any(keyword.lower() in line.lower() for keyword in project_keywords):
            in_project_section = True
            continue
        
        if in_project_section:
            # Check for project title line (often bold or on its own line)
            if not line.startswith(('•', '-', '*')) and not re.match(r'^\d+[\.\)]\s', line):
                # If we found what looks like a title, this is likely a new project
                if current_project and 'name' in current_project:
                    # Save the previous project entry if it exists
                    projects.append(current_project)
                
                # Create new project entry
                current_project = {
                    "name": line,
                    "description": []
                }
            
            # If we're in a project entry, add bullet points to the description
            elif current_project and (line.startswith(('•', '-', '*')) or re.match(r'^\d+[\.\)]\s', line)):
                current_project["description"].append(line)
            
            # Check if we've reached the end of the project section
            elif any(keyword.lower() in line.lower() for keyword in ['experience', 'education', 'skills', 'certifications']):
                in_project_section = False
                if current_project and 'name' in current_project:
                    projects.append(current_project)
                    current_project = {}
    
    # Add the last project entry if it exists
    if current_project and 'name' in current_project:
        projects.append(current_project)
    
    # Convert description lists to strings
    for project in projects:
        if "description" in project and isinstance(project["description"], list):
            project["description"] = "\n".join(project["description"])
    
    return projects

def extract_certifications(text):
    """Extract certification information from text"""
    certifications = []
    
    # Keywords that might indicate certification sections
    cert_keywords = ['certifications', 'certificates', 'credentials', 'licenses']
    
    # Split text into lines and try to identify certification sections
    lines = text.split('\n')
    
    in_cert_section = False
    current_cert = {}
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # Check if this line starts a certification section
        if any(keyword.lower() in line.lower() for keyword in cert_keywords):
            in_cert_section = True
            continue
        
        if in_cert_section:
            # Check for certification title line
            if not line.startswith(('•', '-', '*')) and not re.match(r'^\d+[\.\)]\s', line):
                # If we found what looks like a title, this is likely a new certification
                if current_cert and 'name' in current_cert:
                    # Save the previous certification entry if it exists
                    certifications.append(current_cert)
                
                # Create new certification entry
                current_cert = {
                    "name": line,
                    "issuer": "",
                    "date": ""
                }
                
                # Try to extract issuer and date if they're on the same line
                if ',' in line:
                    parts = line.split(',')
                    current_cert["name"] = parts[0].strip()
                    if len(parts) > 1:
                        # The second part might contain the issuer or date
                        second_part = parts[1].strip()
                        
                        # Check if it contains a date
                        date_match = re.search(r'\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}\b|\b\d{4}\b', second_part)
                        
                        if date_match:
                            current_cert["date"] = date_match.group(0)
                            # The issuer might be before the date
                            issuer_text = second_part[:date_match.start()].strip()
                            if issuer_text:
                                current_cert["issuer"] = issuer_text
                        else:
                            # If no date, assume it's the issuer
                            current_cert["issuer"] = second_part
            
            # Check if we've reached the end of the certification section
            elif any(keyword.lower() in line.lower() for keyword in ['experience', 'education', 'skills', 'projects']):
                in_cert_section = False
                if current_cert and 'name' in current_cert:
                    certifications.append(current_cert)
                    current_cert = {}
    
    # Add the last certification entry if it exists
    if current_cert and 'name' in current_cert:
        certifications.append(current_cert)
    
    return certifications

def extract_summary(text):
    """Extract a professional summary from the resume"""
    # Look for summary section
    summary_keywords = ['summary', 'professional summary', 'profile', 'objective', 'about me']
    
    lines = text.split('\n')
    summary = ""
    in_summary_section = False
    
    for i, line in enumerate(lines):
        line_lower = line.lower().strip()
        
        # Check if this line starts a summary section
        if any(keyword in line_lower for keyword in summary_keywords) and not in_summary_section:
            in_summary_section = True
            continue
        
        if in_summary_section:
            # Add lines until we hit another section or have collected enough lines
            if line.strip() and not any(keyword in line_lower for keyword in ['experience', 'education', 'skills', 'projects', 'certifications']):
                summary += line.strip() + " "
            else:
                # We've reached the end of the summary section
                break
    
    # If no explicit summary section was found, use the first paragraph as a fallback
    if not summary:
        paragraphs = text.split('\n\n')
        if paragraphs:
            first_para = paragraphs[0].strip()
            # Only use if it's not too short and doesn't look like contact info
            if len(first_para) > 50 and not EMAIL_REGEX.search(first_para) and not PHONE_REGEX.search(first_para):
                summary = first_para
    
    return summary.strip()

def extract_publications(text):
    """Extract publication information from text"""
    publications = []
    
    # Keywords that might indicate publication sections
    pub_keywords = ['publications', 'papers', 'research', 'articles', 'journals']
    
    # Split text into lines and try to identify publication sections
    lines = text.split('\n')
    
    in_pub_section = False
    current_pub = {}
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # Check if this line starts a publication section
        if any(keyword.lower() in line.lower() for keyword in pub_keywords):
            in_pub_section = True
            continue
        
        if in_pub_section:
            # Check for publication title line
            if not line.startswith(('•', '-', '*')) and not re.match(r'^\d+[\.\)]\s', line):
                # If we found what looks like a title, this is likely a new publication
                if current_pub and 'title' in current_pub:
                    # Save the previous publication entry if it exists
                    publications.append(current_pub)
                
                # Create new publication entry
                current_pub = {
                    "title": line,
                    "journal": "",
                    "date": "",
                    "authors": "",
                    "url": ""
                }
                
                # Try to extract journal and date if they're on the same line
                if ',' in line:
                    parts = line.split(',')
                    current_pub["title"] = parts[0].strip()
                    
                    if len(parts) > 1:
                        # The second part might contain the journal or date
                        for part in parts[1:]:
                            part = part.strip()
                            
                            # Check if it contains a date
                            date_match = re.search(r'\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}\b|\b\d{4}\b', part)
                            
                            if date_match:
                                current_pub["date"] = date_match.group(0)
                            elif 'http' in part.lower() or 'www' in part.lower():
                                current_pub["url"] = part
                            else:
                                # If no date or URL, assume it's the journal
                                current_pub["journal"] = part
            
            # If we're in a publication entry, check for additional details
            elif current_pub and (line.startswith(('•', '-', '*')) or re.match(r'^\d+[\.\)]\s', line)):
                # This might contain authors, DOI, or other details
                if 'author' in line.lower():
                    current_pub["authors"] = line.split(':', 1)[1].strip() if ':' in line else line
                elif 'doi' in line.lower() or 'http' in line.lower():
                    current_pub["url"] = line
            
            # Check if we've reached the end of the publication section
            elif any(keyword.lower() in line.lower() for keyword in ['experience', 'education', 'skills', 'projects', 'certifications']):
                in_pub_section = False
                if current_pub and 'title' in current_pub:
                    publications.append(current_pub)
                    current_pub = {}
    
    # Add the last publication entry if it exists
    if current_pub and 'title' in current_pub:
        publications.append(current_pub)
    
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
    
    try:
        # Extract contact information
        contact_info = extract_contact_info(text)
        
        # Extract all resume components
        result = {
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
        
        return result
        
    except Exception as e:
        logger.error(f"Error parsing resume: {str(e)}")
        # Return empty structure in case of error
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
