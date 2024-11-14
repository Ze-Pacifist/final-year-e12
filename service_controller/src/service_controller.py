import os
import subprocess
import time
from database_operations import CTFDatabase
from scoreboard_operations import ScoreboardOperations

class ServiceController:
    def __init__(self):
        self.db = DatabaseOperations()
        self.scoreboard = ScoreboardOperations()
        self.tick_interval = int(os.getenv('TICK_INTERVAL', 180))  # Default to 3 minutes
        self.num_teams = int(os.getenv('NUM_TEAMS', 2))  # Default to 2 teams

    def run_healthchecks(self):
        checker_dir = 'checkers'
        tick = 1
        while True:
            print(f"\n--- Tick {tick} ---")
            for checker in os.listdir(checker_dir):
                if checker.endswith('_checker.py'):
                    service_name = checker.replace('_checker.py', '')
                    print(f"\nChecking {service_name}:")
                    for team in range(1, self.num_teams + 1):
                        result = self.run_checker(os.path.join(checker_dir, checker), team)
                        self.update_service_status(service_name, result, team)
            tick += 1
            time.sleep(self.tick_interval)

    def run_checker(self, checker_path, team):
        service_name = os.path.basename(checker_path).replace('_checker.py', '')
        port = 3000 if service_name == 'node_challenge' else 5000
        result = subprocess.run(['python', checker_path, f'team{team}', f'{port}'], capture_output=True, text=True)
        return result.stdout.strip()

    def update_service_status(self, service_name, status, team):
        print(f"  Team {team}: {status}")
        self.db.update_service_status(service_name, status, team)
        self.scoreboard.update_scoreboard(service_name, status, team)

if __name__ == '__main__':
    controller = ServiceController()
    controller.run_healthchecks()
