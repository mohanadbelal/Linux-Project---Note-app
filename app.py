"""
Note-Taking Web Application
Flask + MariaDB with SQLAlchemy ORM
"""

import os
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "change-me-in-production")

DB_USER = os.environ.get("DB_USER", "noteuser")
DB_PASS = os.environ.get("DB_PASS", "notepassword")
DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_PORT = os.environ.get("DB_PORT", "3306")
DB_NAME = os.environ.get("DB_NAME", "notesdb")

app.config["SQLALCHEMY_DATABASE_URI"] = (
    f"mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------
class Note(db.Model):
    __tablename__ = "notes"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), default="General")
    is_pinned = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "content": self.content,
            "category": self.category,
            "is_pinned": self.is_pinned,
            "created_at": self.created_at.strftime("%b %d, %Y %I:%M %p"),
            "updated_at": self.updated_at.strftime("%b %d, %Y %I:%M %p"),
        }

# ---------------------------------------------------------------------------
# Routes – Pages
# ---------------------------------------------------------------------------
@app.route("/")
def index():
    """Home page – list all notes."""
    search = request.args.get("q", "")
    category = request.args.get("category", "")

    query = Note.query
    if search:
        query = query.filter(
            db.or_(
                Note.title.ilike(f"%{search}%"),
                Note.content.ilike(f"%{search}%"),
            )
        )
    if category:
        query = query.filter_by(category=category)

    notes = query.order_by(Note.is_pinned.desc(), Note.updated_at.desc()).all()
    categories = [
        row[0]
        for row in db.session.query(Note.category).distinct().all()
        if row[0]
    ]
    return render_template(
        "index.html",
        notes=notes,
        categories=categories,
        search=search,
        active_category=category,
    )


@app.route("/note/new", methods=["GET", "POST"])
def create_note():
    """Create a new note."""
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        content = request.form.get("content", "").strip()
        category = request.form.get("category", "General").strip()

        if not title or not content:
            flash("Title and content are required.", "error")
            return redirect(url_for("create_note"))

        note = Note(title=title, content=content, category=category)
        db.session.add(note)
        db.session.commit()
        flash("Note created successfully!", "success")
        return redirect(url_for("index"))

    return render_template("note_form.html", note=None)


@app.route("/note/<int:note_id>/edit", methods=["GET", "POST"])
def edit_note(note_id):
    """Edit an existing note."""
    note = Note.query.get_or_404(note_id)

    if request.method == "POST":
        note.title = request.form.get("title", "").strip()
        note.content = request.form.get("content", "").strip()
        note.category = request.form.get("category", "General").strip()

        if not note.title or not note.content:
            flash("Title and content are required.", "error")
            return redirect(url_for("edit_note", note_id=note_id))

        db.session.commit()
        flash("Note updated successfully!", "success")
        return redirect(url_for("index"))

    return render_template("note_form.html", note=note)


@app.route("/note/<int:note_id>/delete", methods=["POST"])
def delete_note(note_id):
    """Delete a note."""
    note = Note.query.get_or_404(note_id)
    db.session.delete(note)
    db.session.commit()
    flash("Note deleted.", "info")
    return redirect(url_for("index"))


@app.route("/note/<int:note_id>/pin", methods=["POST"])
def toggle_pin(note_id):
    """Toggle pin status."""
    note = Note.query.get_or_404(note_id)
    note.is_pinned = not note.is_pinned
    db.session.commit()
    return redirect(url_for("index"))


# ---------------------------------------------------------------------------
# Routes – API (optional JSON endpoints)
# ---------------------------------------------------------------------------
@app.route("/api/notes", methods=["GET"])
def api_list_notes():
    notes = Note.query.order_by(Note.updated_at.desc()).all()
    return jsonify([n.to_dict() for n in notes])


@app.route("/api/notes", methods=["POST"])
def api_create_note():
    data = request.get_json()
    note = Note(
        title=data["title"],
        content=data["content"],
        category=data.get("category", "General"),
    )
    db.session.add(note)
    db.session.commit()
    return jsonify(note.to_dict()), 201


# ---------------------------------------------------------------------------
# Bootstrap
# ---------------------------------------------------------------------------
with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
