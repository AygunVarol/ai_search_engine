from flask import Flask, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from search_engine.predictor import SearchPredictor 
from search_engine.filter import ContentFilter
from models.search_data import SearchQuery, User, Feedback
from services.feedback_handler import FeedbackHandler
from utils.database import init_db, get_redis_connection
import os
from config.config import Config

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(Config)

# Initialize SQLAlchemy
db = SQLAlchemy(app)

# Initialize Login Manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Initialize components
predictor = SearchPredictor()
content_filter = ContentFilter()
feedback_handler = FeedbackHandler()
redis_client = get_redis_connection()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def home():
    return render_template('search.html')

@app.route('/search')
def search():
    query = request.args.get('q', '')
    suggestions = predictor.get_suggestions(query)
    filtered_suggestions = content_filter.filter_suggestions(suggestions)
    
    # Cache results
    redis_client.setex(
        f"search:{query}",
        300,  # Cache for 5 minutes
        str(filtered_suggestions)
    )
    
    return jsonify({
        'query': query,
        'suggestions': filtered_suggestions
    })

@app.route('/feedback', methods=['POST'])
@login_required
def submit_feedback():
    data = request.get_json()
    suggestion_id = data.get('suggestion_id')
    feedback_type = data.get('type')
    
    feedback_handler.process_feedback(
        user_id=current_user.id,
        suggestion_id=suggestion_id,
        feedback_type=feedback_type
    )
    
    return jsonify({'status': 'success'})

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.get_json()
        user = User.query.filter_by(email=data['email']).first()
        
        if user and user.check_password(data['password']):
            login_user(user)
            return jsonify({'status': 'success'})
            
        return jsonify({'status': 'error', 'message': 'Invalid credentials'})
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route('/report_suggestion', methods=['POST'])
@login_required
def report_suggestion():
    data = request.get_json()
    suggestion_id = data.get('suggestion_id')
    reason = data.get('reason')
    
    feedback_handler.handle_report(
        user_id=current_user.id,
        suggestion_id=suggestion_id,
        reason=reason
    )
    
    return jsonify({'status': 'success'})

@app.before_first_request
def setup():
    # Initialize database
    init_db(app)
    
    # Load ML models and initialize components
    predictor.load_models()
    content_filter.load_filters()

@app.errorhandler(404)
def not_found_error(error):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    app.run(debug=Config.DEBUG)
