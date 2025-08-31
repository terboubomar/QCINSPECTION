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


class Inspection(db.Model):
    __tablename__ = "inspection"
    id = db.Column(db.Integer, primary_key=True)
    branch_id = db.Column(db.Integer, db.ForeignKey("branch.id"), nullable=False)
    inspector = db.Column(db.String(120), nullable=False)
    score = db.Column(db.Integer, nullable=False)  # 0..100
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    branch = db.relationship("Branch", back_populates="inspections")

    def __repr__(self) -> str:
        return f"<Inspection {self.id} - {self.branch_id} - {self.score}>"


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

        <label>
          Score (0–100)
          <br>
          <input name="score" type="number" min="0" max="100" value="90" required />
        </label>
      </div>

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
      <a class="muted" href="{{ url_for('branches') }}">Manage branches →</a>
    </div>
    <table>
      <thead>
        <tr>
          <th>#</th>
          <th>Date</th>
          <th>Branch</th>
          <th>Inspector</th>
          <th>Score</th>
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
    return render_template_string(INDEX_HTML, inspections=inspections, branches=branches)


@app.post("/add-inspection")
def add_inspection():
    try:
        branch_id = int(request.form["branch_id"])
        inspector = request.form["inspector"].strip()
        score = int(request.form["score"])
        notes = request.form.get("notes", "").strip()
    except Exception:
        flash("Invalid form submission.")
        return redirect(url_for("index"))

    if not (0 <= score <= 100):
        flash("Score must be between 0 and 100.")
        return redirect(url_for("index"))

    db.session.add(
        Inspection(branch_id=branch_id, inspector=inspector, score=score, notes=notes)
    )
    db.session.commit()
    flash("Inspection added.")
    return redirect(url_for("index"))


@app.get("/branches")
def branches():
    branches = Branch.query.order_by(Branch.name.asc()).all()
    return render_template_string(BRANCHES_HTML, branches=branches)


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
