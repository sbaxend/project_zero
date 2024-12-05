from app import app
from app.routes import api_bp  # Import the Blueprint from routes.py

# Register the Blueprint
app.register_blueprint(api_bp)

if __name__ == "__main__":
    app.run(debug=True)
