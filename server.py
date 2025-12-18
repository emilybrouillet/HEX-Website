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
    payload = request.get_json(force=True)

    tactic = payload.get('tactic')
    column = payload.get('column')
    entry = payload.get('entry')

    if not all([tactic, column, entry]):
        return jsonify({'error': 'Missing required fields'}), 400

    # Find the tactic
    for row in data:
        if row['tactic'] == tactic:
            val = row.get(column)
            if isinstance(val, list):
                val.append(entry)
            elif isinstance(val, str) and val:
                row[column] = [val, entry]
            else:
                row[column] = [entry]
            break
    else:
        # Create new row if tactic not found
        data.append({
            'tactic': tactic,
            column: [entry]
        })

    save_data(data)
    return jsonify({'status': 'ok', 'message': f'Added "{entry}" under {column} for {tactic}.'})

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)
