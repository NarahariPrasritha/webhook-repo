from flask import Flask, request, jsonify
from pymongo import MongoClient
from datetime import datetime

app = Flask(__name__)

# Connect to MongoDB
client = MongoClient('mongodb://localhost:27017/')  # replace with your MongoDB URI if on Atlas
db = client['github_events']
collection = db['events']

# Webhook endpoint to receive events
@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    print("Received data:", data)

    action_type = None
    author = None
    from_branch = None
    to_branch = None

    # Handling different event types
    if 'commits' in data:
        action_type = 'push'
        author = data['pusher']['name']
        to_branch = data['ref'].split('/')[-1]
    elif 'pull_request' in data:
        pr_action = data['action']
        if pr_action == 'opened':
            action_type = 'pull_request'
        elif pr_action == 'closed' and data['pull_request']['merged']:
            action_type = 'merge'
        author = data['pull_request']['user']['login']
        from_branch = data['pull_request']['head']['ref']
        to_branch = data['pull_request']['base']['ref']

    if action_type:
        event_record = {
            "action": action_type,
            "author": author,
            "from_branch": from_branch,
            "to_branch": to_branch,
            "timestamp": datetime.utcnow().isoformat()
        }
        collection.insert_one(event_record)
        return jsonify({"message": "Event received and saved!"}), 200
    else:
        return jsonify({"message": "Event type not handled."}), 400

# GET API to fetch events
@app.route('/get-events', methods=['GET'])
def get_events():
    events = list(collection.find({}, {'_id': 0}))
    return jsonify(events)

if __name__ == '__main__':
    app.run(debug=True)
