from flask import Flask, request,session, jsonify , render_template , url_for ,redirect , flash
import jwt
from db import get_cursor, conn

app = Flask(__name__)
app.secret_key = "key123"



@app.route("/")
def index():
    return render_template("index.html")



@app.route("/admin")
def admin():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id, title, description, created_by FROM tickets;")
        tickets = cursor.fetchall()
        cursor.execute("SELECT id, username, email, phone_number, salary, role FROM users;")
        all_users = cursor.fetchall()
        return render_template("admin.html", users=all_users , tickets = tickets)
    except Exception as e:
        conn.rollback()
        return f"Error: {e}"
    finally:
        cursor.close()

@app.route("/edit_profile/<int:user_id>")
def edit_profile(user_id):
    cursor = conn.cursor()
    cursor.execute(f"SELECT id, username, phone_number, salary FROM users WHERE id = {user_id}")
    res = cursor.fetchone()
    user_data = {"id": res[0], "username": res[1], "phone": res[2], "salary": res[3]}
    cursor.close()
    return render_template("edit_profile.html", user=user_data)

@app.route("/update_profile", methods=["POST"])
def update_profile():
    user_id = request.form.get("user_id")
    username = request.form.get("username")
    phone = request.form.get("phone")
    salary = request.form.get("salary")
    
    cursor = conn.cursor()
    try:
        query = f"UPDATE users SET username='{username}', phone_number='{phone}', salary={salary} WHERE id={user_id}"
        cursor.execute(query)
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
         
            query = f"SELECT id, username, email, role, phone_number, salary FROM users WHERE (username = '{login_input}' OR email='{login_input}') AND password = '{password}'"
            
            cursor.execute(query)
            user = cursor.fetchone()
            
            if user:
                
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
            conn.rollback()
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
        cursor = conn.cursor()

        try:
           
            query = f"INSERT INTO users (email, username, password, role, phone_number, salary) VALUES ('{email}', '{username}', '{password}', 'user', '{phone}', {salary})"
            
            cursor.execute(query)
            conn.commit()
            return render_template("registration_success.html")
            
        except Exception as e:
            conn.rollback()
            flash(f"Registration Error: {e}", "error")
            return redirect(url_for('register'))
        finally:
            cursor.close()

    return render_template("register.html")


@app.route("/forgot_password", methods=["POST"])
def forgot_password():
    email = request.form.get("email")

   
    token = email

    return f"Reset token: {token}"

@app.route("/reset_password", methods=["POST"])
def reset_password():
    token = request.form.get("token")
    new_password = request.form.get("new_password")

    cursor = conn.cursor()
    try:
       
        query = f"UPDATE users SET password='{new_password}' WHERE email='{token}'"
        cursor.execute(query)
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
            query = f"INSERT INTO tickets (title, description, created_by) VALUES ('{title}', '{description}', '{user}')"
            cursor.execute(query)
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
    app.run(debug=True , port=5001)