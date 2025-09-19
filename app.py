from flask import Flask, request, redirect, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import uuid

# Flask app setup
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///urls.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ==========================
# Table for Shortened URLs
# ==========================
class ShortURL(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    original_url = db.Column(db.String(500), nullable=False)
    short_id = db.Column(db.String(10), unique=True, nullable=False)
    clicks = db.relationship('ClickStats', backref='shorturl', lazy=True)


# ==========================
# Table for Click Statistics
# ==========================
class ClickStats(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    source = db.Column(db.String(200))
    location = db.Column(db.String(200))
    shorturl_id = db.Column(db.Integer, db.ForeignKey('short_url.id'))


# Create database tables
with app.app_context():
    db.create_all()


# ==========================
# 1. Route: Create short URL
# ==========================
@app.route('/shorten', methods=['POST'])
def shorten_url():
    data = request.get_json()
    original_url = data.get("url")

    if not original_url:
        return jsonify({"error": "URL required"}), 400

    short_id = str(uuid.uuid4())[:6]  # 6-character short ID
    new_url = ShortURL(original_url=original_url, short_id=short_id)
    db.session.add(new_url)
    db.session.commit()

    return jsonify({"short_url": f"http://127.0.0.1:5000/{short_id}"})


# ==========================
# 2. Route: Redirect short URL
# ==========================
@app.route('/<short_id>')
def redirect_url(short_id):
    url_data = ShortURL.query.filter_by(short_id=short_id).first()
    if url_data:
        click = ClickStats(
            source="direct",
            location="unknown",
            shorturl_id=url_data.id
        )
        db.session.add(click)
        db.session.commit()

        return redirect(url_data.original_url)
    else:
        return "Invalid URL", 404


# ==========================
# 3. Route: Get click stats
# ==========================
@app.route('/stats/<short_id>')
def stats(short_id):
    url_data = ShortURL.query.filter_by(short_id=short_id).first()
    if url_data:
        stats = ClickStats.query.filter_by(shorturl_id=url_data.id).all()
        return jsonify([{
            "timestamp": c.timestamp,
            "source": c.source,
            "location": c.location
        } for c in stats])
    else:
        return "No stats found", 404


# ==========================
# Run Flask app
# ==========================
if __name__ == "_main_":
    app.run(debug=True)
