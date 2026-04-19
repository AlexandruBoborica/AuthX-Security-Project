import psycopg2

conn = psycopg2.connect(
    host="localhost",
    database="authlab",     
    user="postgres",         
    password="Ursu12345"    
)

def get_cursor():
    return conn.cursor()
