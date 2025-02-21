from flask import Flask, request, jsonify, render_template
import threading
from database_operations import DatabaseOperations
from contextlib import contextmanager
import os

app = Flask(__name__, 
    template_folder=os.path.join(os.path.dirname(__file__), 'templates'),
    static_folder=os.path.join(os.path.dirname(__file__), 'static'))

class ScoreboardOperations:
    def __init__(self,db):
        self.db = db
        self.current_tick = 1 
        self.submitted_flags = {}  # {tick: {flag: set(team_ids)}}
        self.flag_lock = threading.Lock()  # Lock for thread-safe operations
        self.api_thread = threading.Thread(target=self._run_api)
        self.api_thread.daemon = True
        self.api_thread.start()

    def _run_api(self):
        # ScoreboardOperations instance available to Flask
        app.scoreboard = self
        app.run(host='0.0.0.0', port=9090)


    def set_tick(self, tick):
        with self.flag_lock:
            if tick != self.current_tick:
                self.submitted_flags = {}
            self.current_tick = tick

@app.route('/submit_flags', methods=['POST'])
def submit_flags():
    try:
        data = request.get_json()
        if not data or 'flags' not in data or 'team_id' not in data:
            return jsonify({'error': 'Missing required fields'}), 400

        flags = data['flags']
        team_id = data['team_id']
        current_tick = app.scoreboard.current_tick
        
        if not isinstance(flags, list):
            return jsonify({'error': 'Flags must be provided as an array'}), 400

        valid_flags = 0
        with app.scoreboard.flag_lock:
            if current_tick not in app.scoreboard.submitted_flags:
                app.scoreboard.submitted_flags[current_tick] = {}

        with app.scoreboard.db.get_db() as conn:
            c = conn.cursor()
            
            # Check if flag exists and matches the current round and same team for now(changed)
            for flag in flags:
                with app.scoreboard.flag_lock:
                    if (flag in app.scoreboard.submitted_flags[current_tick] and 
                        team_id in app.scoreboard.submitted_flags[current_tick][flag]):
                        continue

                    c.execute('''
                        SELECT * FROM current_flags 
                        WHERE flag = ? AND round_id = ? AND team_id != ?
                    ''', (flag, current_tick, team_id))
                    
                    result = c.fetchone()
                    if result:
                        # Ensure multiple submissions of flag from same team is not accepted
                        if flag not in app.scoreboard.submitted_flags[current_tick]:
                            app.scoreboard.submitted_flags[current_tick][flag] = set()
                        app.scoreboard.submitted_flags[current_tick][flag].add(team_id)
                        valid_flags += 1
            
            # Add attack points instead of directly updating score
            if valid_flags > 0:
                app.scoreboard.db.add_attack_points(team_id, valid_flags)
            conn.commit()

        return jsonify({
            'success': True,
            'valid_flags': valid_flags,
            'current_tick': current_tick,
            'message': f'Successfully processed {valid_flags} valid flags'
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/scoreboard', methods=['GET'])
def get_scoreboard():
    try:
        with app.scoreboard.db.get_db() as conn:
            c = conn.cursor()
            
            c.execute('''
                SELECT id, name, score 
                FROM teams 
                ORDER BY score DESC
            ''')
            teams = [dict(row) for row in c.fetchall()]
            
            c.execute('SELECT name FROM services')
            services = [dict(row)['name'] for row in c.fetchall()]
            
            scoreboard_data = []
            for team in teams:
                team_data = {
                    'team_id': team['id'],
                    'team_name': team['name'],
                    'score': team['score'],
                    'services': {}
                }
                
                c.execute('''
                    SELECT service_name, status, last_updated 
                    FROM current_status 
                    WHERE team_id = ?
                ''', (team['id'],))
                
                service_statuses = c.fetchall()
                for service in service_statuses:
                    team_data['services'][service['service_name']] = {
                        'status': service['status'],
                        'last_updated': service['last_updated']
                    }
                
                scoreboard_data.append(team_data)
            
            return jsonify({
                'current_tick': app.scoreboard.current_tick,
                'teams': scoreboard_data,
                'services': services
            })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/')
def index():
    return render_template('scoreboard.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=9090)
