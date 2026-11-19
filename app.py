from flask import (
    Flask, render_template, request,
    redirect, url_for, session, flash
)
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import os

app = Flask(__name__)
app.secret_key = "gramfin_secret_key"

DATABASE = "gramfin.db"


# Database connection
def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


# Create database and users table
def create_database():
    conn = get_db_connection()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()


# Home page
@app.route("/")
def home():
    return render_template("index.html")


# Registration
@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not name or not email or not password:
            flash("Please fill all fields.")
            return redirect(url_for("register"))

        if len(password) < 8:
            flash("Password must contain at least 8 characters.")
            return redirect(url_for("register"))

        password_hash = generate_password_hash(password)

        conn = get_db_connection()

        try:
            conn.execute("""
                INSERT INTO users (name, email, password)
                VALUES (?, ?, ?)
            """, (name, email, password_hash))

            conn.commit()

            flash("Registration successful!")
            return redirect(url_for("login"))

        except sqlite3.IntegrityError:
            flash("Email already registered.")

        finally:
            conn.close()

    return render_template("register.html")


# Login
@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        conn = get_db_connection()

        user = conn.execute("""
            SELECT * FROM users WHERE email = ?
        """, (email,)).fetchone()

        conn.close()

        if user and check_password_hash(user["password"], password):

            session.clear()
            session["user_id"] = user["id"]
            session["name"] = user["name"]

            return redirect(url_for("dashboard"))

        flash("Invalid email or password.")

    return render_template("login.html")


# Dashboard
@app.route("/dashboard")
def dashboard():

    if "user_id" not in session:
        return redirect(url_for("login"))

    return render_template(
        "dashboard.html",
        name=session["name"]
    )


# Banking awareness
@app.route("/banking")
def banking():

    topics = [
        {
            "title": "Savings Account",
            "description": "A savings account helps people save money safely in a bank."
        },
        {
            "title": "Current Account",
            "description": "A current account is mainly used by businesses."
        },
        {
            "title": "ATM Safety",
            "description": "Never share your ATM PIN or OTP with anyone."
        },
        {
            "title": "Banking Documents",
            "description": "Identity and address documents may be required to open a bank account."
        }
    ]

    return render_template(
        "banking.html",
        topics=topics
    )


# Savings and budgeting calculator
@app.route("/budgeting", methods=["GET", "POST"])
def budgeting():

    savings = None
    message = ""

    if request.method == "POST":

        try:
            income = float(request.form.get("income", ""))
            expenses = float(request.form.get("expenses", ""))

            if income < 0 or expenses < 0:
                message = "Enter valid positive amounts."

            else:
                savings = income - expenses

                if savings >= 0:
                    message = "Your monthly savings calculation is complete."

                else:
                    message = "Your expenses are higher than your income."

        except ValueError:
            message = "Please enter valid numbers."

    return render_template(
        "budgeting.html",
        savings=savings,
        message=message
    )


# Logout
@app.route("/logout")
def logout():

    session.clear()

    flash("You have logged out successfully.")

    return redirect(url_for("home"))


# Run application
if __name__ == "__main__":

    create_database()

    app.run(debug=True)
