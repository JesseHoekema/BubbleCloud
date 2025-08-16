from flask import Flask, jsonify, render_template, request, redirect, url_for, session, flash, send_from_directory
import os
import json
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from flask_toastr import Toastr
import shutil

app = Flask(__name__)
app.secret_key = 'secret_app_key'
toastr = Toastr(app)

APP_FILES_DIR = "app-files"
ACCOUNT_FILE = os.path.join(APP_FILES_DIR, "account.json")
UPLOAD_FOLDER = os.path.join(APP_FILES_DIR, "files")
RECENT_FILES = os.path.join(APP_FILES_DIR, "recent_files.json")
FOLDERS_JSON = os.path.join(APP_FILES_DIR, "folders.json")

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

CATEGORIES = {
    "Documents": [".pdf", ".doc", ".docx", ".txt", ".xls", ".xlsx", ".ppt", ".pptx"],
    "Videos": [".mp4", ".avi", ".mov", ".mkv", ".wmv", ".flv"],
    "Images": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".webp", ".svg"],
    "Music": [".mp3", ".wav", ".flac", ".aac", ".ogg", ".m4a"]
}

def load_account():
    if os.path.exists(ACCOUNT_FILE):
        with open(ACCOUNT_FILE, "r") as f:
            return json.load(f)
    return None

def save_account(account_data):
    with open(ACCOUNT_FILE, "w") as f:
        json.dump(account_data, f)

def format_size(size_bytes):
    units = ["B", "KB", "MB", "GB", "TB"]
    
    try:
        # Convert to float, treat None or invalid values as 0
        size = float(size_bytes or 0)
    except (ValueError, TypeError):
        size = 0

    index = 0
    while size >= 1024 and index < len(units) - 1:
        size /= 1024
        index += 1

    return f"{size:.2f} {units[index]}"


def get_file_type(filename):
    ext = os.path.splitext(filename.lower())[1]
    for category, extensions in CATEGORIES.items():
        if ext in extensions:
            return category
    return "Other"

def load_recent_files():
    if os.path.exists(RECENT_FILES):
        with open(RECENT_FILES, "r") as f:
            data = json.load(f)
            # convert list back to dict keyed by "name"
            if isinstance(data, list):
                return {item["name"]: {"last_opened": item["last_opened"], "size_bytes": item["size_bytes"]} for item in data}
            return data
    return {}

def save_recent_files(data):
    # data is dict keyed by filename, convert to list with "name" key
    list_data = [
        {"name": name, "last_opened": info.get("last_opened"), "size_bytes": info.get("size_bytes")}
        for name, info in data.items()
    ]
    with open(RECENT_FILES, "w") as f:
        json.dump(list_data, f, indent=2)

def get_storage_usage():
    usage_bytes = {cat: 0 for cat in CATEGORIES}
    usage_bytes["Other"] = 0

    for filename in os.listdir(UPLOAD_FOLDER):
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        if os.path.isfile(filepath):
            ext = os.path.splitext(filename)[1].lower()
            size_bytes = os.path.getsize(filepath)
            found = False
            for cat, exts in CATEGORIES.items():
                if ext in exts:
                    usage_bytes[cat] += size_bytes
                    found = True
                    break
            if not found:
                usage_bytes["Other"] += size_bytes

    total_bytes = sum(usage_bytes.values())
    # Format sizes to human readable strings
    usage = {cat: format_size(size) for cat, size in usage_bytes.items()}
    total = format_size(total_bytes)

    return usage, total

def get_files_info():
    folder = 'app-files/files'
    files = []

    for filename in os.listdir(folder):
        filepath = os.path.join(folder, filename)
        if os.path.isfile(filepath):
            stat = os.stat(filepath)
            files.append({
                "filename": filename,
                "size": stat.st_size,
                "created": stat.st_ctime  # creation time (Unix timestamp)
            })

    files.sort(key=lambda x: x["created"], reverse=True)

    for f in files:
        f.pop("created")

    return files

def load_folders():
    """Load folders.json, creating it if missing."""
    if not os.path.exists(FOLDERS_JSON):
        with open(FOLDERS_JSON, "w") as f:
            json.dump([], f, indent=2)
    with open(FOLDERS_JSON, "r") as f:
        return json.load(f)

def save_folders(data):
    with open(FOLDERS_JSON, "w") as f:
        json.dump(data, f, indent=2)
        
def get_category(filename):
    ext = os.path.splitext(filename)[1].lower()
    for category, extensions in CATEGORIES.items():
        if ext in extensions:
            return category
    return "Other"

def private_files():
    if not os.path.exists(ACCOUNT_FILE):
        return True
    
    try:
        with open(ACCOUNT_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, IOError):
        return True
    
    return data.get("private-files", True)

@app.context_processor
def inject_common_data():
    files = os.listdir(UPLOAD_FOLDER)
    usage, total = get_storage_usage()

    account = load_account()
    name = account.get("name") if account else None

    recent_files = load_recent_files()
    # Only keep files that actually exist and have a valid dict
    recent_files = {
        f: info if isinstance(info, dict) else {}
        for f, info in recent_files.items() if f in files
    }

    recent_sorted = sorted(
        recent_files.items(),
        key=lambda x: x[1].get("last_opened") or "",
        reverse=True
    )[:4]

    # Ensure size_bytes is never None
    recent_files_list = [
        {
            "name": f,
            "last_opened": info.get("last_opened"),
            "size_bytes": info.get("size_bytes") or 0
        }
        for f, info in recent_sorted
    ]

    four_files = recent_files_list
    files_info_four = get_files_info()[:4]

    return dict(
        files=files,
        categories=usage,
        total=total,
        recent_files=recent_files_list,
        name=name,
        four_files=four_files,
        files_info=files_info_four
    )


@app.route("/", methods=["GET"])
def home():
    account = load_account()
    if not account:
        return redirect(url_for("register"))
    
    if "user" in session:
        return redirect(url_for("dashboard"))
    
    return redirect(url_for("login"))

@app.route("/register", methods=["GET", "POST"])
def register():
    # if load_account():
    #     return redirect(url_for("login"))

    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"]
        encryption = request.form["encryption"]
        name = request.form["name"].strip()  # new

        if encryption == "hashed":
            password = generate_password_hash(password)

        save_account({
            "username": username,
            "password": password,
            "encrypted": (encryption == "hashed"),
            "name": name  
        })

        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    account = load_account()
    if not account:
        return redirect(url_for("register"))

    error = ""
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"]

        if username == account["username"]:
            if account["encrypted"]:
                if check_password_hash(account["password"], password):
                    session["user"] = username
                    return redirect(url_for("dashboard"))
                else:
                    error = "Invalid password"
            else:
                if password == account["password"]:
                    session["user"] = username
                    return redirect(url_for("dashboard"))
                else:
                    error = "Invalid password"
        else:
            error = "Invalid username"

    return render_template("login.html", error=error)

@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    if "user" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        if "file" not in request.files:
            flash("No file selected")
            return redirect(request.url)
        files = request.files.getlist("file")
        for file in files:
            if file and file.filename != "":
                file.save(os.path.join(UPLOAD_FOLDER, file.filename))
                flash("File uploaded successfully", "success")

    files = os.listdir(UPLOAD_FOLDER)
    usage, total = get_storage_usage()
    
    account = load_account()
    name = account.get("name") if account else None

    recent_files = load_recent_files()
    recent_files = {
        f: info if isinstance(info, dict) else {}
        for f, info in recent_files.items() if f in files
    }

    recent_sorted = sorted(
        recent_files.items(),
        key=lambda x: x[1].get("last_opened") or "",
        reverse=True
    )[:4]

    recent_files_list = []
    for f, info in recent_sorted:
        size = info.get("size_bytes") or 0
        try:
            size = float(size)
        except (TypeError, ValueError):
            size = 0

        recent_files_list.append({
            "name": f,
            "last_opened": info.get("last_opened") or "",
            "size_bytes": format_size(size),
            "type": get_file_type(f)
        })
    
    files_info_four = get_files_info()[:4]
    files_info_four = [
        {
            **file_info,
            "size_bytes": format_size(file_info.get("size") or file_info.get("size_bytes") or 0),
            "type": get_file_type(file_info.get("filename") or "")
        }
        for file_info in files_info_four
    ]

    all_folders_list = load_folders()
    folders_list = all_folders_list[:4][::-1]

    return render_template(
        "dashboard.html",
        total=total,
        recent_files=recent_files_list,
        name=name,
        files_info=files_info_four,
        active_page="dashboard",
        folders=folders_list,
    )

@app.route("/files/<filename>")
def uploaded_file(filename):
    if private_files():
        if "user" not in session:
            return redirect(url_for("login"))
        
    recent_files = load_recent_files()
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    file_size = os.path.getsize(file_path) if os.path.exists(file_path) else None

    recent_files[filename] = {
        "last_opened": datetime.utcnow().isoformat(),
        "size_bytes": file_size
    }

    save_recent_files(recent_files)
    return send_from_directory(UPLOAD_FOLDER, filename)

@app.route("/files")
def list_files():
    if "user" not in session:
        return redirect(url_for("login"))
    
    folders_list = load_folders()
    available_folders = [f["name"] for f in folders_list]

    def get_category(filename):
        ext = os.path.splitext(filename)[1].lower()
        for category, extensions in CATEGORIES.items():
            if ext in extensions:
                return category
        return "Others"

    files_info = []
    for filename in os.listdir(UPLOAD_FOLDER):
        file_path = os.path.join(UPLOAD_FOLDER, filename)

        # Skip directories, only include files
        if os.path.isfile(file_path):
            file_stat = os.stat(file_path)

            file_info = {
                "name": filename,
                "last_opened": datetime.fromtimestamp(file_stat.st_atime).isoformat(),
                "size_bytes": format_size(file_stat.st_size),
                "type": get_category(filename)
            }
            files_info.append(file_info)

    return render_template("files.html", files=files_info[::-1], active_page="files", available_folders=available_folders)

@app.route("/recents")
def recent_files():
    if "user" not in session:
        return redirect(url_for("login"))

    recent_files = load_recent_files()
    files_info = []

    def get_file_type(filename):
        ext = os.path.splitext(filename)[1].lower()
        for category, extensions in CATEGORIES.items():
            if ext in extensions:
                return category
        return "Other"

    for filename, info in recent_files.items():
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        if os.path.exists(file_path):
            files_info.append({
                "name": filename,
                "last_opened": info.get("last_opened"),
                "size_bytes": format_size(info.get("size_bytes")),
                "type": get_file_type(filename)
            })

    files_info.sort(key=lambda x: x["last_opened"], reverse=True)

    return render_template("recents.html", files=files_info[:20], active_page="recents")


@app.route("/delete/<filename>", methods=["POST"])
def delete_file(filename):
    if "user" not in session:
        return redirect(url_for("login"))

    file_path = os.path.join(UPLOAD_FOLDER, filename)
    if os.path.exists(file_path):
        os.remove(file_path)
        flash(f"File '{filename}' deleted successfully", "success")
    else:
        flash(f"File '{filename}' not found", "error")

    return redirect(url_for("list_files"))

@app.route("/search", methods=["GET"])
def search_files():
    
    if "user" not in session:
        return redirect(url_for("login"))

    query = request.args.get("query", "").strip()
    if not query:
        return redirect(url_for("list_files"))

    files_info = []
    for filename in os.listdir(UPLOAD_FOLDER):
        if query.lower() in filename.lower():
            file_path = os.path.join(UPLOAD_FOLDER, filename)
            if os.path.isfile(file_path):
                file_stat = os.stat(file_path)
                files_info.append({
                    "name": filename,
                    "last_opened": datetime.fromtimestamp(file_stat.st_atime).isoformat(),
                    "size_bytes": file_stat.st_size
                })

    return render_template("files.html", files=files_info, active_page="files")

@app.route("/settings", methods=["GET", "POST"])
def settings():
    if "user" not in session:
        return redirect(url_for("login"))

    account = load_account()

    return render_template("settings.html", account=account, active_page="settings")

@app.route("/api/settings/user", methods=["POST"])
def update_settings():
    if "user" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.json
    if not data or "name" not in data or "username" not in data:
        flash("Invalid input", "error")
        return jsonify({"error": "Invalid input"}), 400

    account = load_account()
    if not account:
        flash("Account not found", "error")
        return jsonify({"error": "Account not found"}), 404

    account["name"] = data["name"].strip()
    account["username"] = data["username"].strip()

    save_account(account)
    flash("Settings updated successfully", "success")
    return jsonify({"message": "Settings updated successfully"}), 200

@app.route("/api/settings/password", methods=["POST"])
def update_password():
    if "user" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.json
    if not data or "current_password" not in data or "new_password" not in data:
        flash("Invalid input", "error")
        return jsonify({"error": "Invalid input"}), 400

    account = load_account()
    if not account:
        flash("Account not found", "error")
        return jsonify({"error": "Account not found"}), 404

    if account["encrypted"]:
        if not check_password_hash(account["password"], data["current_password"]):
            flash("Current password is incorrect", "error")
            return jsonify({"error": "Current password is incorrect"}), 400
    else:
        if account["password"] != data["current_password"]:
            flash("Current password is incorrect", "error")
            return jsonify({"error": "Current password is incorrect"}), 400

    new_password = data["new_password"]
    if account["encrypted"]:
        account["password"] = generate_password_hash(new_password)
    else:
        account["password"] = new_password

    save_account(account)
    flash("Password updated successfully", "success")
    return jsonify({"success": "true", "message": "Password updated successfully"}), 200

@app.route("/api/settings/delete", methods=["POST"])
def delete_account():
    if "user" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    account = load_account()
    if not account:
        flash("Account not found", "error")
        return jsonify({"error": "Account not found"}), 404

    # Delete account file
    if os.path.exists(ACCOUNT_FILE):
        os.remove(ACCOUNT_FILE)

    # Delete uploaded files folder if it exists
    if os.path.exists(UPLOAD_FOLDER) and os.path.isdir(UPLOAD_FOLDER):
        shutil.rmtree(UPLOAD_FOLDER)

    # Delete folders JSON if it exists
    if os.path.exists(FOLDERS_JSON):
        os.remove(FOLDERS_JSON)

    # Recreate an empty upload folder to avoid FileNotFoundError in inject_common_data
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)

    # Clear session
    session.clear()

    flash("Account deleted successfully", "success")
    return jsonify({"success": True, "message": "Account deleted successfully"}), 200


@app.route("/folders")
def folders():
    if "user" not in session:
        return redirect(url_for("login"))

    folders_list = load_folders()[::-1]
    return render_template("folders.html", folders=folders_list, active_page="folders")

@app.route("/folders/<folder_name>")
def view_folder(folder_name):
    if "user" not in session:
        return redirect(url_for("login"))

    folders_list = load_folders()

    # Find the folder by exact name
    folder = next((f for f in folders_list if f["name"] == folder_name), None)

    if not folder:
        flash(f"Folder '{folder_name}' not found", "error")
        return redirect(url_for("folders"))

    return render_template("view_folder.html", folder=folder, active_page="folders", available_files=os.listdir(UPLOAD_FOLDER))


@app.route("/create-folder", methods=["POST"])
def create_folder():
    if "user" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    # Support both JSON and form submissions
    if request.is_json:
        data = request.get_json()
        folder_name = data.get("name")
    else:
        folder_name = request.form.get("name")

    if not folder_name:
        if request.is_json:
            return jsonify({"error": "Folder name is required"}), 400
        flash("Folder name is required!", "error")
        return redirect(request.referrer or url_for("dashboard"))

    folders_list = load_folders()

    if any(f["name"] == folder_name for f in folders_list):
        if request.is_json:
            return jsonify({"error": "Folder already exists"}), 400
        flash("Folder already exists!", "error")
        return redirect(request.referrer or url_for("dashboard"))

    folders_list.append({"name": folder_name, "files": []})
    save_folders(folders_list)

    flash(f"Folder '{folder_name}' created successfully!", "success")

    if request.is_json:
        return jsonify({"success": True, "folders": folders_list})
    return redirect(request.referrer or url_for("dashboard"))

@app.route("/add-files", methods=["POST"])
def add_files():
    if "user" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    if request.is_json:
        data = request.get_json()
        folder_name = data.get("folder")
        file_names = data.get("files", [])
    else:
        folder_name = request.form.get("folder") 
        file_name = request.form.get("file_name")
        file_names = [file_name] if file_name else []

    if not folder_name or not file_names:
        flash("Folder and file are required", "error")
        return redirect(url_for("folders"))

    folders_list = load_folders()
    folder = next((f for f in folders_list if f["name"] == folder_name), None)
    if not folder:
        flash("Folder not found", "error")
        return redirect(url_for("folders"))

    for file_name in file_names:
        file_path = os.path.join(UPLOAD_FOLDER, file_name)
        if not os.path.exists(file_path):
            size_readable = "0.00 B"
            category = get_category(file_name)
        else:
            size_readable = format_size(os.path.getsize(file_path))
            category = get_category(file_name)

        if not any(f["name"] == file_name for f in folder["files"]):
            folder["files"].append({
                "name": file_name,
                "size": size_readable,
                "type": category
            })

    save_folders(folders_list)
    
    if not request.is_json:
        return redirect(url_for("view_folder", folder_name=folder_name))


    flash(f"Successfully added '{file_name}' to '{folder_name}'", "success")
    return jsonify({"success": True, "folder": folder})


@app.route("/delete-folder", methods=["POST"])
def delete_folder():
    if "user" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json()
    folder_name = data.get("name")

    if not folder_name:
        return jsonify({"error": "Folder name is required"}), 400

    folders_list = load_folders()
    folder = next((f for f in folders_list if f["name"] == folder_name), None)

    if not folder:
        return jsonify({"error": "Folder not found"}), 404

    folders_list.remove(folder)
    save_folders(folders_list)

    flash(f"Successfully deleted: {folder_name}", "success")
    return jsonify({"success": True, "message": "Folder deleted successfully"})

@app.route("/delete-file-from-folder", methods=["POST"])
def delete_file_from_folder():
    if "user" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json() or request.form
    folder_name = data.get("folder")
    file_name = data.get("file_name")

    if not folder_name or not file_name:
        return jsonify({"error": "Folder and file are required"}), 400

    folders_list = load_folders()
    folder = next((f for f in folders_list if f["name"] == folder_name), None)
    if not folder:
        return jsonify({"error": "Folder not found"}), 404

    # Remove the file from the folder's files list
    original_count = len(folder["files"])
    folder["files"] = [f for f in folder["files"] if f["name"] != file_name]
    if len(folder["files"]) == original_count:
        return jsonify({"error": "File not found in folder"}), 404

    save_folders(folders_list)
    
    flash(f"File '{file_name}' deleted from folder '{folder_name}'", "success")

    return jsonify({"success": True, "folder": folder})

@app.route("/edit-folder-name", methods=["POST"])
def edit_folder_name():
    if "user" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json() or request.form
    old_name = data.get("old_name")
    new_name = data.get("new_name")

    if not old_name or not new_name:
        return jsonify({"error": "Both old and new folder names are required"}), 400

    folders_list = load_folders()
    folder = next((f for f in folders_list if f["name"] == old_name), None)
    if not folder:
        return jsonify({"error": "Folder not found"}), 404

    if any(f["name"] == new_name for f in folders_list):
        return jsonify({"error": "A folder with the new name already exists"}), 400

    folder["name"] = new_name
    save_folders(folders_list)
    
    flash("Folder edited successfully!", "success")

    return jsonify({"success": True, "folder": folder})


@app.route("/update-private-files", methods=["POST"])
def update_private_files():
    
    if "user" not in session:
        return "No Auth"
    
    data = request.get_json()
    if not data or "private-files" not in data:
        return jsonify({"error": "Missing 'private-files' in request"}), 400

    new_value = data["private-files"]

    if isinstance(new_value, str):
        if new_value.lower() == "false":
            new_value = False
        elif new_value.lower() == "true":
            new_value = True

    if os.path.exists(ACCOUNT_FILE):
        try:
            with open(ACCOUNT_FILE, "r", encoding="utf-8") as f:
                account_data = json.load(f)
        except (json.JSONDecodeError, IOError):
            account_data = {}
    else:
        account_data = {}

    account_data["private-files"] = new_value

    try:
        with open(ACCOUNT_FILE, "w", encoding="utf-8") as f:
            json.dump(account_data, f, indent=4)
    except IOError as e:
        return jsonify({"error": f"Failed to write to file: {str(e)}"}), 500

    return jsonify({"success": True, "private-files": new_value})

@app.route("/app-api/get-files")
def get_all_files():
    # Check session cookie
    user_in_session = "user" in session
    session_token = request.cookies.get("session")

    # Check Authorization header
    auth_header = request.headers.get("Authorization")
    header_token = None
    if auth_header and auth_header.startswith("Bearer "):
        header_token = auth_header.split(" ")[1]

    if not user_in_session and not session_token and not header_token:
        return redirect(url_for("login"))

    def get_category(filename):
        ext = os.path.splitext(filename)[1].lower()
        for category, extensions in CATEGORIES.items():
            if ext in extensions:
                return category
        return "Others"

    files_info = []
    for filename in os.listdir(UPLOAD_FOLDER):
        file_path = os.path.join(UPLOAD_FOLDER, filename)

        if os.path.isfile(file_path):
            file_stat = os.stat(file_path)
            files_info.append({
                "name": filename,
                "last_opened": datetime.fromtimestamp(file_stat.st_atime).isoformat(),
                "size_bytes": format_size(file_stat.st_size),
                "type": get_category(filename)
            })

    return render_template("/app/get.html", files=files_info[::-1])

@app.route("/app-api/upload-files", methods=["POST"])
def app_api_upload():
    if "user" not in session:
        return redirect(url_for("login"))
 
    if "file" not in request.files:
        return jsonify({"status": "error", "message": "No file provided"}), 400

    files = request.files.getlist("file")
    saved_files = []

    for file in files:
        if file and file.filename != "":
            filepath = os.path.join(UPLOAD_FOLDER, file.filename)
            file.save(filepath)
            saved_files.append(file.filename)

    if not saved_files:
        return jsonify({"status": "error", "message": "No valid files uploaded"}), 400

    return jsonify({
        "status": "success",
        "message": f"{len(saved_files)} file(s) uploaded successfully",
        "files": saved_files
    }), 200


@app.route("/app-api/login-page", methods=["GET", "POST"])
def app_api_login_page():
    account = load_account()
    if not account:
        return redirect(url_for("register"))

    error = ""
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"]

        if username == account["username"]:
            valid = False
            if account["encrypted"]:
                valid = check_password_hash(account["password"], password)
            else:
                valid = password == account["password"]

            if valid:
                session["user"] = username
                
                return redirect(url_for("return_session_token"))
            else:
                error = "Invalid password"
        else:
            error = "Invalid username"

        # Login failed → render login page with error
        return render_template("app/login.html", error=error, username=username)

    # GET request → render login page
    return render_template("app/login.html", error=error)

@app.route("/app-api/session-token")
def return_session_token():
    session_token = request.cookies.get("session")
    return jsonify({"session": session_token})


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(debug=True, port=5923)
