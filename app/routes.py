from flask import Blueprint, jsonify, request
from app import app, cursor, conn
import requests
import psycopg2

# Define a Blueprint for routes
api_bp = Blueprint('api', __name__)

# External API for live pricing (CoinGecko)
COINGECKO_API_URL = "https://api.coingecko.com/api/v3/simple/price"

# Health check endpoint
@api_bp.route('/')
def home():
    return jsonify({"message": "Hybrid Trading Bot API is running!"})

# Users endpoints
@api_bp.route('/users', methods=['GET'])
def get_users():
    cursor.execute("SELECT * FROM users")
    users = cursor.fetchall()
    user_list = [{"id": row[0], "name": row[1], "email": row[2]} for row in users]
    return jsonify({"users": user_list})


@api_bp.route('/add_user', methods=['POST'])
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

@api_bp.route('/add_trade', methods=['POST'])
def add_trade():
    data = request.json
    user_id = data.get('user_id')
    asset = data.get('asset')
    quantity = data.get('quantity')
    trade_type = data.get('trade_type')
    price = data.get('price')

    if trade_type not in ['buy', 'sell']:
        return jsonify({"status": "error", "message": "Invalid trade type"}), 400

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


@api_bp.route('/portfolio', methods=['GET'])
def portfolio():
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({"status": "error", "message": "User ID is required"}), 400

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

        # Fetch live prices from CoinGecko
        asset_symbols = ','.join(portfolio.keys()).lower()
        response = requests.get(COINGECKO_API_URL, params={
            "ids": asset_symbols,
            "vs_currencies": "usd"
        })

        if response.status_code != 200:
            return jsonify({"status": "error", "message": "Failed to fetch live prices"}), 500

        prices = response.json()

        # Calculate portfolio value
        total_value_usd = 0
        portfolio_with_values = {}
        for asset, quantity in portfolio.items():
            asset_key = asset.lower()
            price = prices.get(asset_key, {}).get("usd", 0)
            value = price * quantity
            portfolio_with_values[asset] = {
                "quantity": quantity,
                "price_usd": price,
                "value_usd": value
            }
            total_value_usd += value

        return jsonify({
            "status": "success",
            "portfolio": portfolio_with_values,
            "total_value_usd": total_value_usd
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400

@api_bp.route('/trades', methods=['GET'])
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
