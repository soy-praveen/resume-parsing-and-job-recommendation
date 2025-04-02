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
client = OpenAI(api_key="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")

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
        try:
            # The newest OpenAI model is "gpt-4o" which was released May 13, 2024.
            # Do not change this unless explicitly requested by the user
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": query}
                ],
                max_tokens=300,
                temperature=0.7
            )
            
            # Extract and return the generated text
            return response.choices[0].message.content
        except Exception as api_error:
            logger.error(f"API call error: {str(api_error)}")
            
            # If the API call fails, use the fallback responses
            return generate_fallback_response(query, context)
        
    except Exception as e:
        logger.error(f"Error generating ChatGPT response: {str(e)}")
        return "I'm sorry, I couldn't process your question. Please try again or ask a different question."

def generate_fallback_response(query, context=None):
    """
    Generate a fallback response when the API is unavailable
    
    Args:
        query (str): The user's question
        context (dict, optional): Additional context
        
    Returns:
        str: A fallback response
    """
    query_lower = query.lower()
    
    # Prepare skills information from context
    skills_text = ""
    if context and 'skills' in context and context['skills']:
        skills_text = ", ".join(context['skills'])
    
    missing_skills_text = ""
    if context and 'missing_skills' in context and context['missing_skills']:
        missing_skills_text = ", ".join(context['missing_skills'])
    
    job_title = ""
    if context and 'job_title' in context and context['job_title']:
        job_title = context['job_title']
    
    # Check for different types of questions and provide appropriate responses
    if any(keyword in query_lower for keyword in ['resume', 'cv', 'improve']):
        skills_advice = ""
        if skills_text:
            skills_advice = " Include these skills in your resume: " + skills_text
        return "To improve your resume, focus on quantifying your achievements and highlighting relevant skills for your target roles. Use action verbs and ensure your experience demonstrates your capabilities clearly." + skills_advice
    
    elif any(keyword in query_lower for keyword in ['skill', 'learn', 'develop']):
        if missing_skills_text:
            return "Based on your profile, I recommend focusing on developing these key skills: " + missing_skills_text + ". You can learn them through online courses on platforms like Coursera, Udemy, or through hands-on projects."
        else:
            return "To develop your skills, consider taking online courses, working on personal projects, contributing to open source, or obtaining relevant certifications in your field."
    
    elif any(keyword in query_lower for keyword in ['interview', 'prep', 'question']):
        skills_advice = ""
        if skills_text:
            skills_advice = " Focus on how you have applied these skills: " + skills_text
        return "Prepare for interviews by researching the company, practicing common questions, and preparing examples that demonstrate your skills and experience." + skills_advice
    
    elif any(keyword in query_lower for keyword in ['job', 'search', 'find', 'application']):
        return "For an effective job search, update your LinkedIn profile, set up job alerts on major platforms, network with professionals in your target field, and tailor each application to the specific role and company."
    
    elif any(keyword in query_lower for keyword in ['salary', 'negotiate', 'offer']):
        return "When negotiating salary, research industry standards, highlight your unique value, consider the total compensation package including benefits, and practice your negotiation approach beforehand."
    
    elif any(keyword in query_lower for keyword in ['career', 'path', 'switch', 'change']):
        return "For a successful career change, identify transferable skills, fill knowledge gaps with targeted learning, network with professionals in your desired field, and consider starting with hybrid roles that bridge your current and target careers."
    
    else:
        # Generic response for other questions
        return "As a career assistant, I can help with resume optimization, job search strategies, skill development, interview preparation, and career planning. Could you specify which aspect you need help with?"

def is_api_key_valid():
    """Check if the OpenAI API key is valid and working"""
    try:
        # Make a minimal API call to verify the key is working
        # The newest OpenAI model is "gpt-4o" which was released May 13, 2024.
        # Do not change this unless explicitly requested by the user
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "user", "content": "Hello"}
            ],
            max_tokens=5
        )
        return True
    except Exception as e:
        logger.error(f"API key validation error: {str(e)}")
        return False
