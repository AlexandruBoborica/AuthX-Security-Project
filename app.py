from flask import Flask, request, jsonify , render_template , url_for
import jwt
from db import get_cursor, conn

app = Flask(__name__)




@app.route("/")
def index():
    cursor = get_cursor()
    try:
        cursor.execute("SELECT id, username ,email, role FROM users;")
        all_users = cursor.fetchall() 
    except Exception as e:
        print(f"Connection Error: {e}")
        all_users = []
    finally:
        cursor.close()

    return render_template("index.html", users=all_users)



@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        login_input = request.form.get("login_input")
        password = request.form.get("password")

        cursor = get_cursor()

        try:
            query = f"SELECT id, username, email, role FROM users WHERE username = '{login_input}' OR email='{login_input}' AND password = '{password}'"

            cursor.execute(query)
            user = cursor.fetchone()

            if user:
                return f"Welcome {user[3]} (role: {user[2]})"
            else:
                return "Invalid credentials"

        except Exception as e:
            return f"Error: {e}"

        finally:
            cursor.close()

    return render_template("login.html")










@app.route("/register", methods=["GET", "POST"])
def register():
    if(request.method == "POST"):
        new_member_email = request.form.get("email")
        new_member_username = request.form.get("username")
        new_member_passwd = request.form.get("password")
       
        cursor = get_cursor()
        try:
            cursor.execute(
                "INSERT INTO users (email, password, role , username) VALUES (%s, %s, %s, %s)",
                (new_member_email, new_member_passwd, "user" , new_member_username)
            )
            conn.commit()
            return "User registered successfully"
        except Exception as e:
            return f"Error: {e}"
        finally:
            cursor.close()
    return render_template("register.html")


if __name__ == "__main__":
    app.run(debug=True , port=5001)