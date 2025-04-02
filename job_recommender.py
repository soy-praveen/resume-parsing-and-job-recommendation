import logging
import random
from collections import Counter

# Configure logging
logging.basicConfig(level=logging.DEBUG)

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
    }
]

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
        import re
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
    # Extract text from experience and education
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
    """Get job recommendations based on parsed resume data"""
    try:
        # Extract skills from resume
        resume_skills = resume_data.get('skills', [])
        
        # Calculate match scores for each job
        job_matches = []
        for job in SAMPLE_JOB_POSTINGS:
            match_score = calculate_skill_match(resume_skills, job['required_skills'])
            
            # Calculate matches for each job
            matching_skills = [skill for skill in job['required_skills'] 
                              if skill.lower() in [s.lower() for s in resume_skills]]
            missing_skills = [skill for skill in job['required_skills'] 
                             if skill.lower() not in [s.lower() for s in resume_skills]]
            
            # Add job with match score to the list
            job_matches.append({
                'id': job['id'],
                'title': job['title'],
                'company': job['company'],
                'location': job['location'],
                'description': job['description'],
                'match_score': match_score,
                'matching_skills': matching_skills,
                'missing_skills': missing_skills
            })
        
        # Sort by match score (descending)
        job_matches.sort(key=lambda x: x['match_score'], reverse=True)
        
        # Add experience level and industry insights
        experience_level = get_experience_level(resume_data)
        relevant_industry = get_relevant_industry(resume_data)
        
        # Return top matches and insights
        return {
            'jobs': job_matches[:5],  # Return top 5 matches
            'insights': {
                'experience_level': experience_level,
                'relevant_industry': relevant_industry,
                'top_skills': resume_skills[:5] if resume_skills else [],
                'skill_count': len(resume_skills)
            }
        }
    
    except Exception as e:
        logging.error(f"Error generating job recommendations: {str(e)}")
        # Return empty results on error
        return {
            'jobs': [],
            'insights': {
                'experience_level': 'Unknown',
                'relevant_industry': 'Unknown',
                'top_skills': [],
                'skill_count': 0
            }
        }
