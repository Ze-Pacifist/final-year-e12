import os
import subprocess
import threading
import time
from database_operations import DatabaseOperations
from scoreboard_operations import ScoreboardOperations

def gen_flag():
    return "flag{" + os.urandom(32).hex() + "}"

class ServiceController:
    def __init__(self):
        self.db = DatabaseOperations()
        self.scoreboard = ScoreboardOperations(self.db)
        self.tick_interval = int(os.getenv('TICK_INTERVAL', 180))  # Default to 3 minutes
        self.num_teams = int(os.getenv('NUM_TEAMS', 2))  # Default to 2 teams

    def run_healthchecks(self):
        checker_dir = 'checkers'
        tick = 1
        while True:
            print(f"\n--- Tick {tick} ---")
            self.scoreboard.set_tick(tick)  # Update tick in scoreboard
            for checker in os.listdir(checker_dir):
                if not checker.endswith('_checker.py'):
                    print("Checker script naming scheme error")
                    continue
                service_name = checker.replace('_checker.py', '')
                print(f"\nChecking {service_name}:")
                threads = []
                for team in range(1, self.num_teams + 1):
                    thread = threading.Thread(
                        target=self.check_team_service,
                        args=(service_name, tick, team, os.path.join(checker_dir, checker))
                    )
                    threads.append(thread)
                    thread.start()
                for thread in threads:
                    thread.join()     
            tick += 1
            time.sleep(self.tick_interval)

# Threaded function to parallelly run healthchecks+flag plant for all teams
    def check_team_service(self, service_name, tick, team, checker_path):
        flag = gen_flag()
        print(f"Team {team} flag: {flag}")
        self.db.insert_flag(service_name, tick, team, flag)
        result = self.run_checker(checker_path, team, flag)
        print(f"Result from team {team} check:", result)
        self.update_service_status(service_name, result, team)

    def run_checker(self, checker_path, team, flag):
        service_name = os.path.basename(checker_path).replace('_checker.py', '')
        result = subprocess.run(['python', checker_path, f'team{team}', flag], capture_output=True, text=True)
        return result.stdout.strip()

# Update database and scoreboard with service status
    def update_service_status(self, service_name, status, team):
        print(f"  Team {team}: {status}")
        self.db.update_service_status(service_name, status, team)
        self.scoreboard.update_scoreboard(service_name, status, team)

if __name__ == '__main__':
    controller = ServiceController()
    controller.run_healthchecks()
