import os
import logging
import uuid
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
import werkzeug.utils
from werkzeug.utils import secure_filename
from resume_parser import extract_text_from_resume, parse_resume
from job_recommender import get_job_recommendations

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Create Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "default-dev-secret-key")

# Configure upload folder
UPLOAD_FOLDER = '/tmp/resume_uploads'
ALLOWED_EXTENSIONS = {'pdf', 'docx'}

# Create upload folder if it doesn't exist
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    """Render the home page"""
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_resume():
    """Handle resume upload and processing"""
    # Check if a file was submitted
    if 'resume' not in request.files:
        flash('No file part', 'danger')
        return redirect(request.url)
    
    file = request.files['resume']
    
    # Check if user didn't select a file
    if file.filename == '':
        flash('No file selected', 'danger')
        return redirect(request.url)
    
    # Check if file is allowed
    if file and allowed_file(file.filename):
        # Generate a unique filename to prevent overwrites
        original_filename = secure_filename(file.filename)
        file_extension = original_filename.rsplit('.', 1)[1].lower()
        unique_filename = f"{uuid.uuid4().hex}.{file_extension}"
        
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(filepath)
        
        try:
            # Extract text from the resume file
            extracted_text = extract_text_from_resume(filepath, file_extension)
            
            if not extracted_text:
                flash('Could not extract text from the uploaded file', 'danger')
                return redirect(url_for('index'))
            
            # Parse the resume using NLP
            parsed_data = parse_resume(extracted_text)
            
            # Get job recommendations based on the parsed resume
            job_recommendations = get_job_recommendations(parsed_data)
            
            # Store the results in the session
            session['parsed_data'] = parsed_data
            session['job_recommendations'] = job_recommendations
            
            # Redirect to results page
            return redirect(url_for('show_results'))
            
        except Exception as e:
            logging.error(f"Error processing resume: {str(e)}")
            flash(f'Error processing resume: {str(e)}', 'danger')
            return redirect(url_for('index'))
    else:
        flash(f'Unsupported file format. Please upload a PDF or DOCX file.', 'danger')
        return redirect(url_for('index'))

@app.route('/results')
def show_results():
    """Display the parsed resume data and job recommendations"""
    # Check if we have parsed data in the session
    if 'parsed_data' not in session or 'job_recommendations' not in session:
        flash('No resume data found. Please upload a resume first.', 'warning')
        return redirect(url_for('index'))
    
    parsed_data = session['parsed_data']
    job_recommendations = session['job_recommendations']
    
    return render_template('results.html', 
                          parsed_data=parsed_data,
                          job_recommendations=job_recommendations)

# Error handlers
@app.errorhandler(404)
def page_not_found(e):
    return render_template('index.html'), 404

@app.errorhandler(413)
def file_too_large(e):
    flash('The file is too large. Maximum file size is 16MB.', 'danger')
    return redirect(url_for('index'))

@app.errorhandler(500)
def internal_server_error(e):
    flash('An internal server error occurred. Please try again later.', 'danger')
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
