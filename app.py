from __future__ import annotations

import secrets
import sqlite3
from pathlib import Path

from flask import (
    Flask,
    flash,
    redirect,
    render_template,
    request,
    send_from_directory,
    session,
    url_for,
)
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename

BASE_DIR = Path(__file__).resolve().parent
DATABASE_PATH = BASE_DIR / "app.db"
UPLOAD_FOLDER = BASE_DIR / "uploads"
ALLOWED_EXTENSIONS = {
    "txt",
    "pdf",
    "png",
    "jpg",
    "jpeg",
    "gif",
    "zip",
    "docx",
    "xlsx",
    "csv",
}

app = Flask(__name__)
app.config["SECRET_KEY"] = secrets.token_hex(16)
app.config["UPLOAD_FOLDER"] = str(UPLOAD_FOLDER)
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16MB


def get_db_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    UPLOAD_FOLDER.mkdir(exist_ok=True)
    with get_db_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL
            )
            """
        )
        conn.commit()


def is_allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def current_user_upload_path(username: str) -> Path:
    user_folder = UPLOAD_FOLDER / secure_filename(username)
    user_folder.mkdir(exist_ok=True)
    return user_folder


@app.route("/")
def index() -> str:
    if "user_id" not in session:
        return redirect(url_for("login"))
    return redirect(url_for("dashboard"))


@app.route("/register", methods=["GET", "POST"])
def register() -> str:
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        if len(username) < 4 or len(password) < 6:
            flash("Tên đăng nhập phải >= 4 ký tự và mật khẩu >= 6 ký tự.", "error")
            return render_template("register.html")

        password_hash = generate_password_hash(password)
        try:
            with get_db_connection() as conn:
                conn.execute(
                    "INSERT INTO users (username, password_hash) VALUES (?, ?)",
                    (username, password_hash),
                )
                conn.commit()
            flash("Đăng ký thành công! Hãy đăng nhập.", "success")
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            flash("Tên đăng nhập đã tồn tại.", "error")

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login() -> str:
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        with get_db_connection() as conn:
            user = conn.execute(
                "SELECT id, username, password_hash FROM users WHERE username = ?", (username,)
            ).fetchone()

        if user and check_password_hash(user["password_hash"], password):
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            flash("Đăng nhập thành công.", "success")
            return redirect(url_for("dashboard"))

        flash("Sai tài khoản hoặc mật khẩu.", "error")

    return render_template("login.html")


@app.route("/logout", methods=["POST"])
def logout() -> str:
    session.clear()
    flash("Bạn đã đăng xuất.", "success")
    return redirect(url_for("login"))


@app.route("/dashboard", methods=["GET", "POST"])
def dashboard() -> str:
    if "user_id" not in session:
        return redirect(url_for("login"))

    username = session["username"]
    user_folder = current_user_upload_path(username)

    if request.method == "POST":
        if "file" not in request.files:
            flash("Không tìm thấy tệp trong yêu cầu.", "error")
            return redirect(url_for("dashboard"))

        uploaded_file = request.files["file"]
        if uploaded_file.filename == "":
            flash("Bạn chưa chọn tệp.", "error")
            return redirect(url_for("dashboard"))

        if not is_allowed_file(uploaded_file.filename):
            flash("Định dạng tệp không được hỗ trợ.", "error")
            return redirect(url_for("dashboard"))

        filename = secure_filename(uploaded_file.filename)
        save_path = user_folder / filename
        uploaded_file.save(save_path)
        flash(f"Tải lên thành công: {filename}", "success")
        return redirect(url_for("dashboard"))

    files = sorted([p.name for p in user_folder.iterdir() if p.is_file()])
    return render_template("dashboard.html", files=files, username=username)


@app.route("/download/<path:filename>")
def download(filename: str):
    if "user_id" not in session:
        return redirect(url_for("login"))

    username = session["username"]
    user_folder = current_user_upload_path(username)
    safe_name = secure_filename(filename)
    return send_from_directory(user_folder, safe_name, as_attachment=True)


@app.errorhandler(413)
def file_too_large(_error):
    flash("Tệp quá lớn. Kích thước tối đa là 16MB.", "error")
    return redirect(url_for("dashboard"))


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000, debug=True)
