from flask import Flask
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from config.config import Config
from controllers.search_controller import search_bp
from utils.database import init_db

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(Config)

# Enable CORS
CORS(app)

# Initialize SQLAlchemy
db = SQLAlchemy()
db.init_app(app)

# Initialize database
init_db(app)

# Register blueprints
app.register_blueprint(search_bp, url_prefix='/api/search')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
