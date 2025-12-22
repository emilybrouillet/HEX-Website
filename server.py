from flask import Flask, request, jsonify, send_from_directory
import json, os
import re

app = Flask(__name__, static_folder='.', static_url_path='')

DATA_FILE = 'matrixData.json'

# ---------- Helpers ----------

def load_data():
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def slugify(text):
    return re.sub(r'[^a-z0-9]+', '-', text.lower()).strip('-')

# ---------- Routes ----------

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/<path:path>')
def static_proxy(path):
    # Serve CSS, JS, and other static files
    return send_from_directory('.', path)

@app.route('/api/data', methods=['GET'])
def get_data():
    return jsonify(load_data())

@app.route('/api/submit', methods=['POST'])
def submit_entry():
    data = load_data()
    payload = request.get_json(force=True) or {}

    tactic_id = payload.get('tacticId') or payload.get('tactic')  # supports old clients
    column = payload.get('column')
    entry = (payload.get('entry') or '').strip()
    description = (payload.get('description') or '').strip()

    VALID_COLUMNS = {"social", "application", "decision", "middleware", "data", "sensing", "physical"}
    COLUMN_LABELS = {
        "social": "Social Interface",
        "application": "Application",
        "decision": "Decision-making",
        "middleware": "Middleware",
        "data": "Data Processing",
        "sensing": "Sensing & Perception",
        "physical": "Physical"
    }

    if not tactic_id or column not in VALID_COLUMNS or not entry:
        return jsonify({'error': 'Missing or invalid fields'}), 400

    # Find the row by id
    row = next((r for r in data if r.get('id') == tactic_id), None)
    if row is None:
        return jsonify({'error': f'Tactic id not found: {tactic_id}'}), 404

    cell = row.get(column)

    # Normalize old formats to a list of objects
    if cell is None or cell == "":
        cell_list = []
    elif isinstance(cell, list):
        cell_list = cell
    elif isinstance(cell, str):
        # old single-string cell -> convert to one object
        cell_list = [{
            "id": slugify(cell.strip()),
            "title": cell.strip(),
            "description": "",
            "notes": ""
        }]
    else:
        # unexpected type -> stringify it
        cell_list = [{
            "id": slugify(str(cell)),
            "title": str(cell),
            "description": "",
            "notes": ""
        }]

    # Append the new entry as an object
    cell_list.append({
        "id": slugify(entry),
        "title": entry,
        "description": description,
        "notes": ""
    })

    row[column] = cell_list
    save_data(data)

    layer_name = COLUMN_LABELS.get(column, column)
    return jsonify({
        'status': 'ok',
        'message': f'Added "{entry}" under {layer_name} for {row.get("tactic", tactic_id)}.'
    })

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)
