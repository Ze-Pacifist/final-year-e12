import sqlite3
from datetime import datetime
from contextlib import contextmanager



class DatabaseOperations:
    def __init__(self, db_path='database/ctf.db'):
        self.db_path = db_path
        self.init_db()

    @contextmanager
    def get_db(self):
        conn = sqlite3.connect(self.db_path, timeout=10.0)
        conn.row_factory = sqlite3.Row
        try:
            conn.execute('PRAGMA journal_mode=WAL')
            # 60 second timeout
            conn.execute('PRAGMA busy_timeout=60000')  
            yield conn
            conn.commit()
        finally:
            conn.close()

    # Initialize database
    def init_db(self):
        return
        with self.get_db() as conn:
            c = conn.cursor()
            # Teams table
            c.execute('''CREATE TABLE IF NOT EXISTS teams
                        (id INTEGER PRIMARY KEY,
                         name TEXT UNIQUE NOT NULL,
                         score INTEGER DEFAULT 0)''')

            # insert default teams
            c.execute('''INSERT INTO teams (name) VALUES ('Team 1')''')

    # Return service names in list format
    def get_services(self):
        with self.get_db() as conn:
            c = conn.cursor()
            c.execute('SELECT name FROM services')
            services = [row['name'] for row in c.fetchall()]
            return services

    # Update current service status to UP or DOWN 
    def update_service_status(self, service_name, status, team):
        with self.get_db() as conn:
            c = conn.cursor()
            c.execute('''UPDATE current_status SET status = ?, last_updated = ? WHERE team_id = ? AND service_name = ?''', (status, datetime.now(), team, service_name))
            conn.commit()

    # Update SLA score if service is UP
    def update_service_score(self, service_name, status, team):
        if status.upper() == "UP":
            with self.get_db() as conn:
                c = conn.cursor()
                c.execute('''UPDATE teams SET score = score + 1 WHERE id = ?''', (team,))
                conn.commit()
                print(f"Added 1 point to Team {team} for {service_name} being UP")

    # Insert generated flags into database
    def insert_flag(self, service_name,tick, team, flag):
        with self.get_db() as conn:
            c = conn.cursor()
            c.execute('''INSERT INTO current_flags (flag, round_id, team_id, service_name, timestamp) VALUES (?, ?, ?, ?, ?)''', (flag, tick, team, service_name, datetime.now()))
            conn.commit()
