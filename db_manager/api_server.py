from flask import Flask, request, jsonify
import sqlite3
from datetime import datetime
from flask_cors import CORS
from dotenv import load_dotenv
import os

load_dotenv()


app = Flask(__name__)
CORS(app)

# Database setup
def init_db():
    conn = sqlite3.connect('ctf.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS teams
                 (id INTEGER PRIMARY KEY, name TEXT UNIQUE)''')
    c.execute('''CREATE TABLE IF NOT EXISTS services
                 (id INTEGER PRIMARY KEY, name TEXT UNIQUE)''')
    c.execute('''CREATE TABLE IF NOT EXISTS flags
                 (id INTEGER PRIMARY KEY, team_id INTEGER, service_id INTEGER, 
                  flag TEXT, timestamp DATETIME)''')
    c.execute('''CREATE TABLE IF NOT EXISTS service_status
                 (id INTEGER PRIMARY KEY, team_id INTEGER, service_id INTEGER, 
                  status TEXT, timestamp DATETIME)''')
    c.execute('''CREATE TABLE IF NOT EXISTS score_events
                 (id INTEGER PRIMARY KEY, team_id INTEGER, points INTEGER, 
                  reason TEXT, timestamp DATETIME)''')
    conn.commit()
    conn.close()

init_db()

# Helper functions
def get_db():
    conn = sqlite3.connect('ctf.db')
    conn.row_factory = sqlite3.Row
    return conn

# API Routes
@app.route('/team', methods=['POST'])
def add_team():
    team_name = request.json['name']
    db = get_db()
    cursor = db.cursor()
    cursor.execute('INSERT INTO teams (name) VALUES (?)', (team_name,))
    db.commit()
    return jsonify({'id': cursor.lastrowid, 'name': team_name}), 201

@app.route('/service', methods=['POST'])
def add_service():
    service_name = request.json['name']
    db = get_db()
    cursor = db.cursor()
    cursor.execute('INSERT INTO services (name) VALUES (?)', (service_name,))
    db.commit()
    return jsonify({'id': cursor.lastrowid, 'name': service_name}), 201

@app.route('/flag', methods=['POST'])
def set_flag():
    team_id = request.json['team_id']
    service_id = request.json['service_id']
    flag = request.json['flag']
    timestamp = datetime.now()
    db = get_db()
    cursor = db.cursor()
    cursor.execute('INSERT INTO flags (team_id, service_id, flag, timestamp) VALUES (?, ?, ?, ?)',
                   (team_id, service_id, flag, timestamp))
    db.commit()
    return jsonify({'status': 'success'}), 201

@app.route('/status', methods=['POST'])
def update_service_status():
    team_id = request.json['team_id']
    service_id = request.json['service_id']
    status = request.json['status']
    timestamp = datetime.now()
    db = get_db()
    cursor = db.cursor()
    cursor.execute('INSERT INTO service_status (team_id, service_id, status, timestamp) VALUES (?, ?, ?, ?)',
                   (team_id, service_id, status, timestamp))
    db.commit()
    return jsonify({'status': 'success'}), 201

@app.route('/score', methods=['POST'])
def update_score():
    team_id = request.json['team_id']
    points = request.json['points']
    reason = request.json['reason']
    timestamp = datetime.now()
    db = get_db()
    cursor = db.cursor()
    cursor.execute('INSERT INTO score_events (team_id, points, reason, timestamp) VALUES (?, ?, ?, ?)',
                   (team_id, points, reason, timestamp))
    db.commit()
    return jsonify({'status': 'success'}), 201

@app.route('/scoreboard')
def get_scoreboard():
    db = get_db()
    cursor = db.cursor()
    
    # Get team scores
    cursor.execute('''
        SELECT teams.id, teams.name, COALESCE(SUM(score_events.points), 0) as total_score
        FROM teams
        LEFT JOIN score_events ON teams.id = score_events.team_id
        GROUP BY teams.id
        ORDER BY total_score DESC
    ''')
    teams = cursor.fetchall()
    
    # Get all services
    cursor.execute('SELECT id, name FROM services')
    services = cursor.fetchall()
    
    scoreboard = []
    for team in teams:
        team_data = dict(team)
        team_data['services'] = {}
        
        # Get latest status for each service for this team
        for service in services:
            cursor.execute('''
                SELECT status
                FROM service_status
                WHERE team_id = ? AND service_id = ?
                ORDER BY timestamp DESC
                LIMIT 1
            ''', (team['id'], service['id']))
            status = cursor.fetchone()
            
            team_data['services'][service['name']] = status['status'] if status else 'unknown'
        
        scoreboard.append(team_data)
    
    # If scoreboard is empty, add some sample data
    if not scoreboard:
        scoreboard = [
            {"id": 1, "name": "Team1", "total_score": 300, "services": {"Service1": "up", "Service2": "down"}},
            {"id": 2, "name": "Team2", "total_score": 250, "services": {"Service1": "up", "Service2": "up"}},
        ]
    
    return jsonify(scoreboard)

if __name__ == '__main__':
    app.run(port=int(os.getenv('API_PORT', 5000)))
