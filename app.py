from flask import Flask, request, jsonify , render_template , url_for
import jwt
from db import get_cursor, conn

app = Flask(__name__)




@app.route("/")
def index():
    cursor = get_cursor()
    try:
        cursor.execute("SELECT id, email, role FROM users;")
        all_users = cursor.fetchall() 
    except Exception as e:
        print(f"Connection Error: {e}")
        all_users = []
    finally:
        cursor.close()

    return render_template("index.html", users=all_users)

@app.route("/login")
def login():
    return render_template("login.html");




@app.route("/register", methods=["GET", "POST"])
def register():
        
    return render_template("register.html")


if __name__ == "__main__":
    app.run(debug=True , port=5001)