from flask import Flask, request, session, render_template, url_for, redirect, flash
from db import conn
import bcrypt
import secrets
import os
import time,re


login_attempts = {}
MAX_ATTEMPTS = 5
BLOCK_TIME = 60

app = Flask(__name__)
app.secret_key = os.urandom(24)

app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SECURE=False  # True if using HTTPS
)


@app.before_request
def csrf_protect():
    if request.method == "POST":
        token = session.get("_csrf_token")
        form_token = request.form.get("_csrf_token")
        if not token or token != form_token:
            return "CSRF attack detected", 403


def generate_csrf_token():
    if "_csrf_token" not in session:
        session["_csrf_token"] = secrets.token_hex(16)
    return session["_csrf_token"]

app.jinja_env.globals['csrf_token'] = generate_csrf_token



@app.route("/")
def index():
    return render_template("index.html")


@app.route("/admin")
def admin():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if session.get('role') != 'admin':
        return "Access denied", 403

    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id, title, description, created_by FROM tickets;")
        tickets = cursor.fetchall()

        cursor.execute("SELECT id, username, email, phone_number, salary, role FROM users;")
        users = cursor.fetchall()

        return render_template("admin.html", users=users, tickets=tickets)
    finally:
        cursor.close()


@app.route("/edit_profile/<int:user_id>")
def edit_profile(user_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if session['user_id'] != user_id:
        return "Unauthorized", 403

    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, username, phone_number, salary FROM users WHERE id = %s",
        (user_id,)
    )
    res = cursor.fetchone()
    cursor.close()

    user_data = {
        "id": res[0],
        "username": res[1],
        "phone": res[2],
        "salary": res[3]
    }

    return render_template("edit_profile.html", user=user_data)


@app.route("/update_profile", methods=["POST"])
def update_profile():

    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']

    username = request.form.get("username")
    phone = request.form.get("phone")

    cursor = conn.cursor()

    try:
        cursor.execute("""
            UPDATE users
            SET username=%s,
                phone_number=%s
            WHERE id=%s
        """, (username, phone, user_id))

        conn.commit()

        flash("Profile updated", "success")

    except Exception as e:
        conn.rollback()
        flash(str(e), "error")

    finally:
        cursor.close()

    return redirect(url_for("index"))


@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        login_input = request.form.get("login_input")
        password = request.form.get("password")

        now = time.time()


        if login_input in login_attempts:

            attempts, last_attempt = login_attempts[login_input]

            if attempts >= MAX_ATTEMPTS:

                if now - last_attempt < BLOCK_TIME:

                    remaining = int(
                        BLOCK_TIME - (now - last_attempt)
                    )

                    flash(
                        f"Too many failed attempts. Wait {remaining} seconds.",
                        "error"
                    )

                    return redirect(url_for("login"))

                else:
                
                    del login_attempts[login_input]

        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT id, username, email, role,
                       phone_number, salary, password
                FROM users
                WHERE username=%s OR email=%s
            """, (login_input, login_input))

            user = cursor.fetchone()

        

            if user and bcrypt.checkpw(
                password.encode(),
                user[6].encode()
            ):

             
                login_attempts.pop(login_input, None)

                session['user_id'] = user[0]
                session['role'] = user[3]

                user_data = {
                    "id": user[0],
                    "username": user[1],
                    "email": user[2],
                    "role": user[3],
                    "phone": user[4],
                    "salary": user[5]
                }

                if user_data["role"] == "admin":
                    return redirect(url_for("admin"))

                return render_template(
                    "profile.html",
                    user=user_data
                )

          
            else:

                if login_input not in login_attempts:
                    login_attempts[login_input] = [1, now]

                else:
                    login_attempts[login_input][0] += 1
                    login_attempts[login_input][1] = now

                flash("Invalid credentials", "error")
                return redirect(url_for("login"))

        finally:
            cursor.close()

    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        email = request.form.get("email")
        username = request.form.get("username")
        password = request.form.get("password")
        phone = request.form.get("phone")

        salary = 50000

        

        if len(password) < 12:
            flash("Password must be at least 12 characters")
            return redirect(url_for("register"))

        if not re.search(r"\d", password):
            flash("Password must contain at least 1 number")
            return redirect(url_for("register"))

        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
            flash("Password must contain at least 1 special character")
            return redirect(url_for("register"))

    
        hashed_password = bcrypt.hashpw(
            password.encode(),
            bcrypt.gensalt()
        ).decode()

        cursor = conn.cursor()

        try:

            cursor.execute("""
                INSERT INTO users
                (email, username, password,
                 role, phone_number, salary)

                VALUES (%s,%s,%s,%s,%s,%s)
            """,

            (
                email,
                username,
                hashed_password,
                "user",
                phone,
                salary
            ))

            conn.commit()

            return render_template(
                "registration_success.html"
            )

        except Exception as e:

            conn.rollback()

            flash(
                f"Registration Error: {e}",
                "error"
            )

            return redirect(
                url_for("register")
            )

        finally:
            cursor.close()

    return render_template("register.html")

@app.route("/forgot_password", methods=["GET", "POST"])
def forgot_password():

    if request.method == "POST":

        email = request.form.get("email")

        token = secrets.token_urlsafe(32)

        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                UPDATE users
                SET reset_token=%s
                WHERE email=%s
                """,
                (token, email)
            )

            conn.commit()

            flash(
                "If the account exists, a reset link has been sent.",
                "success"
            )

            return redirect(url_for("login"))

        finally:
            cursor.close()

    return render_template("forgot_password.html")


@app.route("/reset_password/<token>", methods=["GET","POST"])
def reset_password(token):

    if request.method == "POST":

        new_password = request.form.get(
            "new_password"
        )

        
 

        hashed_password = bcrypt.hashpw(
            new_password.encode(),
            bcrypt.gensalt()
        ).decode()

        cursor = conn.cursor()

        try:

            cursor.execute("""
                UPDATE users
                SET password=%s,
                    reset_token=NULL
                WHERE reset_token=%s
            """,

            (
                hashed_password,
                token
            ))

            conn.commit()

            flash(
                "Password reset successful.",
                "success"
            )

            return redirect(
                url_for("login")
            )

        finally:
            cursor.close()

    return render_template(
        "reset_password.html"
    )

@app.route("/create_ticket", methods=["GET", "POST"])
def create_ticket():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if request.method == "POST":
        title = request.form.get("title")
        description = request.form.get("description")
        user = session.get("user_id")

        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO tickets (title, description, created_by) 
                VALUES (%s, %s, %s)
            """, (title, description, user))

            conn.commit()
            return "Ticket created!"

        except Exception as e:
            conn.rollback()
            return f"Error: {e}"

        finally:
            cursor.close()

    return render_template("create_ticket.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for('login'))


if __name__ == "__main__":
    app.run(debug=True, port=5001)