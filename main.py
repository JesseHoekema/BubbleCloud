import os
from flask import Flask, request, redirect, url_for, render_template, send_from_directory, flash, session
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "supersecretkey"

# File to store credentials (username, password)
CREDENTIALS_FILE = 'credentials.txt'

# Folder where uploaded files are stored
UPLOAD_FOLDER = 'files'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024 * 1024  # 50 GB in bytes

# Helper function to check if account exists
def account_exists():
    return os.path.exists(CREDENTIALS_FILE)

# Helper function to read credentials
def read_credentials():
    if account_exists():
        with open(CREDENTIALS_FILE, 'r') as f:
            credentials = f.read().strip().split(',')
            return credentials
    return None

# Route: Home (Requires Login)
@app.route('/')
def index():
    # If no account exists, redirect to register page
    if not account_exists():
        flash('No account found. Please create an account.')
        return redirect(url_for('register'))

    # If not logged in, redirect to login page
    if not session.get('logged_in'):
        flash('Please log in to access the page.')
        return redirect(url_for('login'))

    # Display uploaded files if logged in
    files = os.listdir(app.config['UPLOAD_FOLDER'])
    return render_template('index.html', files=files)

# Route: Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        credentials = read_credentials()

        if credentials and username == credentials[0] and password == credentials[1]:
            session['logged_in'] = True
            flash('Login successful!')
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password.')
    
    return render_template('login.html')

# Route: Register (Create Account)
@app.route('/register', methods=['GET', 'POST'])
def register():
    if account_exists():
        flash('Account already exists. Please log in.')
        return redirect(url_for('login'))

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Save credentials to file
        with open(CREDENTIALS_FILE, 'w') as f:
            f.write(f"{username},{password}")
        flash('Account created successfully. Please log in.')
        return redirect(url_for('login'))
    
    return render_template('register.html')

# Route: Upload File (Requires Login)
@app.route('/upload', methods=['POST'])
def upload_file():
    if not session.get('logged_in'):
        flash('Please log in to upload files.')
        return redirect(url_for('login'))

    if 'file' not in request.files:
        flash('No file selected for uploading')
        return redirect(url_for('index'))

    file = request.files['file']
    if file.filename == '':
        flash('No file selected')
        return redirect(url_for('index'))

    if file:
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        flash('File uploaded successfully!')
        return redirect(url_for('index'))

# Route: Download File (Requires Login)
@app.route('/files/<filename>')
def uploaded_file(filename):
    if not session.get('logged_in'):
        flash('Please log in to access files.')
        return redirect(url_for('login'))

    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# Route: Delete File (Requires Login)
@app.route('/delete/<filename>', methods=['POST'])
def delete_file(filename):
    if not session.get('logged_in'):
        flash('Please log in to delete files.')
        return redirect(url_for('login'))

    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if os.path.exists(file_path):
        os.remove(file_path)
        flash(f'File {filename} deleted successfully!')
    else:
        flash(f'File {filename} not found.')
    
    return redirect(url_for('index'))

# Route: Logout
@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    flash('Logged out successfully.')
    return redirect(url_for('login'))

# Error handler: File too large
@app.errorhandler(413)
def file_too_large(error):
    flash('File is too large. Maximum allowed size is 50 GB.')
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
