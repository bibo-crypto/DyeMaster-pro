import os

UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pdf_uploads")
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)