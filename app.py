from flask import Flask, render_template, request, redirect, url_for, send_from_directory, jsonify
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///data.db"
app.config["UPLOAD_FOLDER"] = "uploads"
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tg_id = db.Column(db.String(50), unique=True)
    first_name = db.Column(db.String(100))
    last_name = db.Column(db.String(100))
    phone = db.Column(db.String(50))
    university = db.Column(db.String(200))
    article_filename = db.Column(db.String(200))

    @property
    def fullname(self):
        return f"{self.first_name} {self.last_name}"

@app.route("/")
def index():
    users = User.query.filter(User.article_filename.isnot(None)).all()
    return render_template("index.html", users=users)

@app.route("/maqolalar")
def maqolalar():
    users = User.query.filter(User.article_filename.isnot(None)).all()
    return render_template("maqolalar.html", users=users)

@app.route("/user/<tg_id>")
def get_user(tg_id):
    user = User.query.filter_by(tg_id=tg_id).first()
    if user:
        return jsonify({"registered": True})
    return jsonify({"registered": False})

@app.route("/register", methods=["POST"])
def register():
    data = request.json
    user = User.query.filter_by(tg_id=data["tg_id"]).first()
    if not user:
        user = User(**data)
        db.session.add(user)
        db.session.commit()
        return jsonify({"message": "Registered"}), 201
    return jsonify({"message": "Already registered"}), 200

@app.route("/upload_article/<tg_id>", methods=["POST"])
def upload_article(tg_id):
    user = User.query.filter_by(tg_id=tg_id).first()
    if not user:
        return jsonify({"error": "User not found"}), 404

    file = request.files["file"]
    filename = f"{tg_id}_{file.filename}"
    file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
    user.article_filename = filename
    db.session.commit()
    return jsonify({"message": "Uploaded"}), 200

@app.route("/uploads/<filename>")
def uploaded_file(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
