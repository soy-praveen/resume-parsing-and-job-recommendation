"""
ChatGPT integration service for the resume analyzer application.
This module handles the integration with OpenAI's API to provide
intelligent responses to user queries about career development,
skill improvement, and job search advice.
"""

import os
import logging
import json
from openai import OpenAI

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize the OpenAI client
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

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
        # Create a prompt with context if available
        system_prompt = "You are a helpful AI career assistant providing advice on job skills, resume building, and career development."
        
        if context:
            # Add resume and job context if available
            skills_context = ""
            if 'skills' in context and context['skills']:
                skills_context = "User's skills: " + ", ".join(context['skills'])
            
            missing_skills_context = ""
            if 'missing_skills' in context and context['missing_skills']:
                missing_skills_context = "Skills the user needs to develop: " + ", ".join(context['missing_skills'])
            
            job_title_context = ""
            if 'job_title' in context and context['job_title']:
                job_title_context = f"Job user is interested in: {context['job_title']}"
            
            system_prompt += f"\n\n{skills_context}\n{missing_skills_context}\n{job_title_context}"
            
            system_prompt += "\n\nProvide specific, actionable advice based on the user's profile and their target job."
        
        # Call the OpenAI API
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": query}
            ],
            max_tokens=300,
            temperature=0.7
        )
        
        # Extract and return the generated text
        return response.choices[0].message.content
        
    except Exception as e:
        logger.error(f"Error generating ChatGPT response: {str(e)}")
        return "I'm sorry, I couldn't process your question. Please try again or ask a different question."

def is_api_key_valid():
    """Check if the OpenAI API key is valid and working"""
    try:
        # Make a minimal API call to verify the key is working
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "user", "content": "Hello"}
            ],
            max_tokens=5
        )
        return True
    except Exception as e:
        logger.error(f"API key validation error: {str(e)}")
        return False