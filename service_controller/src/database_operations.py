import sqlite3
import threading
import time
from datetime import datetime
import os
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
            conn.execute('PRAGMA busy_timeout=60000')  # 60 second timeout
            yield conn
            conn.commit()
        finally:
            conn.close()

    def init_db(self):
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
                         timeout INTEGER NOT NULL)''')

            # Current service status
            c.execute('''CREATE TABLE IF NOT EXISTS current_status
                        (team_id INTEGER NOT NULL,
                         service_name TEXT UNIQUE NOT NULL,
                         status TEXT NOT NULL,
                         last_updated DATETIME NOT NULL,
                         PRIMARY KEY (team_id, service_name),
                         FOREIGN KEY (team_id) REFERENCES teams(id),
                         FOREIGN KEY (service_name) REFERENCES services(name))''')

            # Rounds table - for flag generation cycles - needs to be reconsidered
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
                         service_name TEXT NOT NULL,
                         timestamp DATETIME NOT NULL,
                         FOREIGN KEY (round_id) REFERENCES rounds(id),
                         FOREIGN KEY (team_id) REFERENCES teams(id),
                         FOREIGN KEY (service_name) REFERENCES services(name))''')
            # Inserting teams/services needs to be automated.
            # insert default teams
            c.execute('''INSERT INTO teams (name) VALUES ('Team 1')''')
            # insert default services
            c.execute('''INSERT INTO services (name, port, timeout) VALUES ('python_challenge', 8001, 10), ('node_challenge', 8002, 10)''')
            # insert default current_status
            c.execute('''INSERT INTO current_status (team_id, service_name, status, last_updated) VALUES (1, 'python_challenge', 'up', datetime('now'))''')
            c.execute('''INSERT INTO current_status (team_id, service_name, status, last_updated) VALUES (1, 'node_challenge', 'up', datetime('now'))''')
    def update_service_status(self, service_name, status, team):
        with self.get_db() as conn:
            c = conn.cursor()
            c.execute('''UPDATE current_status SET status = ?, last_updated = ? WHERE team_id = ? AND service_name = ?''', (status, datetime.now(), team, service_name))
            conn.commit()

    def insert_flag(self, service_name,tick, team, flag):
        with self.get_db() as conn:
            c = conn.cursor()
            c.execute('''INSERT INTO current_flags (flag, round_id, team_id, service_name, timestamp) VALUES (?, ?, ?, ?, ?)''', (flag, tick, team, service_name, datetime.now()))
            conn.commit()
