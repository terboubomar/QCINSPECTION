# qc_app.py
from __future__ import annotations

import os
from datetime import datetime
from flask import Flask, render_template_string, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy

# ------------------------------------------------------------------------------
# Flask & DB setup
# ------------------------------------------------------------------------------
app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret")

# SQLite file in project root
DB_PATH = os.path.join(os.path.dirname(__file__), "qc_app.db")
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{DB_PATH}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


# ------------------------------------------------------------------------------
# Models
# ------------------------------------------------------------------------------
class Branch(db.Model):
    __tablename__ = "branch"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False, unique=True)
    location = db.Column(db.String(200), nullable=True)

    inspections = db.relationship("Inspection", back_populates="branch", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Branch {self.name!r}>"


class Criteria(db.Model):
    __tablename__ = "criteria"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False, unique=True)

    questions = db.relationship("Question", back_populates="criteria", cascade="all, delete-orphan")

    def __repr__(self) -> str:  # pragma: no cover - simple repr
        return f"<Criteria {self.name!r}>"


class Question(db.Model):
    __tablename__ = "question"
    id = db.Column(db.Integer, primary_key=True)
    criteria_id = db.Column(db.Integer, db.ForeignKey("criteria.id"), nullable=False)
    text = db.Column(db.String(200), nullable=False)
    max_score = db.Column(db.Integer, nullable=False)

    criteria = db.relationship("Criteria", back_populates="questions")
    answers = db.relationship("InspectionAnswer", back_populates="question", cascade="all, delete-orphan")

    def __repr__(self) -> str:  # pragma: no cover - simple repr
        return f"<Question {self.text!r}>"


class Inspection(db.Model):
    __tablename__ = "inspection"
    id = db.Column(db.Integer, primary_key=True)
    branch_id = db.Column(db.Integer, db.ForeignKey("branch.id"), nullable=False)
    inspector = db.Column(db.String(120), nullable=False)
    score = db.Column(db.Integer, nullable=False)  # 0..100
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    branch = db.relationship("Branch", back_populates="inspections")
    answers = db.relationship("InspectionAnswer", back_populates="inspection", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Inspection {self.id} - {self.branch_id} - {self.score}>"


class InspectionAnswer(db.Model):
    __tablename__ = "inspection_answer"
    id = db.Column(db.Integer, primary_key=True)
    inspection_id = db.Column(db.Integer, db.ForeignKey("inspection.id"), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey("question.id"), nullable=False)
    score = db.Column(db.Integer, nullable=False)

    inspection = db.relationship("Inspection", back_populates="answers")
    question = db.relationship("Question", back_populates="answers")

    def __repr__(self) -> str:  # pragma: no cover - simple repr
        return f"<InspectionAnswer ins={self.inspection_id} q={self.question_id} score={self.score}>"


# ------------------------------------------------------------------------------
# One-time DB bootstrap for Render (called from render_build.sh)
# ------------------------------------------------------------------------------
def setup_database(flask_app: Flask) -> None:
    """Create tables and seed minimal data. Safe to run multiple times."""
    with flask_app.app_context():
        db.create_all()

        # Seed a couple of branches on first run
        if Branch.query.count() == 0:
            branches = [
                Branch(name="Central Kitchen", location="Main Street"),
                Branch(name="Airport Outlet", location="Terminal 1"),
                Branch(name="Mall Food Court", location="Downtown Mall"),
            ]
            db.session.add_all(branches)
            db.session.commit()

        # Add a sample inspection if none exist
        if Inspection.query.count() == 0:
            central = Branch.query.filter_by(name="Central Kitchen").first()
            db.session.add(
                Inspection(
                    branch_id=central.id,
                    inspector="System",
                    score=92,
                    notes="Initial seeded inspection.",
                )
            )
            db.session.commit()

        # Seed some basic criteria & questions
        if Criteria.query.count() == 0:
            hygiene = Criteria(name="Hygiene")
            hygiene.questions = [
                Question(text="Work surfaces clean", max_score=10),
                Question(text="Proper food storage", max_score=10),
            ]
            safety = Criteria(name="Safety")
            safety.questions = [
                Question(text="Fire exits accessible", max_score=5)
            ]
            db.session.add_all([hygiene, safety])
            db.session.commit()


# ------------------------------------------------------------------------------
# Views
# ------------------------------------------------------------------------------
INDEX_HTML = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <title>QC Inspection</title>
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <style>
    body{font-family: system-ui, Arial, sans-serif; margin: 24px; max-width: 920px}
    table{width:100%; border-collapse:collapse; margin-top:12px}
    th,td{padding:8px 10px; border-bottom:1px solid #ddd; text-align:left}
    .row{display:flex; gap:12px; flex-wrap:wrap}
    .card{border:1px solid #e3e3e3; border-radius:10px; padding:16px; margin:12px 0}
    .btn{background:#111; color:#fff; border:none; padding:8px 14px; border-radius:8px; cursor:pointer}
    .btn:disabled{opacity:.6; cursor:not-allowed}
    .muted{color:#666}
    .flash{background:#fff8d1; border:1px solid #f0e19b; padding:8px 12px; border-radius:8px; margin:8px 0}
  </style>
</head>
<body>
  <h1>Restaurant Quality Control – Inspections</h1>
  <p class="muted">Simple demo running on Render. Use the form below to add a new inspection.</p>

  {% with messages = get_flashed_messages() %}
    {% if messages %}
      {% for m in messages %}<div class="flash">{{ m }}</div>{% endfor %}
    {% endif %}
  {% endwith %}

  <div class="card">
    <form method="post" action="{{ url_for('add_inspection') }}">
      <div class="row">
        <label>
          Branch
          <br>
          <select name="branch_id" required>
            {% for b in branches %}
              <option value="{{ b.id }}">{{ b.name }} – {{ b.location or 'N/A' }}</option>
            {% endfor %}
          </select>
        </label>

        <label>
          Inspector
          <br>
          <input name="inspector" placeholder="Inspector name" required />
        </label>

      </div>

      {% for c in criteria %}
        <fieldset style="border:none; margin-top:8px;">
          <legend><strong>{{ c.name }}</strong></legend>
          {% for q in c.questions %}
            <label style="display:block; margin-top:4px;">
              {{ q.text }} (max {{ q.max_score }})
              <br>
              <input name="q_{{ q.id }}" type="number" min="0" max="{{ q.max_score }}" value="{{ q.max_score }}" required />
            </label>
          {% endfor %}
        </fieldset>
      {% endfor %}

      <label style="display:block; margin-top:8px;">
        Notes
        <br>
        <textarea name="notes" rows="3" style="width:100%;"></textarea>
      </label>

      <div style="margin-top:10px;">
        <button class="btn">Add Inspection</button>
      </div>
    </form>
  </div>

  <div class="card">
    <div class="row" style="justify-content:space-between; align-items:center">
      <h2 style="margin:0">Latest Inspections</h2>
      <div>
        <a class="muted" href="{{ url_for('branches') }}">Manage branches →</a>
        <a class="muted" href="{{ url_for('criteria') }}" style="margin-left:12px;">Manage criteria →</a>
      </div>
    </div>
    <table>
      <thead>
        <tr>
          <th>#</th>
          <th>Date</th>
          <th>Branch</th>
          <th>Inspector</th>
          <th>Achieved %</th>
          <th>Notes</th>
        </tr>
      </thead>
      <tbody>
        {% for i in inspections %}
          <tr>
            <td>{{ i.id }}</td>
            <td>{{ i.created_at.strftime('%Y-%m-%d %H:%M') }}</td>
            <td>{{ i.branch.name }}</td>
            <td>{{ i.inspector }}</td>
            <td>{{ i.score }}</td>
            <td>{{ i.notes or '' }}</td>
          </tr>
        {% else %}
          <tr><td colspan="6" class="muted">No inspections yet.</td></tr>
        {% endfor %}
      </tbody>
    </table>
  </div>
</body>
</html>
"""

BRANCHES_HTML = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <title>QC – Branches</title>
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <style>
    body{font-family: system-ui, Arial, sans-serif; margin: 24px; max-width: 920px}
    table{width:100%; border-collapse:collapse; margin-top:12px}
    th,td{padding:8px 10px; border-bottom:1px solid #ddd; text-align:left}
    .row{display:flex; gap:12px; flex-wrap:wrap}
    .card{border:1px solid #e3e3e3; border-radius:10px; padding:16px; margin:12px 0}
    .btn{background:#111; color:#fff; border:none; padding:8px 14px; border-radius:8px; cursor:pointer}
    .muted{color:#666}
  </style>
</head>
<body>
  <h1>Branches</h1>
  <p class="muted">Add a new branch.</p>

  <div class="card">
    <form method="post" action="{{ url_for('add_branch') }}">
      <div class="row">
        <label>
          Name
          <br>
          <input name="name" placeholder="Branch name" required />
        </label>
        <label>
          Location
          <br>
          <input name="location" placeholder="City / Address" />
        </label>
      </div>
      <div style="margin-top:10px;">
        <button class="btn">Add Branch</button>
        <a href="{{ url_for('index') }}" class="muted" style="margin-left:12px;">← Back</a>
      </div>
    </form>
  </div>

  <div class="card">
    <h2 style="margin:0">All Branches</h2>
    <table>
      <thead><tr><th>ID</th><th>Name</th><th>Location</th></tr></thead>
      <tbody>
        {% for b in branches %}
          <tr><td>{{ b.id }}</td><td>{{ b.name }}</td><td>{{ b.location or '' }}</td></tr>
        {% else %}
          <tr><td colspan="3" class="muted">No branches yet.</td></tr>
        {% endfor %}
      </tbody>
    </table>
  </div>
</body>
</html>
"""

CRITERIA_HTML = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <title>QC – Criteria</title>
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <style>
    body{font-family: system-ui, Arial, sans-serif; margin: 24px; max-width: 920px}
    table{width:100%; border-collapse:collapse; margin-top:12px}
    th,td{padding:8px 10px; border-bottom:1px solid #ddd; text-align:left}
    .row{display:flex; gap:12px; flex-wrap:wrap}
    .card{border:1px solid #e3e3e3; border-radius:10px; padding:16px; margin:12px 0}
    .btn{background:#111; color:#fff; border:none; padding:8px 14px; border-radius:8px; cursor:pointer}
    .muted{color:#666}
  </style>
</head>
<body>
  <h1>Criteria & Questions</h1>
  <p class="muted">Manage criteria and their questions.</p>

  <div class="card">
    <form method="post" action="{{ url_for('add_criteria') }}">
      <div class="row">
        <label>Name<br><input name="name" required /></label>
      </div>
      <div style="margin-top:10px;">
        <button class="btn">Add Criteria</button>
        <a href="{{ url_for('index') }}" class="muted" style="margin-left:12px;">← Back</a>
      </div>
    </form>
  </div>

  <div class="card">
    <form method="post" action="{{ url_for('add_question') }}">
      <div class="row">
        <label>Criteria<br>
          <select name="criteria_id">
            {% for c in criteria %}
              <option value="{{ c.id }}">{{ c.name }}</option>
            {% endfor %}
          </select>
        </label>
        <label>Question<br><input name="text" required /></label>
        <label>Max Score<br><input name="max_score" type="number" min="1" required /></label>
      </div>
      <div style="margin-top:10px;"><button class="btn">Add Question</button></div>
    </form>
  </div>

  <div class="card">
    <h2 style="margin:0">All Criteria</h2>
    {% for c in criteria %}
      <h3>{{ c.name }}</h3>
      <table>
        <thead><tr><th>Question</th><th>Max Score</th></tr></thead>
        <tbody>
          {% for q in c.questions %}
            <tr><td>{{ q.text }}</td><td>{{ q.max_score }}</td></tr>
          {% else %}
            <tr><td colspan="2" class="muted">No questions yet.</td></tr>
          {% endfor %}
        </tbody>
      </table>
    {% else %}
      <p class="muted">No criteria yet.</p>
    {% endfor %}
  </div>
</body>
</html>
"""


@app.get("/health")
def health():
    return "ok"


@app.get("/")
def index():
    inspections = (
        Inspection.query.order_by(Inspection.created_at.desc())
        .limit(50)
        .all()
    )
    branches = Branch.query.order_by(Branch.name.asc()).all()
    criteria = Criteria.query.order_by(Criteria.name.asc()).all()
    return render_template_string(
        INDEX_HTML, inspections=inspections, branches=branches, criteria=criteria
    )


@app.post("/add-inspection")
def add_inspection():
    try:
        branch_id = int(request.form["branch_id"])
        inspector = request.form["inspector"].strip()
    except Exception:
        flash("Invalid form submission.")
        return redirect(url_for("index"))
    notes = request.form.get("notes", "").strip()

    questions = Question.query.order_by(Question.id).all()
    total = 0
    max_total = 0
    answers = []
    for q in questions:
        field = f"q_{q.id}"
        if field not in request.form:
            flash("Missing question scores.")
            return redirect(url_for("index"))
        try:
            score = int(request.form[field])
        except Exception:
            flash("Invalid score provided.")
            return redirect(url_for("index"))
        if not (0 <= score <= q.max_score):
            flash("Score out of range.")
            return redirect(url_for("index"))
        total += score
        max_total += q.max_score
        answers.append(InspectionAnswer(question_id=q.id, score=score))

    percentage = int((total / max_total) * 100) if max_total else 0
    inspection = Inspection(
        branch_id=branch_id, inspector=inspector, score=percentage, notes=notes
    )
    inspection.answers = answers
    db.session.add(inspection)
    db.session.commit()
    flash("Inspection added.")
    return redirect(url_for("index"))


@app.get("/branches")
def branches():
    branches = Branch.query.order_by(Branch.name.asc()).all()
    return render_template_string(BRANCHES_HTML, branches=branches)


@app.get("/criteria")
def criteria():
    criteria_list = Criteria.query.order_by(Criteria.name.asc()).all()
    return render_template_string(CRITERIA_HTML, criteria=criteria_list)


@app.post("/add-criteria")
def add_criteria():
    name = request.form["name"].strip()
    if not name:
        flash("Criteria name is required.")
        return redirect(url_for("criteria"))
    if Criteria.query.filter_by(name=name).first():
        flash("Criteria already exists.")
        return redirect(url_for("criteria"))
    db.session.add(Criteria(name=name))
    db.session.commit()
    flash("Criteria added.")
    return redirect(url_for("criteria"))


@app.post("/add-question")
def add_question():
    try:
        criteria_id = int(request.form["criteria_id"])
        text = request.form["text"].strip()
        max_score = int(request.form["max_score"])
    except Exception:
        flash("Invalid form submission.")
        return redirect(url_for("criteria"))
    if not text or max_score <= 0:
        flash("Question and score are required.")
        return redirect(url_for("criteria"))
    db.session.add(Question(criteria_id=criteria_id, text=text, max_score=max_score))
    db.session.commit()
    flash("Question added.")
    return redirect(url_for("criteria"))


@app.post("/add-branch")
def add_branch():
    name = request.form["name"].strip()
    location = request.form.get("location", "").strip()
    if not name:
        flash("Branch name is required.")
        return redirect(url_for("branches"))
    if Branch.query.filter_by(name=name).first():
        flash("Branch name already exists.")
        return redirect(url_for("branches"))

    db.session.add(Branch(name=name, location=location or None))
    db.session.commit()
    flash("Branch added.")
    return redirect(url_for("branches"))


# ------------------------------------------------------------------------------
# Local dev entrypoint (optional)
# ------------------------------------------------------------------------------
if __name__ == "__main__":
    # When running locally: create DB (idempotent) then start dev server
    setup_database(app)
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
