from flask import Flask, request, session, jsonify, render_template, url_for, redirect, flash
import jwt
from db import get_cursor, conn
import bcrypt


app = Flask(__name__)
app.secret_key = "key123"


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
        all_users = cursor.fetchall()

        return render_template("admin.html", users=all_users, tickets=tickets)

    except Exception as e:
        conn.rollback()
        return f"Error: {e}"
    finally:
        cursor.close()


@app.route("/edit_profile/<int:user_id>")
def edit_profile(user_id):
    # ❌ Not logged in
    if 'user_id' not in session:
        return redirect(url_for('login'))

    # ❌ Trying to edit someone else
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

    user_id = session['user_id']  # 🔐 TRUST SESSION, NOT FORM

    username = request.form.get("username")
    phone = request.form.get("phone")
    salary = request.form.get("salary")

    cursor = conn.cursor()
    try:
        cursor.execute("""
            UPDATE users 
            SET username=%s, phone_number=%s, salary=%s 
            WHERE id=%s
        """, (username, phone, salary, user_id))

        conn.commit()
        flash("Update successful!", "success")

    except Exception as e:
        conn.rollback()
        flash(f"Error: {e}", "error")

    finally:
        cursor.close()

    return redirect(url_for('index'))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        login_input = request.form.get("login_input")
        password = request.form.get("password")

        cursor = conn.cursor()
        try:
            query = """
            SELECT id, username, email, role, phone_number, salary, password
            FROM users 
            WHERE username = %s OR email = %s
            """

            cursor.execute(query, (login_input, login_input))
            user = cursor.fetchone()

            # 🔐 CHECK HASH
            if user and bcrypt.checkpw(
                password.encode('utf-8'),
                user[6].encode('utf-8')
            ):
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

                if user_data['role'] == 'admin':
                    return redirect(url_for('admin'))
                else:
                    return render_template("profile.html", user=user_data)

            else:
                flash("Invalid username/email or password.", "error")
                return redirect(url_for('login'))

        except Exception as e:
            conn.rollback()
            flash(f"Database Error: {e}", "error")
            return redirect(url_for('login'))

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

        # 🔐 HASH PASSWORD
        hashed_password = bcrypt.hashpw(
            password.encode('utf-8'),
            bcrypt.gensalt()
        ).decode('utf-8')

        cursor = conn.cursor()
        try:
            query = """
            INSERT INTO users (email, username, password, role, phone_number, salary) 
            VALUES (%s, %s, %s, %s, %s, %s)
            """

            cursor.execute(query, (email, username, hashed_password, 'user', phone, salary))
            conn.commit()

            return render_template("registration_success.html")

        except Exception as e:
            conn.rollback()
            flash(f"Registration Error: {e}", "error")
            return redirect(url_for('register'))

        finally:
            cursor.close()

    return render_template("register.html")


@app.route("/forgot_password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        email = request.form.get("email")

        token = email  

        return render_template("reset_password.html", token=token)

    return render_template("forgot_password.html")


@app.route("/reset_password", methods=["POST"])
def reset_password():
    token = request.form.get("token")
    new_password = request.form.get("new_password")

    cursor = conn.cursor()
    try:
        query = """
        UPDATE users SET password=%s WHERE email=%s
        """
        cursor.execute(query, (new_password, token))
        conn.commit()

        return "Password reset successful"

    except Exception as e:
        conn.rollback()
        return f"Error: {e}"

    finally:
        cursor.close()


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
            query = """
            INSERT INTO tickets (title, description, created_by) 
            VALUES (%s, %s, %s)
            """

            cursor.execute(query, (title, description, user))
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