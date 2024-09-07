import os
from flask import Flask, request, redirect, url_for, render_template, send_from_directory, flash

app = Flask(__name__)
app.secret_key = "supersecretkey"

# Map waar geüploade bestanden worden opgeslagen
UPLOAD_FOLDER = 'files'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Maximaal toegestane bestandsgrootte: 50 GB
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024 * 1024  # 50 GB in bytes

@app.errorhandler(413)
def file_too_large(error):
    flash('Bestand is te groot. De maximale toegestane grootte is 50 GB.')
    return redirect(url_for('index'))

# Homepage voor het uploaden, weergeven en verwijderen van bestanden
@app.route('/')
def index():
    files = os.listdir(app.config['UPLOAD_FOLDER'])
    return render_template('index.html', files=files)

# Route om bestanden te uploaden
@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        flash('No Files Selected')
        return redirect(url_for('index'))

    file = request.files['file']
    if file.filename == '':
        flash('No Files Uploaded')
        return redirect(url_for('index'))

    if file:
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], file.filename))
        flash('Uploaded Sucessfully')
        return redirect(url_for('index'))

# Route om bestanden te downloaden
@app.route('/files/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# Route om bestanden te verwijderen
@app.route('/delete/<filename>', methods=['POST'])
def delete_file(filename):
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if os.path.exists(file_path):
        os.remove(file_path)
        flash(f'File {filename} Deleted')
    else:
        flash(f'File {filename} Not Found')
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)