import re
import unicodedata
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)

def clean_text(text):
    """Clean and normalize text extracted from resumes"""
    if not text:
        return ""
    
    # Replace multiple spaces with a single space
    text = re.sub(r'\s+', ' ', text)
    
    # Remove excessive newlines (keep at most 2 consecutive newlines)
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    # Normalize unicode characters
    text = unicodedata.normalize('NFKD', text)
    
    # Remove special characters that are likely formatting artifacts
    text = re.sub(r'[^\w\s\.\,\;\:\-\(\)\[\]\{\}\'\"\!\?\/\&\+\=\*\%\$\#\@\|\\]', '', text)
    
    # Fix common OCR/extraction issues
    text = text.replace('•', '- ')  # Replace bullets with dashes
    
    return text.strip()

def format_phone_number(phone):
    """Format a phone number consistently"""
    if not phone:
        return ""
    
    # Remove all non-digit characters
    digits = re.sub(r'\D', '', phone)
    
    # Format based on length
    if len(digits) == 10:
        return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
    elif len(digits) == 11 and digits[0] == '1':
        return f"+1 ({digits[1:4]}) {digits[4:7]}-{digits[7:]}"
    else:
        return phone

def truncate_text(text, max_length=100):
    """Truncate text to a maximum length, ending with an ellipsis if truncated"""
    if not text:
        return ""
    
    if len(text) <= max_length:
        return text
    
    # Truncate at a word boundary when possible
    truncated = text[:max_length].rsplit(' ', 1)[0]
    return truncated + "..."

def calculate_profile_completeness(resume_data):
    """Calculate how complete a resume profile is based on key components"""
    if not resume_data:
        return 0
    
    # Define weights for different resume components
    component_weights = {
        'name': 10,
        'email': 10,
        'phone': 5,
        'summary': 15,
        'skills': 20,
        'education': 20,
        'experience': 20
    }
    
    # Calculate score based on presence and completeness of components
    score = 0
    
    # Check basic fields
    if resume_data.get('name'):
        score += component_weights['name']
    
    if resume_data.get('email'):
        score += component_weights['email']
    
    if resume_data.get('phone'):
        score += component_weights['phone']
    
    if resume_data.get('summary'):
        summary_length = len(resume_data['summary'])
        if summary_length > 200:
            score += component_weights['summary']
        else:
            score += (summary_length / 200) * component_weights['summary']
    
    # Check skills
    skills = resume_data.get('skills', [])
    if skills:
        skill_score = min(len(skills) / 10, 1) * component_weights['skills']
        score += skill_score
    
    # Check education
    education = resume_data.get('education', [])
    if education:
        edu_score = min(len(education), 2) / 2 * component_weights['education']
        score += edu_score
    
    # Check experience
    experience = resume_data.get('experience', [])
    if experience:
        exp_score = min(len(experience), 3) / 3 * component_weights['experience']
        score += exp_score
    
    return min(round(score), 100)  # Return score as a percentage, capped at 100
