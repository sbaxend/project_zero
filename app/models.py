from app import cursor, conn

def get_all_users():
    cursor.execute("SELECT * FROM users")
    return cursor.fetchall()

def add_user_to_db(name, email):
    try:
        cursor.execute(
            "INSERT INTO users (name, email) VALUES (%s, %s)", (name, email)
        )
        conn.commit()
        return {"status": "success", "message": f"User {name} added successfully!"}
    except Exception as e:
        conn.rollback()
        return {"status": "error", "message": str(e)}
