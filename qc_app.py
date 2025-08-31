import datetime
from flask import Flask, render_template_string, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import os

# --- Basic Configuration ---
basedir = os.path.abspath(os.path.dirname(__file__))
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'qc_app.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


# --- Meta Tags for "Add to Home Screen" Functionality ---
PWA_META_TAGS = """
    <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no">
    <meta name="mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
    <meta name="apple-mobile-web-app-title" content="QC App">
    <meta name="theme-color" content="#007bff">
"""

# --- Global CSS Styles for Tablet App ---
GLOBAL_CSS = """
<style>
    :root {
        --primary-color: #007bff;
        --primary-hover: #0056b3;
        --success-color: #28a745;
        --danger-color: #dc3545;
        --light-gray: #f8f9fa;
        --medium-gray: #dee2e6;
        --dark-gray: #343a40;
        --font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif, "Apple Color Emoji", "Segoe UI Emoji";
        --box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
        --border-radius: 12px;
    }
    
    html {
        -webkit-text-size-adjust: 100%;
        -webkit-tap-highlight-color: rgba(0,0,0,0);
    }

    body {
        font-family: var(--font-family);
        margin: 0;
        background-color: var(--light-gray);
        color: var(--dark-gray);
        line-height: 1.6;
        font-size: 18px; /* Larger base font for tablets */
    }

    .container {
        max-width: 1200px;
        margin: 1.5em auto;
        padding: 1.5em;
    }
    
    h1, h2 {
        color: var(--dark-gray);
        border-bottom: 2px solid var(--medium-gray);
        padding-bottom: 0.5em;
        margin-top: 0;
        margin-bottom: 1em;
    }
    h1 { font-size: 2.5em; }
    h2 { font-size: 2em; }
    
    a {
        color: var(--primary-color);
        text-decoration: none;
    }
    
    .btn {
        display: block; /* Full width for easy tapping */
        width: 100%;
        box-sizing: border-box;
        padding: 1em;
        background-color: var(--primary-color);
        color: white !important;
        text-align: center;
        text-decoration: none;
        border-radius: var(--border-radius);
        font-weight: bold;
        border: none;
        cursor: pointer;
        font-size: 1.2em;
        transition: background-color 0.2s, transform 0.1s;
    }
    .btn:active {
        transform: scale(0.98);
        background-color: var(--primary-hover);
    }
    .btn-success { background-color: var(--success-color); }
    .btn-success:active { background-color: #218838; }

    .card {
        background-color: white;
        border-radius: var(--border-radius);
        box-shadow: var(--box-shadow);
        padding: 1.5em;
        margin-bottom: 1.5em;
    }

    .card-list a {
        display: block;
        padding: 1.5em;
        margin: 1em 0;
        background-color: #fff;
        text-decoration: none;
        color: var(--dark-gray);
        border-radius: var(--border-radius);
        box-shadow: var(--box-shadow);
        transition: transform 0.2s;
    }
    .card-list a:active {
        transform: scale(0.99);
    }
    .card-list strong {
        color: var(--primary-color);
        font-size: 1.3em;
    }
    
    table {
        width: 100%;
        border-collapse: collapse;
        margin: 2em 0;
    }
    th, td {
        border: 1px solid var(--medium-gray);
        padding: 1em;
        text-align: left;
    }
    th {
        background-color: var(--light-gray);
        font-weight: bold;
    }
    
    .pass { color: var(--success-color); font-weight: bold; }
    .fail { color: var(--danger-color); font-weight: bold; }
    
    label { font-weight: bold; }
    input[type="text"], textarea {
        width: 100%;
        padding: 1em;
        border: 2px solid var(--medium-gray);
        border-radius: var(--border-radius);
        box-sizing: border-box;
        font-size: 1em;
        margin-top: 0.5em;
    }
    
    .radio-group {
        display: flex;
        gap: 1em;
        margin-top: 1em;
    }
    .radio-group input[type="radio"] { display: none; }
    .radio-group label {
        flex: 1;
        text-align: center;
        padding: 1em;
        border: 2px solid var(--medium-gray);
        border-radius: var(--border-radius);
        font-weight: bold;
        cursor: pointer;
        transition: all 0.2s ease-in-out;
    }
    .radio-group input[type="radio"]:checked + label {
        border-color: var(--primary-color);
        background-color: var(--primary-color);
        color: white;
        box-shadow: 0 4px 8px rgba(0, 123, 255, 0.3);
    }
</style>
"""

# --- HTML Templates ---

INDEX_HTML = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>QC App - Branches</title>
    {PWA_META_TAGS}
    {GLOBAL_CSS}
</head>
<body>
    <div class="container">
        <div class="card">
            <h1>Select a Branch</h1>
        </div>
        <div class="card-list">
            {{% for branch in branches %}}
                <a href="{{{{ url_for('branch_dashboard', branch_id=branch.id) }}}}">
                    <strong>{{{{ branch.name }}}}</strong> <br>
                    <small style="color: #6c757d;">{{{{ branch.location }}}}</small>
                </a>
            {{% endfor %}}
        </div>
    </div>
</body>
</html>
"""

BRANCH_DASHBOARD_HTML = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>{{{{ branch.name }}}} Dashboard</title>
    {PWA_META_TAGS}
    {GLOBAL_CSS}
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
</head>
<body>
    <div class="container">
        <a href="{{{{ url_for('index') }}}}">&laquo; Back to All Branches</a>
        <div class="card" style="margin-top: 1em;">
            <h1>{{{{ branch.name }}}}</h1>
            <a href="{{{{ url_for('start_inspection', branch_id=branch.id) }}}}" class="btn btn-success">Start New Inspection</a>
        </div>

        <div class="card">
            <h2>Performance History</h2>
            {{% if chart_labels|length > 1 %}}
            <div>
                <canvas id="performanceChart"></canvas>
            </div>
            {{% else %}}
            <p style="text-align: center; color: #6c757d;">Not enough data to display a chart. Complete at least two inspections.</p>
            {{% endif %}}
        </div>

        <div class="card">
            <h2>Past Inspections</h2>
            <div class="card-list">
                {{% for inspection in inspections %}}
                    <a href="{{{{ url_for('view_inspection', inspection_id=inspection.id) }}}}">
                        <strong>Inspector:</strong> {{{{ inspection.inspector_name }}}} <br>
                        <small style="color: #6c757d;">Date: {{{{ inspection.inspection_date.strftime('%Y-%m-%d %H:%M') }}}} UTC</small>
                    </a>
                {{% else %}}
                    <div style="padding: 1em; text-align: center; color: #6c757d;">No inspections found.</div>
                {{% endfor %}}
            </div>
        </div>
    </div>
    <script>
        {{% if chart_labels|length > 1 %}}
        const ctx = document.getElementById('performanceChart').getContext('2d');
        new Chart(ctx, {{
            type: 'line',
            data: {{
                labels: {{{{ chart_labels|tojson }}}},
                datasets: [{{
                    label: 'Inspection Score (%)',
                    data: {{{{ chart_data|tojson }}}},
                    borderColor: 'rgba(0, 123, 255, 1)',
                    backgroundColor: 'rgba(0, 123, 255, 0.1)',
                    fill: true,
                    tension: 0.1
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                scales: {{
                    y: {{
                        beginAtZero: true,
                        max: 100,
                        ticks: {{
                            callback: function(value) {{ return value + '%' }}
                        }}
                    }}
                }},
                plugins: {{
                    tooltip: {{
                        callbacks: {{
                            label: function(context) {{
                                return context.dataset.label + ': ' + context.parsed.y.toFixed(2) + '%';
                            }}
                        }}
                    }}
                }}
            }}
        }});
        {{% endif %}}
    </script>
</body>
</html>
"""

INSPECTION_FORM_HTML = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>New Inspection</title>
    {PWA_META_TAGS}
    {GLOBAL_CSS}
</head>
<body>
    <div class="container">
        <a href="{{{{ url_for('branch_dashboard', branch_id=branch.id) }}}}">&laquo; Cancel Inspection</a>
        <h1 style="margin-top: 1em;">New Inspection: {{{{ branch.name }}}}</h1>
        <form action="{{{{ url_for('submit_inspection', branch_id=branch.id) }}}}" method="post">
            <div class="card">
                <label for="inspector_name">Inspector's Name</label>
                <input type="text" id="inspector_name" name="inspector_name" required>
            </div>
            {{% for category in categories %}}
                <div class="card">
                    <h2>{{{{ category.name }}}}</h2>
                    {{% for item in category.items %}}
                        <div style="border-top: 1px solid var(--medium-gray); padding: 1.5em 0; margin: 1.5em 0;">
                            <p style="font-weight: 600; margin-top: 0;">{{{{ item.question }}}} <span style="font-size: 0.9em; color: #6c757d; font-weight: normal;">({{{{ item.points }}}} pts)</span></p>
                            <input type="hidden" name="item_ids" value="{{{{ item.id }}}}">
                            <div class="radio-group">
                                <input type="radio" name="response_{{{{ item.id }}}}" value="Pass" id="pass_{{{{ item.id }}}}" required>
                                <label for="pass_{{{{ item.id }}}}">Pass</label>
                                <input type="radio" name="response_{{{{ item.id }}}}" value="Fail" id="fail_{{{{ item.id }}}}">
                                <label for="fail_{{{{ item.id }}}}">Fail</label>
                            </div>
                            <textarea name="notes_{{{{ item.id }}}}" placeholder="Add notes/remarks (optional)" style="margin-top: 1em;"></textarea>
                        </div>
                    {{% endfor %}}
                </div>
            {{% endfor %}}
            <button type="submit" class="btn">Submit Inspection Report</button>
        </form>
    </div>
</body>
</html>
"""

INSPECTION_RESULTS_HTML = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Inspection Report</title>
    {PWA_META_TAGS}
    {GLOBAL_CSS}
    <style>
        .remarks {{ font-style: italic; color: #6c757d; }}
        .score-card .final-score {{
            font-size: 4em;
            font-weight: bold;
            color: var(--primary-color);
            margin: 0.2em 0;
        }}
    </style>
</head>
<body>
    <div class="container">
        <a href="{{{{ url_for('branch_dashboard', branch_id=inspection.branch.id) }}}}">&laquo; Back to {{{{ inspection.branch.name }}}} Dashboard</a>
        <h1 style="margin-top: 1em;">Inspection Report</h1>
        <div class="card">
            <p><strong>Branch:</strong> {{{{ inspection.branch.name }}}}</p>
            <p><strong>Inspector:</strong> {{{{ inspection.inspector_name }}}}</p>
            <p><strong>Date:</strong> {{{{ inspection.inspection_date.strftime('%Y-%m-%d %H:%M') }}}} UTC</p>
        </div>
        <div class="card score-card" style="text-align: center;">
            <h2>Overall Score</h2>
            <div class="final-score">{{{{ "%.2f"|format(results['percentage']) }}}}%</div>
            <div style="font-size: 1.2em; font-weight: bold;">({{{{ results['total_scored'] }}}} / {{{{ results['total_possible'] }}}} Points)</div>
        </div>
        {{% for category_name, data in results['categories'].items() %}}
        <div class="card">
            <h2>{{{{ category_name }}}} ({{{{data['scored']}}}} / {{{{data['possible']}}}})</h2>
            <div style="overflow-x: auto;">
                <table>
                    <thead>
                        <tr><th>Criteria</th><th>Result</th><th>Points</th><th>Remarks</th></tr>
                    </thead>
                    <tbody>
                        {{% for item in data['items'] %}}
                        <tr>
                            <td>{{{{ item['question'] }}}}</td>
                            <td class="{{{{ item['response']|lower }}}}">{{{{ item['response'] }}}}</td>
                            <td>{{{{ item['scored_points'] }}}} / {{{{ item['points'] }}}}</td>
                            <td class="remarks">{{{{ item['notes'] }}}}</td>
                        </tr>
                        {{% endfor %}}
                    </tbody>
                </table>
            </div>
        </div>
        {{% endfor %}}
    </div>
</body>
</html>
"""

# --- Database Models (Unchanged) ---
class Branch(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    location = db.Column(db.String(100), nullable=False)
    inspections = db.relationship('Inspection', backref='branch', lazy=True, cascade="all, delete-orphan")
class ChecklistCategory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    items = db.relationship('ChecklistItem', backref='category', lazy=True, cascade="all, delete-orphan")
class ChecklistItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question = db.Column(db.String(500), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('checklist_category.id'), nullable=False)
    points = db.Column(db.Integer, nullable=False, default=0)
class Inspection(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    branch_id = db.Column(db.Integer, db.ForeignKey('branch.id'), nullable=False)
    inspector_name = db.Column(db.String(100), nullable=False)
    inspection_date = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    responses = db.relationship('InspectionResponse', backref='inspection', lazy=True, cascade="all, delete-orphan")
class InspectionResponse(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    inspection_id = db.Column(db.Integer, db.ForeignKey('inspection.id'), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey('checklist_item.id'), nullable=False)
    item = db.relationship('ChecklistItem', backref='responses')
    response = db.Column(db.String(10), nullable=False)
    notes = db.Column(db.String(500))


# --- Helper Function for Score Calculation ---
def _calculate_inspection_results(inspection):
    results = {'categories': {}, 'total_scored': 0, 'total_possible': 0, 'percentage': 0}
    for response in inspection.responses:
        category_name = response.item.category.name
        if category_name not in results['categories']:
            results['categories'][category_name] = {'items': [], 'scored': 0, 'possible': 0}
        scored_points = response.item.points if response.response == 'Pass' else 0
        possible_points = response.item.points
        results['categories'][category_name]['items'].append({
            'question': response.item.question, 'response': response.response,
            'notes': response.notes, 'points': possible_points, 'scored_points': scored_points
        })
        results['categories'][category_name]['scored'] += scored_points
        results['categories'][category_name]['possible'] += possible_points
        results['total_scored'] += scored_points
        results['total_possible'] += possible_points
    if results['total_possible'] > 0:
        results['percentage'] = (results['total_scored'] / results['total_possible']) * 100
    return results

# --- Application Routes ---

@app.route('/')
def index():
    branches = Branch.query.order_by(Branch.name).all()
    return render_template_string(INDEX_HTML, branches=branches)

@app.route('/branch/<int:branch_id>')
def branch_dashboard(branch_id):
    branch = Branch.query.get_or_404(branch_id)
    # Get all inspections for the list view (newest first)
    inspections_desc = Inspection.query.filter_by(branch_id=branch_id).order_by(Inspection.inspection_date.desc()).all()
    
    # Get last 10 inspections for the chart (oldest first)
    inspections_asc = Inspection.query.filter_by(branch_id=branch_id).order_by(Inspection.inspection_date.asc()).limit(10).all()
    
    chart_labels = [insp.inspection_date.strftime('%b %d') for insp in inspections_asc]
    chart_data = [_calculate_inspection_results(insp)['percentage'] for insp in inspections_asc]
    
    return render_template_string(BRANCH_DASHBOARD_HTML, branch=branch, inspections=inspections_desc, chart_labels=chart_labels, chart_data=chart_data)

@app.route('/start_inspection/<int:branch_id>')
def start_inspection(branch_id):
    branch = Branch.query.get_or_404(branch_id)
    categories = ChecklistCategory.query.order_by(ChecklistCategory.id).all()
    return render_template_string(INSPECTION_FORM_HTML, branch=branch, categories=categories)

@app.route('/submit_inspection/<int:branch_id>', methods=['POST'])
def submit_inspection(branch_id):
    inspector_name = request.form['inspector_name']
    new_inspection = Inspection(branch_id=branch_id, inspector_name=inspector_name)
    db.session.add(new_inspection)
    db.session.commit()
    for item_id_str in request.form.getlist('item_ids'):
        item_id = int(item_id_str)
        response_value = request.form.get(f'response_{item_id}')
        notes_value = request.form.get(f'notes_{item_id}')
        new_response = InspectionResponse(
            inspection_id=new_inspection.id, item_id=item_id,
            response=response_value, notes=notes_value
        )
        db.session.add(new_response)
    db.session.commit()
    return redirect(url_for('branch_dashboard', branch_id=branch_id))

@app.route('/inspection/<int:inspection_id>')
def view_inspection(inspection_id):
    inspection = Inspection.query.get_or_404(inspection_id)
    results = _calculate_inspection_results(inspection)
    return render_template_string(INSPECTION_RESULTS_HTML, inspection=inspection, results=results)


def setup_database(app):
    with app.app_context():
        db.create_all()
        if Branch.query.first():
            print("Database already populated.")
            return

        print("Populating database with initial data...")
        branches = [
            Branch(name='Dammam Uhud', location='Dammam'), Branch(name='Riyadh Dahrat Laban', location='Riyadh'),
            Branch(name='Riyadh Al Rayan', location='Riyadh'), Branch(name='Riyadh Boulevard', location='Riyadh'),
            Branch(name='Riyadh Malqa', location='Riyadh'), Branch(name='Jubail Fanateer', location='Jubail'),
            Branch(name='Al Ahssa Hofuf', location='Al Ahssa'), Branch(name='Khobar Al Shamaliya', location='Khobar'),
            Branch(name='Qatif Tarot Island', location='Qatif'),
        ]
        db.session.bulk_save_objects(branches)
        
        cat_ss, cat_bs, cat_br = ChecklistCategory(name='Small Sandwiches'), ChecklistCategory(name='Big Sandwiches'), ChecklistCategory(name='Broasted')
        cat_bev, cat_fr, cat_des, cat_misc = ChecklistCategory(name='Beverages'), ChecklistCategory(name='Fries/Fancy/Curly/Onion Rings'), ChecklistCategory(name='Deserts'), ChecklistCategory(name='Miscellaneous')
        db.session.add_all([cat_ss, cat_bs, cat_br, cat_bev, cat_fr, cat_des, cat_misc])
        db.session.commit()

        items = [
            ChecklistItem(question='Procedures: Are the procedures within standards?', category_id=cat_ss.id, points=25),
            ChecklistItem(question='Procedures: Center Dressing, Bun toasting etc.?', category_id=cat_ss.id, points=25),
            ChecklistItem(question='TEMPERATURE: Is it HOT? Internal temperature?', category_id=cat_ss.id, points=25),
            ChecklistItem(question='TEMPERATURE: Condiments not cold', category_id=cat_ss.id, points=25),
            ChecklistItem(question='TASTE: Is it fresh?', category_id=cat_ss.id, points=20),
            ChecklistItem(question='APPEARANCE: Clean Packaging, Pretty & Appetizing', category_id=cat_ss.id, points=20),
            ChecklistItem(question='APPEARANCE: Color, Neat Dressing', category_id=cat_ss.id, points=20),
            ChecklistItem(question='PREPERATION TIME: Not exceeding 4 minutes- total time', category_id=cat_ss.id, points=20),
            ChecklistItem(question='Procedures: Are the procedures within standards?', category_id=cat_bs.id, points=25),
            ChecklistItem(question='Procedures: Center Dressing, Bun toasting etc.?', category_id=cat_bs.id, points=25),
            ChecklistItem(question='TEMPERATURE: Is it HOT? Internal temperature?', category_id=cat_bs.id, points=20),
            ChecklistItem(question='TEMPERATURE: Condiments not cold', category_id=cat_bs.id, points=20),
            ChecklistItem(question='TASTE: Is it fresh?', category_id=cat_bs.id, points=20),
            ChecklistItem(question='APPEARANCE: Clean Packaging, Pretty & Appetizing', category_id=cat_bs.id, points=20),
            ChecklistItem(question='APPEARANCE: Color, Neat Dressing', category_id=cat_bs.id, points=20),
            ChecklistItem(question='PREPERATION TIME: Not exceeding 8 minutes-total time', category_id=cat_bs.id, points=20),
            ChecklistItem(question='Procedures: Are the procedures within standards?', category_id=cat_br.id, points=25),
            ChecklistItem(question='Procedures: Center Dressing, Bun toasting etc.?', category_id=cat_br.id, points=25),
            ChecklistItem(question='TEMPERATURE: Is it HOT? Internal temperature?', category_id=cat_br.id, points=20),
            ChecklistItem(question='TEMPERATURE: Condiments not cold', category_id=cat_br.id, points=20),
            ChecklistItem(question='TASTE: Is it fresh?', category_id=cat_br.id, points=20),
            ChecklistItem(question='APPEARANCE: Clean Packaging, Pretty & Appetizing', category_id=cat_br.id, points=20),
            ChecklistItem(question='APPEARANCE: Color, Neat Dressing', category_id=cat_br.id, points=20),
            ChecklistItem(question='PREPERATION TIME: Not exceeding 15 minutes-total time', category_id=cat_br.id, points=20),
            ChecklistItem(question='PROCEDURES: Are the procedures within standards?', category_id=cat_bev.id, points=25),
            ChecklistItem(question='TEMPERATURE: Amount of ice? Hot or Cold?', category_id=cat_bev.id, points=20),
            ChecklistItem(question='TASTE: Calibration?', category_id=cat_bev.id, points=20),
            ChecklistItem(question='APPEARANCE: Clean packaging, properly sealed without spills', category_id=cat_bev.id, points=15),
            ChecklistItem(question='PREPERATION TIME: Draw as needed. No Pre-drawing', category_id=cat_bev.id, points=15),
            ChecklistItem(question='PROCEDURES: Are the procedures within standards? Right Amount?', category_id=cat_fr.id, points=25),
            ChecklistItem(question='TEMPERATURE: Is it HOT?', category_id=cat_fr.id, points=25),
            ChecklistItem(question='TASTE: Is it fresh? Crisp? Properly salted', category_id=cat_fr.id, points=20),
            ChecklistItem(question='APPEARANCE: Clean Packaging, Pretty & Appetizing, Color, Not greasy', category_id=cat_fr.id, points=15),
            ChecklistItem(question='HOLDING TIME: Within prescribed time - fries 5 mins, Fancy/Curly/Onion 5 mins', category_id=cat_fr.id, points=15),
            ChecklistItem(question='PROCEDURES: Are the procedures within standards? Right Quantity?', category_id=cat_des.id, points=25),
            ChecklistItem(question='TEMPERATURE: Correct Temperature?', category_id=cat_des.id, points=20),
            ChecklistItem(question='TASTE: Texture', category_id=cat_des.id, points=20),
            ChecklistItem(question='APPEARANCE: Clean & Neat Packaging, Color, Nice & Appetizing', category_id=cat_des.id, points=15),
            ChecklistItem(question='HOLDING TIME: Within prescribe time (apple pie 1.5 hours; include 20 mins cooling)', category_id=cat_des.id, points=15),
            ChecklistItem(question='All product within proper shelf life', category_id=cat_misc.id, points=25),
            ChecklistItem(question='Prepared products are labeled', category_id=cat_misc.id, points=25),
            ChecklistItem(question='Hand washing procedures followed at least every hour', category_id=cat_misc.id, points=20),
            ChecklistItem(question='Gloves & apron are being used', category_id=cat_misc.id, points=15),
            ChecklistItem(question='Preparation chart updated and labeling used', category_id=cat_misc.id, points=15),
            ChecklistItem(question='Sanitation system in use & implemented', category_id=cat_misc.id, points=15),
        ]
        db.session.bulk_save_objects(items)
        db.session.commit()
        print("Initial data added successfully.")

# --- Main execution block ---
if __name__ == '__main__':
    setup_database(app)
    app.run(debug=True, host='0.0.0.0')