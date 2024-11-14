from flask import Flask, request, jsonify
import sqlite3
from datetime import datetime
from flask_cors import CORS
from contextlib import contextmanager
import threading
import time
import os

class CTFDatabase:
    def __init__(self, db_path='ctf.db'):
        self.db_path = db_path
        self.init_db()

    @contextmanager
    def get_db(self):
        conn = sqlite3.connect(self.db_path, timeout=60.0)  # Increased timeout
        conn.row_factory = sqlite3.Row
        try:
            # Enable WAL mode for better concurrency
            conn.execute('PRAGMA journal_mode=WAL')
            conn.execute('PRAGMA busy_timeout=60000')  # 60 second timeout
            yield conn
            conn.commit()
        finally:
            conn.close()

    def init_db(self):
        """Initialize database tables"""
        with self.get_db() as conn:
            c = conn.cursor()

            # Teams table
            c.execute('''CREATE TABLE IF NOT EXISTS teams
                        (id INTEGER PRIMARY KEY,
                         name TEXT UNIQUE NOT NULL,
                         score INTEGER DEFAULT 0)''')

            # Services table
            c.execute('''CREATE TABLE IF NOT EXISTS services
                        (id INTEGER PRIMARY KEY,
                         name TEXT UNIQUE NOT NULL,
                         port INTEGER NOT NULL,
                         timeout INTEGER NOT NULL,
                         checker_host TEXT NOT NULL,
                         checker_port INTEGER NOT NULL)''')

            # Current service status
            c.execute('''CREATE TABLE IF NOT EXISTS current_status
                        (team_id INTEGER NOT NULL,
                         service_id INTEGER NOT NULL,
                         status TEXT NOT NULL,
                         last_updated DATETIME NOT NULL,
                         PRIMARY KEY (team_id, service_id),
                         FOREIGN KEY (team_id) REFERENCES teams(id),
                         FOREIGN KEY (service_id) REFERENCES services(id))''')

            # Rounds table - for flag generation cycles
            c.execute('''CREATE TABLE IF NOT EXISTS rounds
                        (id INTEGER PRIMARY KEY,
                         start_time DATETIME NOT NULL,
                         round_number INTEGER NOT NULL,
                         finished BOOLEAN NOT NULL DEFAULT 0)''')

            # Current flags table
            c.execute('''CREATE TABLE IF NOT EXISTS current_flags
                        (flag TEXT PRIMARY KEY,
                         round_id INTEGER NOT NULL,
                         team_id INTEGER NOT NULL,
                         service_id INTEGER NOT NULL,
                         timestamp DATETIME NOT NULL,
                         FOREIGN KEY (round_id) REFERENCES rounds(id),
                         FOREIGN KEY (team_id) REFERENCES teams(id),
                         FOREIGN KEY (service_id) REFERENCES services(id))''')

class TeamManager:
    def __init__(self, db: CTFDatabase):
        self.db = db

    def add_team(self, name: str) -> dict:
        """Add a new team"""
        with self.db.get_db() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute('INSERT INTO teams (name) VALUES (?)', (name,))
                return {
                    'id': cursor.lastrowid,
                    'name': name,
                    'score': 0
                }
            except sqlite3.IntegrityError:
                raise ValueError('Team name already exists')

    def get_teams(self) -> list:
        """Get all teams"""
        with self.db.get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT id, name, score FROM teams')
            return [dict(row) for row in cursor.fetchall()]

class ServiceManager:
    def __init__(self, db: CTFDatabase):
        self.db = db

    def add_service(self, name: str, port: int, timeout: int,
                   checker_host: str, checker_port: int) -> dict:
        """Add a new service"""
        with self.db.get_db() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute('''
                    INSERT INTO services
                    (name, port, timeout, checker_host, checker_port)
                    VALUES (?, ?, ?, ?, ?)''',
                    (name, port, timeout, checker_host, checker_port))
                return {
                    'id': cursor.lastrowid,
                    'name': name
                }
            except sqlite3.IntegrityError:
                raise ValueError('Service name already exists')

    def update_status(self, team_id: int, service_id: int,
                     status: str) -> dict:
        """Update service status"""
        timestamp = datetime.now()

        with self.db.get_db() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                INSERT OR REPLACE INTO current_status
                (team_id, service_id, status, last_updated)
                VALUES (?, ?, ?, ?)
            """, (team_id, service_id, status, timestamp))

            return {
                'status': 'success',
                'team_id': team_id,
                'service_id': service_id,
                'current_status': status
            }

class FlagManager:
    def __init__(self, db: CTFDatabase):
        self.db = db

    def clean_expired_flags(self) -> None:
        """Clean up expired flags, keeping only last 3 rounds"""
        with self.db.get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                DELETE FROM current_flags
                WHERE round_id NOT IN (
                    SELECT id FROM rounds
                    ORDER BY round_number DESC
                    LIMIT 3
                )
            """)
    def dump_flags(self) -> list:
        """Dump all flags with their details"""
        with self.db.get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT
                    f.flag,
                    t.name as team_name,
                    s.name as service_name,
                    r.round_number,
                    f.timestamp
                FROM current_flags f
                JOIN teams t ON f.team_id = t.id
                JOIN services s ON f.service_id = s.id
                JOIN rounds r ON f.round_id = r.id
                ORDER BY r.round_number, t.name, s.name
            """)
            return [dict(row) for row in cursor.fetchall()]

    def generate_flag(self) -> str:
        """Generate a new flag"""
        import secrets
        return f"FLAG{{{secrets.token_hex(16)}}}"

    def submit_flag(self, submitting_team_id: int, flag: str) -> dict:
        """Handle flag submission"""
        with self.db.get_db() as conn:
            cursor = conn.cursor()

            # Find flag and its owner from last 3 rounds
            cursor.execute("""
                SELECT
                    f.team_id as owner_team_id,
                    f.service_id,
                    s.name as service_name
                FROM current_flags f
                JOIN services s ON f.service_id = s.id
                JOIN rounds r ON f.round_id = r.id
                WHERE f.flag = ?
                AND r.id IN (
                    SELECT id FROM rounds
                    ORDER BY round_number DESC
                    LIMIT 3
                )
            """, (flag,))

            flag_info = cursor.fetchone()

            if not flag_info:
                raise ValueError('Invalid or expired flag')

            if flag_info['owner_team_id'] == submitting_team_id:
                raise ValueError('Cannot submit your own flag')

            # Award points and update team score
            cursor.execute("""
                UPDATE teams
                SET score = score + 100
                WHERE id = ?
            """, (submitting_team_id,))

            return {
                'status': 'success',
                'message': 'Flag accepted',
                'points': 100,
                'service': flag_info['service_name']
            }

class GameController:
    def __init__(self, db: CTFDatabase, tick_interval: int = 180):
        self.db = db
        self.tick_interval = tick_interval
        self.running = False
        self.flag_manager = FlagManager(db)
        self._round_lock = threading.Lock()

    def start_new_round(self) -> int:
        """Start a new round and return its ID"""
        with self._round_lock:  # Ensure only one round can start at a time
            with self.db.get_db() as conn:
                cursor = conn.cursor()

                # Mark previous round as finished
                cursor.execute("UPDATE rounds SET finished = 1 WHERE finished = 0")
                conn.commit()  # Commit this change immediately

                # Get next round number
                cursor.execute("""
                    SELECT COALESCE(MAX(round_number), 0) + 1
                    FROM rounds
                """)
                next_round = cursor.fetchone()[0]

                # Start new round
                timestamp = datetime.now()
                cursor.execute("""
                    INSERT INTO rounds (start_time, round_number, finished)
                    VALUES (?, ?, 0)
                """, (timestamp, next_round))
                conn.commit()  # Commit the new round immediately

                round_id = cursor.lastrowid

                # Only clean up flags older than 3 rounds
                self.flag_manager.clean_expired_flags()

                return round_id

    def generate_flags(self, round_id: int):
        """Generate new flags for all teams and services"""
        with self.db.get_db() as conn:
            cursor = conn.cursor()

            cursor.execute("SELECT id FROM teams")
            teams = cursor.fetchall()

            cursor.execute("SELECT id FROM services")
            services = cursor.fetchall()

            timestamp = datetime.now()
            for team in teams:
                for service in services:
                    flag = self.flag_manager.generate_flag()
                    cursor.execute("""
                        INSERT INTO current_flags
                        (flag, round_id, team_id, service_id, timestamp)
                        VALUES (?, ?, ?, ?, ?)
                    """, (flag, round_id, team['id'], service['id'], timestamp))

    def run_tick(self):
        """Run one complete tick of the CTF"""
        try:
            round_id = self.start_new_round()
            print(f"Started round {round_id}")

            self.generate_flags(round_id)
            print("Generated flags")

        except Exception as e:
            print(f"Error in tick: {e}")

    def run(self):
        """Main game loop"""
        self.running = True
        while self.running:
            self.run_tick()
            time.sleep(self.tick_interval)

    def start(self):
        """Start the game loop in a separate thread"""
        thread = threading.Thread(target=self.run)
        thread.daemon = True
        thread.start()

    def stop(self):
        """Stop the game loop"""
        self.running = False

class CTFServer:
    def __init__(self, db_path='ctf.db'):
        self.db = CTFDatabase(db_path)
        self.team_manager = TeamManager(self.db)
        self.service_manager = ServiceManager(self.db)
        self.flag_manager = FlagManager(self.db)
        self.game_controller = GameController(self.db)

        self.app = Flask(__name__)
        CORS(self.app)
        self.setup_routes()

    def setup_routes(self):
        @self.app.route('/team', methods=['POST'])
        def add_team():
            try:
                return jsonify(self.team_manager.add_team(
                    request.json['name']
                )), 201
            except ValueError as e:
                return jsonify({'error': str(e)}), 400

        @self.app.route('/teams', methods=['GET'])
        def get_teams():
            return jsonify(self.team_manager.get_teams())

        @self.app.route('/submit_flag', methods=['POST'])
        def submit_flag():
            try:
                return jsonify(self.flag_manager.submit_flag(
                    request.json['team_id'],
                    request.json['flag']
                ))
            except ValueError as e:
                return jsonify({
                    'status': 'error',
                    'message': str(e)
                }), 400

        @self.app.route('/scoreboard')
        def get_scoreboard():
            teams = self.team_manager.get_teams()
            for team in teams:
                team['services'] = {}
                with self.db.get_db() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        SELECT s.name, cs.status
                        FROM services s
                        LEFT JOIN current_status cs
                            ON cs.service_id = s.id
                            AND cs.team_id = ?
                    ''', (team['id'],))
                    services = cursor.fetchall()
                    for service in services:
                        team['services'][service['name']] = (
                            service['status'] if service['status'] else 'unknown'
                        )
            return jsonify(teams)

    def start(self, port=5000):
        """Start the CTF server"""
        self.game_controller.start()
        self.app.run(port=port)
#
# if __name__ == '__main__':
#     ctf_server = CTFServer()
#     ctf_server.start(port=int(os.getenv('API_PORT', 5000)))
