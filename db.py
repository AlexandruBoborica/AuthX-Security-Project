import psycopg2

conn = psycopg2.connect(
    dbname="authlab",
    user="alex",
    password="Ursu12345",
    host="localhost"
)

def get_cursor():
    return conn.cursor()