from flask import Flask, request, jsonify, send_from_directory
import json, os

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

    VALID_COLUMNS = {"social", "application", "decision", "middleware", "data", "sensing", "physical"}

    if not tactic_id or column not in VALID_COLUMNS or not entry:
        return jsonify({'error': 'Missing or invalid fields'}), 400

    # Find the row by id (not by tactic label)
    row = next((r for r in data if r.get('id') == tactic_id), None)
    if row is None:
        # Do NOT create a new row; this indicates a mismatch in IDs
        return jsonify({'error': f'Tactic id not found: {tactic_id}'}), 404

    # Ensure the cell is a list, then append
    cell = row.get(column, [])
    if isinstance(cell, list):
        cell.append(entry)
        row[column] = cell
    elif isinstance(cell, str) and cell.strip():
        # migrate old string cell to list
        row[column] = [cell.strip(), entry]
    else:
        row[column] = [entry]

    save_data(data)
    return jsonify({'status': 'ok', 'message': f'Added "{entry}" under {column} for {row.get("tactic", tactic_id)}.'})

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)
