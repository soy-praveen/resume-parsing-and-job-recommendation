# This file is not being used in the current implementation
# We're not using a database for this application, but keeping this
# file to maintain the suggested structure

class Resume:
    """Class to represent a parsed resume"""
    def __init__(self, name="", email="", phone="", skills=None, 
                 education=None, work_experience=None, summary=""):
        self.name = name
        self.email = email
        self.phone = phone
        self.skills = skills or []
        self.education = education or []
        self.work_experience = work_experience or []
        self.summary = summary
    
    def to_dict(self):
        """Convert the resume object to a dictionary"""
        return {
            'name': self.name,
            'email': self.email,
            'phone': self.phone,
            'skills': self.skills,
            'education': self.education,
            'work_experience': self.work_experience,
            'summary': self.summary
        }


class JobPosting:
    """Class to represent a job posting"""
    def __init__(self, title="", company="", location="", 
                 description="", required_skills=None, match_score=0):
        self.title = title
        self.company = company
        self.location = location
        self.description = description
        self.required_skills = required_skills or []
        self.match_score = match_score
    
    def to_dict(self):
        """Convert the job posting object to a dictionary"""
        return {
            'title': self.title,
            'company': self.company,
            'location': self.location,
            'description': self.description,
            'required_skills': self.required_skills,
            'match_score': self.match_score
        }
