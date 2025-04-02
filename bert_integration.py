"""
BERT-based model integration for improved resume parsing and job matching
"""
import logging
import re
import numpy as np
from typing import List, Dict, Any, Tuple

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Flag to determine if we can use the BERT model
try:
    from sentence_transformers import SentenceTransformer
    BERT_AVAILABLE = True
    logger.info("BERT model is available and will be used for enhanced matching")
    
    # Load the BERT model for embeddings
    try:
        model = SentenceTransformer('paraphrase-MiniLM-L6-v2')  # Using a smaller model for efficiency
        logger.info("Successfully loaded BERT model: paraphrase-MiniLM-L6-v2")
    except Exception as e:
        logger.error(f"Failed to load BERT model: {str(e)}")
        BERT_AVAILABLE = False
        
except ImportError:
    BERT_AVAILABLE = False
    logger.warning("BERT model not available. Using fallback similarity methods")


def get_bert_embeddings(texts: List[str]) -> np.ndarray:
    """
    Get BERT embeddings for a list of texts
    
    Args:
        texts: List of text strings
        
    Returns:
        Numpy array of embeddings
    """
    if not BERT_AVAILABLE or not texts:
        return np.array([])
    
    try:
        # Generate embeddings
        embeddings = model.encode(texts)
        return embeddings
    except Exception as e:
        logger.error(f"Error generating BERT embeddings: {str(e)}")
        return np.array([])


def calculate_semantic_similarity(resume_text: str, job_text: str) -> float:
    """
    Calculate semantic similarity between resume and job description using BERT
    
    Args:
        resume_text: Text from resume
        job_text: Text from job description
        
    Returns:
        Similarity score (0-100)
    """
    if not BERT_AVAILABLE:
        # Fallback to simple keyword matching
        return 0
    
    try:
        # Get embeddings
        embeddings = get_bert_embeddings([resume_text, job_text])
        
        if len(embeddings) < 2:
            return 0
        
        # Calculate cosine similarity
        resume_embedding = embeddings[0]
        job_embedding = embeddings[1]
        
        similarity = cosine_similarity(resume_embedding, job_embedding)
        
        # Convert to percentage
        return similarity * 100
    except Exception as e:
        logger.error(f"Error calculating semantic similarity: {str(e)}")
        return 0


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """
    Calculate cosine similarity between two vectors
    
    Args:
        a: First vector
        b: Second vector
        
    Returns:
        Cosine similarity score (0-1)
    """
    if len(a) == 0 or len(b) == 0:
        return 0
    
    dot_product = np.dot(a, b)
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    
    if norm_a == 0 or norm_b == 0:
        return 0
    
    return dot_product / (norm_a * norm_b)


def extract_keywords(text: str, max_keywords: int = 20) -> List[str]:
    """
    Extract important keywords from text
    
    Args:
        text: Input text
        max_keywords: Maximum number of keywords to extract
        
    Returns:
        List of extracted keywords
    """
    # Simple implementation - in practice, you'd use BERT or TF-IDF here
    # Remove special characters and convert to lowercase
    text = re.sub(r'[^\w\s]', ' ', text.lower())
    
    # Split into words
    words = text.split()
    
    # Remove common stop words
    stop_words = {'a', 'an', 'the', 'and', 'or', 'but', 'is', 'are', 'was', 'were', 
                 'be', 'been', 'being', 'in', 'on', 'at', 'to', 'for', 'with', 'by',
                 'about', 'against', 'between', 'into', 'through', 'during', 'before',
                 'after', 'above', 'below', 'from', 'up', 'down', 'of', 'off', 'over',
                 'under', 'again', 'further', 'then', 'once', 'here', 'there', 'when',
                 'where', 'why', 'how', 'all', 'any', 'both', 'each', 'few', 'more',
                 'most', 'other', 'some', 'such', 'no', 'nor', 'not', 'only', 'own',
                 'same', 'so', 'than', 'too', 'very', 'can', 'will', 'just', 'should',
                 'now'}
    
    filtered_words = [word for word in words if word not in stop_words and len(word) > 2]
    
    # Count word frequency
    word_counts = {}
    for word in filtered_words:
        if word in word_counts:
            word_counts[word] += 1
        else:
            word_counts[word] = 1
    
    # Sort by frequency
    sorted_words = sorted(word_counts.items(), key=lambda x: x[1], reverse=True)
    
    # Return top keywords
    keywords = [word for word, count in sorted_words[:max_keywords]]
    
    return keywords


def get_enhanced_job_matches(resume_data: Dict[str, Any], job_postings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Get enhanced job matches using BERT-based semantic similarity
    
    Args:
        resume_data: Parsed resume data
        job_postings: List of job posting dictionaries
        
    Returns:
        List of job matches with similarity scores
    """
    # Prepare resume text - combine skills, experience, and summary
    resume_skills = ' '.join(resume_data.get('skills', []))
    resume_experience = ' '.join([exp.get('description', '') + ' ' + exp.get('title', '') 
                               for exp in resume_data.get('experience', [])])
    resume_summary = resume_data.get('summary', '')
    
    resume_text = f"{resume_summary} {resume_experience} {resume_skills}"
    
    job_matches = []
    
    for job in job_postings:
        # Prepare job text
        job_skills = ' '.join(job.get('required_skills', []))
        job_description = job.get('description', '')
        job_title = job.get('title', '')
        
        job_text = f"{job_title} {job_description} {job_skills}"
        
        # Calculate traditional skill matching score
        skill_match_score = calculate_skill_match(resume_data.get('skills', []), job.get('required_skills', []))
        
        # Calculate semantic similarity if BERT is available
        semantic_score = 0
        if BERT_AVAILABLE:
            semantic_score = calculate_semantic_similarity(resume_text, job_text)
        
        # Combine scores (70% skill match, 30% semantic similarity)
        # If BERT is not available, use only skill match score
        if BERT_AVAILABLE:
            combined_score = (skill_match_score * 0.7) + (semantic_score * 0.3)
        else:
            combined_score = skill_match_score
        
        # Calculate matching and missing skills
        matching_skills = [skill for skill in job.get('required_skills', []) 
                          if skill.lower() in [s.lower() for s in resume_data.get('skills', [])]]
        
        missing_skills = [skill for skill in job.get('required_skills', []) 
                         if skill.lower() not in [s.lower() for s in resume_data.get('skills', [])]]
        
        # Add job to matches
        job_matches.append({
            'id': job.get('id'),
            'title': job.get('title', ''),
            'company': job.get('company', ''),
            'location': job.get('location', ''),
            'description': job.get('description', ''),
            'match_score': round(combined_score),
            'matching_skills': matching_skills,
            'missing_skills': missing_skills,
            'semantic_score': round(semantic_score) if BERT_AVAILABLE else 0
        })
    
    # Sort by combined score
    job_matches.sort(key=lambda x: x['match_score'], reverse=True)
    
    return job_matches


def calculate_skill_match(resume_skills: List[str], job_skills: List[str]) -> float:
    """
    Calculate match score between resume skills and job skills
    
    Args:
        resume_skills: List of skills from resume
        job_skills: List of skills required for job
        
    Returns:
        Match score as percentage (0-100)
    """
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