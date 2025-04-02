import logging
import random
import re
from collections import Counter
import numpy as np
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize

try:
    import spacy
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False
    logging.warning("spaCy or scikit-learn not available. Using basic matching.")

# Download NLTK resources if not already available
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt', quiet=True)
try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords', quiet=True)

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Load spaCy model for NLP processing (this is our BERT-like model)
BERT_LIKE_AVAILABLE = False
nlp = None  # Initialize to avoid unbound variable error

if SPACY_AVAILABLE:
    try:
        nlp = spacy.load("en_core_web_sm")
        logger.info("Using spaCy model for enhanced semantic matching (BERT-like functionality)")
        BERT_LIKE_AVAILABLE = True
    except Exception as e:
        logger.error(f"Could not load spaCy model: {str(e)}")
else:
    logger.warning("spaCy not available, using basic matching only")

# Sample job postings database (in a real application, this would come from a database or API)
SAMPLE_JOB_POSTINGS = [
    {
        "id": 1,
        "title": "Software Engineer",
        "company": "Tech Innovations Inc.",
        "location": "San Francisco, CA",
        "description": "We are looking for a software engineer with experience in web development and a strong foundation in computer science fundamentals.",
        "required_skills": ["Python", "JavaScript", "React", "SQL", "Git", "API"]
    },
    {
        "id": 2,
        "title": "Data Scientist",
        "company": "DataWorks Analytics",
        "location": "Boston, MA",
        "description": "Join our team of data scientists working on cutting-edge machine learning solutions for enterprise clients.",
        "required_skills": ["Python", "Machine Learning", "Pandas", "NumPy", "SQL", "Statistics", "Data Visualization"]
    },
    {
        "id": 3,
        "title": "Full Stack Developer",
        "company": "WebSphere Solutions",
        "location": "Seattle, WA",
        "description": "Looking for a full stack developer familiar with modern web technologies and frameworks.",
        "required_skills": ["JavaScript", "React", "Node.js", "Express", "MongoDB", "HTML", "CSS"]
    },
    {
        "id": 4,
        "title": "DevOps Engineer",
        "company": "Cloud Systems Inc.",
        "location": "Austin, TX",
        "description": "Help us build and maintain our cloud infrastructure and CI/CD pipelines.",
        "required_skills": ["AWS", "Docker", "Kubernetes", "Jenkins", "Linux", "Terraform", "Git"]
    },
    {
        "id": 5,
        "title": "Machine Learning Engineer",
        "company": "AI Innovations",
        "location": "Mountain View, CA",
        "description": "Join our team developing state-of-the-art machine learning models for various applications.",
        "required_skills": ["Python", "TensorFlow", "PyTorch", "Machine Learning", "Deep Learning", "NLP"]
    },
    {
        "id": 6,
        "title": "Frontend Developer",
        "company": "User Experience Design",
        "location": "New York, NY",
        "description": "Create beautiful, responsive, and accessible web interfaces for our clients.",
        "required_skills": ["JavaScript", "React", "HTML", "CSS", "UI/UX", "Responsive Design"]
    },
    {
        "id": 7,
        "title": "Backend Developer",
        "company": "Server Solutions",
        "location": "Chicago, IL",
        "description": "Develop and maintain server-side applications and RESTful APIs.",
        "required_skills": ["Python", "Django", "Flask", "SQL", "API", "Database Design"]
    },
    {
        "id": 8,
        "title": "Mobile Developer",
        "company": "App Creations",
        "location": "Los Angeles, CA",
        "description": "Build engaging mobile applications for iOS and Android platforms.",
        "required_skills": ["Swift", "Kotlin", "React Native", "Mobile UI/UX", "API Integration"]
    },
    {
        "id": 9,
        "title": "Cloud Architect",
        "company": "CloudScale Solutions",
        "location": "Denver, CO",
        "description": "Design and implement robust, scalable cloud infrastructure for enterprise clients.",
        "required_skills": ["AWS", "Azure", "GCP", "Terraform", "Kubernetes", "Microservices", "Security"]
    },
    {
        "id": 10,
        "title": "AI Research Scientist",
        "company": "Cognitive Research Labs",
        "location": "Cambridge, MA",
        "description": "Conduct cutting-edge research in artificial intelligence and machine learning algorithms.",
        "required_skills": ["Python", "TensorFlow", "PyTorch", "Deep Learning", "Research", "PhD", "Mathematics"]
    }
]

def extract_document_features(text):
    """Extract document features using spaCy (as BERT alternative) or NLTK as fallback"""
    if not text:
        return []
    
    # Use spaCy if available (better quality)
    if BERT_LIKE_AVAILABLE:
        try:
            # Process text with spaCy
            doc = nlp(text)
            
            # Extract important entities and noun phrases
            entities = [ent.text for ent in doc.ents]
            noun_phrases = [chunk.text for chunk in doc.noun_chunks]
            
            # Combine features
            features = entities + noun_phrases
            
            # Clean and normalize
            features = [f.lower() for f in features if len(f) > 2]
            
            # Remove duplicates
            features = list(set(features))
            
            return features
        except Exception as e:
            logger.error(f"Error extracting document features with spaCy: {str(e)}")
            # Fall back to basic extraction
    
    # Basic extraction using NLTK or just word frequency
    try:
        # Convert to lowercase and tokenize
        text = text.lower()
        
        # Try to use NLTK if available
        try:
            tokens = word_tokenize(text)
            stop_list = set(stopwords.words('english'))
            words = [word for word in tokens if word.isalpha() and len(word) > 2 and word not in stop_list]
        except Exception:
            # Even more basic fallback
            words = [word for word in text.split() if len(word) > 2]
        
        # Count word frequency
        word_counts = {}
        for word in words:
            if word in word_counts:
                word_counts[word] += 1
            else:
                word_counts[word] = 1
        
        # Get top words by frequency
        sorted_words = sorted(word_counts.items(), key=lambda x: x[1], reverse=True)
        features = [word for word, count in sorted_words[:20]]
        
        return features
    except Exception as e:
        logger.error(f"Error extracting document features with fallback method: {str(e)}")
        return []

def calculate_semantic_similarity(text1, text2):
    """Calculate semantic similarity between two texts using TF-IDF and cosine similarity or fallback"""
    if not text1 or not text2:
        return 0
    
    # Use scikit-learn if available (better quality)
    if SPACY_AVAILABLE:
        try:
            # Create TF-IDF vectorizer
            vectorizer = TfidfVectorizer(stop_words='english')
            
            # Fit and transform
            tfidf_matrix = vectorizer.fit_transform([text1, text2])
            
            # Calculate cosine similarity
            similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
            
            # Convert to percentage
            return similarity * 100
        except Exception as e:
            logger.error(f"Error calculating semantic similarity with scikit-learn: {str(e)}")
            # Fall back to basic similarity
    
    # Basic similarity calculation - Jaccard similarity
    try:
        # Tokenize and clean texts
        text1 = text1.lower()
        text2 = text2.lower()
        
        # Try to use NLTK if available
        try:
            tokens1 = set(word_tokenize(text1))
            tokens2 = set(word_tokenize(text2))
            stop_list = set(stopwords.words('english'))
            words1 = {word for word in tokens1 if word.isalpha() and len(word) > 2 and word not in stop_list}
            words2 = {word for word in tokens2 if word.isalpha() and len(word) > 2 and word not in stop_list}
        except Exception:
            # Even more basic fallback
            words1 = {word for word in text1.split() if len(word) > 2}
            words2 = {word for word in text2.split() if len(word) > 2}
        
        # Calculate Jaccard similarity (intersection over union)
        if not words1 or not words2:
            return 0
            
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        # Convert to percentage
        return (len(intersection) / len(union)) * 100
    except Exception as e:
        logger.error(f"Error calculating semantic similarity with fallback method: {str(e)}")
        return 0

def calculate_skill_match(resume_skills, job_skills):
    """Calculate the match score between resume skills and job skills"""
    if not resume_skills or not job_skills:
        return 0
    
    # Normalize skills (lowercase)
    resume_skills_lower = [skill.lower() for skill in resume_skills]
    job_skills_lower = [skill.lower() for skill in job_skills]
    
    # Count matching skills
    matching_skills = [skill for skill in job_skills_lower if skill in resume_skills_lower]
    
    # Calculate match score
    if not job_skills_lower:
        return 0
    
    match_score = (len(matching_skills) / len(job_skills_lower)) * 100
    return round(match_score)

def get_experience_level(resume_data):
    """Estimate experience level from resume data"""
    experience = resume_data.get('experience', [])
    
    # Count total years of experience (simplified)
    total_years = 0
    for job in experience:
        date_range = job.get('date', '')
        # Look for year ranges like "2018 - 2021" or "2018 - Present"
        years = re.findall(r'20\d\d', date_range)
        if len(years) >= 2:
            try:
                start_year = int(years[0])
                end_year = int(years[1])
                total_years += (end_year - start_year)
            except (ValueError, IndexError):
                pass
        elif len(years) == 1 and 'present' in date_range.lower():
            try:
                import datetime
                start_year = int(years[0])
                current_year = datetime.datetime.now().year
                total_years += (current_year - start_year)
            except (ValueError, IndexError):
                pass
    
    # Determine experience level
    if total_years < 2:
        return "Entry-level"
    elif total_years < 5:
        return "Mid-level"
    else:
        return "Senior"

def get_relevant_industry(resume_data):
    """Determine relevant industry based on resume content"""
    # Extract text from experience
    experience_text = " ".join([job.get('description', '') + " " + job.get('title', '') 
                              for job in resume_data.get('experience', [])])
    
    # Define industry keywords
    industry_keywords = {
        "Technology": ["software", "tech", "IT", "information technology", "programming", "developer", "web"],
        "Finance": ["finance", "banking", "investment", "financial", "accounting", "bank"],
        "Healthcare": ["healthcare", "medical", "hospital", "clinical", "health", "patient"],
        "Marketing": ["marketing", "advertising", "market research", "branding", "digital marketing"],
        "Education": ["education", "teaching", "academic", "school", "university", "instructor"],
        "Manufacturing": ["manufacturing", "production", "assembly", "factory", "industrial"],
        "Retail": ["retail", "sales", "store", "customer service", "merchandising"]
    }
    
    # Count occurrences of industry keywords
    industry_counts = Counter()
    for industry, keywords in industry_keywords.items():
        for keyword in keywords:
            if keyword.lower() in experience_text.lower():
                industry_counts[industry] += 1
    
    # Return the industry with the most hits, default to Technology
    if industry_counts:
        return industry_counts.most_common(1)[0][0]
    return "Technology"

def get_job_recommendations(resume_data):
    """Get job recommendations based on parsed resume data with BERT-like semantic matching"""
    try:
        # Extract skills from resume
        resume_skills = resume_data.get('skills', [])
        
        # Prepare resume text for semantic matching
        resume_text = ""
        if resume_data.get('summary'):
            resume_text += resume_data.get('summary') + " "
            
        # Add experience descriptions
        for exp in resume_data.get('experience', []):
            if exp.get('description'):
                resume_text += exp.get('description') + " "
            if exp.get('title'):
                resume_text += exp.get('title') + " "
                
        # Add skills
        resume_text += " ".join(resume_skills)
        
        # Calculate match scores for each job
        job_matches = []
        for job in SAMPLE_JOB_POSTINGS:
            # Traditional skill matching
            skill_match = calculate_skill_match(resume_skills, job['required_skills'])
            
            # Semantic matching score
            job_text = job['title'] + " " + job['description'] + " " + " ".join(job['required_skills'])
            semantic_score = 0
            
            if BERT_LIKE_AVAILABLE:
                semantic_score = calculate_semantic_similarity(resume_text, job_text)
                
            # Combined score (70% skill match, 30% semantic match)
            if BERT_LIKE_AVAILABLE:
                combined_score = (skill_match * 0.7) + (semantic_score * 0.3)
            else:
                combined_score = skill_match
            
            # Calculate matching/missing skills
            matching_skills = [skill for skill in job['required_skills'] 
                              if skill.lower() in [s.lower() for s in resume_skills]]
            missing_skills = [skill for skill in job['required_skills'] 
                             if skill.lower() not in [s.lower() for s in resume_skills]]
            
            # Extract important keywords for this job (BERT-like feature extraction)
            job_keywords = extract_document_features(job_text)[:5] if BERT_LIKE_AVAILABLE else []
            
            # Add job with match score to the list
            job_matches.append({
                'id': job['id'],
                'title': job['title'],
                'company': job['company'],
                'location': job['location'],
                'description': job['description'],
                'match_score': round(combined_score),
                'skill_match': skill_match,  # Original skill match score
                'semantic_score': round(semantic_score) if BERT_LIKE_AVAILABLE else 0,  # Semantic match score
                'matching_skills': matching_skills,
                'missing_skills': missing_skills,
                'key_job_requirements': job_keywords  # BERT-like extracted features
            })
        
        # Sort by match score (descending)
        job_matches.sort(key=lambda x: x['match_score'], reverse=True)
        
        # Add experience level and industry insights
        experience_level = get_experience_level(resume_data)
        relevant_industry = get_relevant_industry(resume_data)
        
        # Get resume keywords using BERT-like extraction
        resume_keywords = extract_document_features(resume_text)[:10] if BERT_LIKE_AVAILABLE else []
        
        # Return top matches and insights
        return {
            'jobs': job_matches[:5],  # Return top 5 matches
            'insights': {
                'experience_level': experience_level,
                'relevant_industry': relevant_industry,
                'top_skills': resume_skills[:5] if resume_skills else [],
                'skill_count': len(resume_skills),
                'using_enhanced_matching': BERT_LIKE_AVAILABLE,
                'extracted_keywords': resume_keywords
            }
        }
    
    except Exception as e:
        logger.error(f"Error generating job recommendations: {str(e)}")
        # Return empty results on error
        return {
            'jobs': [],
            'insights': {
                'experience_level': 'Unknown',
                'relevant_industry': 'Unknown',
                'top_skills': [],
                'skill_count': 0,
                'using_enhanced_matching': False,
                'extracted_keywords': []
            }
        }
