from flask import Flask, request, jsonify
import threading
from database_operations import DatabaseOperations
from contextlib import contextmanager

app = Flask(__name__)

class ScoreboardOperations:
    def __init__(self,db):
        self.db = db
        self.current_tick = 1 
        self.api_thread = threading.Thread(target=self._run_api)
        self.api_thread.daemon = True
        self.api_thread.start()

    def _run_api(self):
        # ScoreboardOperations instance available to Flask
        app.scoreboard = self
        app.run(host='0.0.0.0', port=9090)

    def update_scoreboard(self, service_name, status, team):
        if status.upper() == "UP":
            with self.db.get_db() as conn:
                c = conn.cursor()
                c.execute('''UPDATE teams SET score = score + 1 WHERE id = ?''', (team,))
                conn.commit()
                print(f"Added 1 point to Team {team} for {service_name} being UP")

    def set_tick(self, tick):
        self.current_tick = tick

@app.route('/submit_flags', methods=['POST'])
def submit_flags():
    try:
        data = request.get_json()
        if not data or 'flags' not in data or 'team_id' not in data:
            return jsonify({'error': 'Missing required fields'}), 400

        flags = data['flags']
        team_id = data['team_id']
        current_tick = app.scoreboard.current_tick  # Get current tick from scoreboard instance
        
        if not isinstance(flags, list):
            return jsonify({'error': 'Flags must be provided as an array'}), 400

        valid_flags = 0
        with app.scoreboard.db.get_db() as conn:
            c = conn.cursor()
            
            for flag in flags:
                # Check if flag exists and matches the current round and same team for now(change this)
                c.execute('''
                    SELECT * FROM current_flags 
                    WHERE flag = ? AND round_id = ? AND team_id = ?
                ''', (flag, current_tick, team_id))
                
                result = c.fetchone()
                if result:
                    valid_flags += 1
                    # Update the submitting team's score
                    c.execute('''
                        UPDATE teams 
                        SET score = score + 1 
                        WHERE id = ?
                    ''', (team_id,))
            
            conn.commit()

        return jsonify({
            'success': True,
            'valid_flags': valid_flags,
            'current_tick': current_tick,
            'message': f'Successfully processed {valid_flags} valid flags'
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=9090)
