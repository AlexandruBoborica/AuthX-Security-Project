from flask import Flask, request, jsonify
import jwt
from db import get_cursor, conn

app = Flask(__name__)

SECRET_KEY = "123"  # weak on purpose 😈


# ---------------- REGISTER ----------------
@app.route("/register", methods=["POST"])
def register():
    data = request.json
    email = data.get("email")
    password = data.get("password")

    cur = get_cursor()

    try:
        cur.execute(
            "INSERT INTO users (email, password, role) VALUES (%s, %s, %s)",
            (email, password, "USER")
        )
        conn.commit()
        return jsonify({"message": "User created"})
    except Exception as e:
        return jsonify({"error": str(e)})


# ---------------- LOGIN ----------------
@app.route("/login", methods=["POST"])
def login():
    data = request.json
    email = data.get("email")
    password = data.get("password")

    cur = get_cursor()
    cur.execute("SELECT id, password FROM users WHERE email=%s", (email,))
    user = cur.fetchone()

    # ❌ user enumeration
    if not user:
        return jsonify({"error": "User not found"}), 404

    # ❌ plain password check
    if user[1] != password:
        return jsonify({"error": "Wrong password"}), 401

    token = jwt.encode({"user_id": user[0]}, SECRET_KEY, algorithm="HS256")

    return jsonify({"token": token})


# ---------------- PROFILE ----------------
@app.route("/profile", methods=["GET"])
def profile():
    auth_header = request.headers.get("Authorization")

    if not auth_header:
        return jsonify({"error": "Missing token"}), 401

    token = auth_header.split(" ")[1]

    try:
        decoded = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return jsonify({"user_id": decoded["user_id"]})
    except Exception as e:
        return jsonify({"error": str(e)}), 401


if __name__ == "__main__":
    app.run(debug=True)