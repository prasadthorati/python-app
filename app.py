from flask import Flask, request, render_template, redirect, url_for
import os
import openai
from docx import Document
import PyPDF2
from io import BytesIO
import re

app = Flask(__name__)

def extract_text_from_pdf(file_stream):
    reader = PyPDF2.PdfReader(file_stream)
    text = ''
    for page in reader.pages:
        text += page.extract_text()
    return text

def extract_text_from_docx(file_stream):
    doc = Document(file_stream)
    text = ''.join(para.text for para in doc.paragraphs)
    return text

def extract_text(file):
    file_stream = BytesIO()
    file.save(file_stream)
    file_stream.seek(0)
    if file.filename.endswith('.pdf'):
        return extract_text_from_pdf(file_stream)
    elif file.filename.endswith('.docx'):
        return extract_text_from_docx(file_stream)
    else:
        return "Unsupported file format"
    

def parse_response(text):
    parts = text.split('. Key points: ')
    score = parts[0].strip()
    key_points = parts[1].strip() if len(parts) > 1 else "No key points provided."
    return score, key_points

def extract_score(text):
    # Regular expression to find patterns like "9/10"
    match = re.search(r'\b\d+/\d+\b', text)
    if match:
        score = match.group()  # This will be '9/10' if found
        # Remove the score from the text and return both
        text_without_score = re.sub(r'\b\d+/\d+\b', '', text).strip()
        return score, text_without_score
    else:
        return None, text  # No score found, return None and original text

# def parse_score_and_justification(text):
#     # Assuming the format always starts with "Candidate Score: <score> Justification: <justification>"
#     if "Justification:" in text:
#         parts = text.split("Justification:", 1)  # Split only on the first occurrence
#         score = parts[0].strip()
#         justification = parts[1].strip() if len(parts) > 1 else "No justification provided."
#     else:
#         score = "No score provided."
#         justification = "No justification provided."
#     return score, justification

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        cv_file = request.files.get('cv')
        job_description = request.form.get('jobDescription')
        
        if not cv_file or not job_description:
            return render_template('index.html', error="Please upload a CV and provide a job description.")

        if not cv_file.filename.endswith('.docx') and not cv_file.filename.endswith('.pdf'):
            return render_template('index.html', error="Unsupported file format.")

        cv_text = extract_text(cv_file)

        # Setup OpenAI key
        openai.api_key = os.getenv("OPENAI_API_KEY")

        # Updated API call for OpenAI
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an AI that assesses the suitability of candidates for job roles based on their CVs. Rate the candidate's suitability on a scale of 1 to 10 and provide key points justifying your score."},
                {"role": "user", "content": f"Candidate's CV Summary:\n{cv_text}\n\nJob Description:\n{job_description}"}
            ]
        )

        result = response['choices'][0]['message']['content']
        score, justification = extract_score(result)
        return render_template('index.html', score=score, justification=justification)

    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
