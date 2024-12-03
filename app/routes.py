from flask import jsonify, request
from app import app, cursor, conn
import psycopg2
@app.route('/')
def home():
    return jsonify({"message": "Hybrid Trading Bot API is running!"})

@app.route('/users', methods=['GET'])
def get_users():
    cursor.execute("SELECT * FROM users")
    users = cursor.fetchall()
    user_list = [{"id": row[0], "name": row[1], "email": row[2]} for row in users]
    return jsonify({"users": user_list})

@app.route('/add_user', methods=['POST'])
def add_user():
    data = request.json
    name = data.get('name')
    email = data.get('email')
    try:
        cursor.execute(
            "INSERT INTO users (name, email) VALUES (%s, %s)", (name, email)
        )
        conn.commit()
        return jsonify({"status": "success", "message": f"User {name} added successfully!"})
    except psycopg2.IntegrityError:
        conn.rollback()
        return jsonify({"status": "error", "message": "Email already exists!"}), 400

@app.route('/add_trade', methods=['POST'])
def add_trade():
    print("POST /add_trade route hit")
    print(conn)  # Debugging: Check if the database connection is live
    print(cursor)  # Debugging: Check if the cursor is working
    data = request.json
    user_id = data.get('user_id')
    asset = data.get('asset')
    quantity = data.get('quantity')
    trade_type = data.get('trade_type')
    price = data.get('price')

    try:
        cursor.execute(
            """
            INSERT INTO trades (user_id, asset, quantity, trade_type, price)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (user_id, asset, quantity, trade_type, price)
        )
        conn.commit()
        return jsonify({"status": "success", "message": "Trade added successfully!"})
    except Exception as e:
        conn.rollback()
        return jsonify({"status": "error", "message": str(e)}), 400



@app.route('/trades', methods=['GET'])
def get_trades():
    user_id = request.args.get('user_id')

    try:
        cursor.execute("SELECT * FROM trades WHERE user_id = %s ORDER BY timestamp DESC", (user_id,))
        trades = cursor.fetchall()

        trade_list = [
            {
                "id": row[0],
                "user_id": row[1],
                "asset": row[2],
                "quantity": float(row[3]),
                "trade_type": row[4],
                "price": float(row[5]) if row[5] else None,
                "timestamp": row[6].strftime('%Y-%m-%d %H:%M:%S')
            } for row in trades
        ]
        return jsonify({"trades": trade_list})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400


@app.route('/portfolio', methods=['GET'])
def portfolio():
    user_id = request.args.get('user_id')

    try:
        # Calculate portfolio holdings based on trades
        cursor.execute("""
            SELECT asset, SUM(
                CASE WHEN trade_type = 'buy' THEN quantity
                     WHEN trade_type = 'sell' THEN -quantity
                END
            ) AS total_quantity
            FROM trades
            WHERE user_id = %s
            GROUP BY asset
        """, (user_id,))
        holdings = cursor.fetchall()

        portfolio = {row[0]: float(row[1]) for row in holdings if row[1] > 0}
        return jsonify({"portfolio": portfolio})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400
