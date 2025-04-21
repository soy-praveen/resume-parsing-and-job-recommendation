"""
ChatGPT integration service for the resume analyzer application.
This module handles the integration with OpenAI's API to provide
intelligent responses to user queries about career development,
skill improvement, and job search advice.
"""

import os
import logging
from openai import OpenAI
import backoff

# Set up logging
logging.basicConfig(level=logging.DEBUG)  # Changed to DEBUG for more detailed logs
logger = logging.getLogger(__name__)

# Initialize the OpenAI client with environment variable
# Never hardcode API keys in your code
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# Add backoff decorator to handle rate limiting and transient errors
@backoff.on_exception(backoff.expo, 
                     (Exception),
                     max_tries=3)
def generate_chatgpt_response(query, context=None):
    """
    Generate a response from ChatGPT based on the user's query.
    
    Args:
        query (str): The user's question
        context (dict, optional): Additional context like resume data, job info, etc.
        
    Returns:
        str: The response from ChatGPT
    """
    try:
        # Create a system prompt with context if available
        system_prompt = "You are a helpful AI career assistant providing advice on job skills, resume building, and career development."
        
        if context:
            # Add resume and job context if available
            context_details = []
            
            if 'skills' in context and context['skills']:
                context_details.append("User's skills: " + ", ".join(context['skills']))
            
            if 'missing_skills' in context and context['missing_skills']:
                context_details.append("Skills the user needs to develop: " + ", ".join(context['missing_skills']))
            
            if 'job_title' in context and context['job_title']:
                context_details.append(f"Job user is interested in: {context['job_title']}")
                
            if 'experience' in context and context['experience']:
                experience_summary = []
                for exp in context['experience']:
                    if isinstance(exp, dict):
                        exp_str = f"{exp.get('title', 'Role')} at {exp.get('company', 'Company')}"
                        experience_summary.append(exp_str)
                context_details.append(f"User's experience: {'; '.join(experience_summary)}")
                
            if 'education' in context and context['education']:
                edu_summary = []
                for edu in context['education']:
                    if isinstance(edu, dict):
                        edu_str = f"{edu.get('degree', 'Degree')} from {edu.get('institution', 'Institution')}"
                        edu_summary.append(edu_str)
                context_details.append(f"User's education: {'; '.join(edu_summary)}")
            
            if context_details:
                system_prompt += "\n\n" + "\n".join(context_details)
            
            system_prompt += "\n\nProvide specific, actionable advice based on the user's profile and their target job."
        
        # Call the OpenAI API
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": query}
            ],
            max_tokens=500,
            temperature=0.7
        )
        
        # Extract and return the generated text
        return response.choices[0].message.content
        
    except Exception as e:
        logger.error(f"Error generating ChatGPT response: {str(e)}", exc_info=True)
        return "I'm sorry, I encountered an issue connecting to the AI service. Please try again in a moment."

def is_api_key_valid():
    """Check if the OpenAI API key is valid and working"""
    try:
        # Make a minimal API call to verify the key is working
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",  # Using a cheaper model for validation
            messages=[
                {"role": "user", "content": "Hello"}
            ],
            max_tokens=5
        )
        return True
    except Exception as e:
        logger.error(f"API key validation error: {str(e)}", exc_info=True)
        return False

# Example usage
if __name__ == "__main__":
    # Test the API connection
    if is_api_key_valid():
        print("API connection successful!")
    else:
        print("API connection failed. Please check your API key.")
        
    # Example query
    sample_query = "How can I improve my resume for a software engineer position?"
    sample_context = {
        "skills": ["Python", "JavaScript", "SQL"],
        "missing_skills": ["Docker", "Kubernetes"],
        "job_title": "Senior Software Engineer"
    }
    
    print("\nTesting query with context:")
    response = generate_chatgpt_response(sample_query, sample_context)
    print(f"Query: {sample_query}")
    print(f"Response: {response}")
