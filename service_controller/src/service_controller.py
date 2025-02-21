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
        # Default to 3 minutes
        self.tick_interval = int(os.getenv('TICK_INTERVAL', 180))  
        # Default to 2 teams
        self.num_teams = int(os.getenv('NUM_TEAMS', 2))  

    def run_healthchecks(self, services):
        checker_dir = 'checkers'
        tick = 1
        while True:
            print(f"\n--- Tick {tick} ---")
            # Update tick in scoreboard
            self.scoreboard.set_tick(tick)  
            start = time.time()
            for service_name in services:
                checker = f"{service_name}_checker.py"
                checker_path = os.path.join(checker_dir, checker)

                # Skip if checker doesn't exist
                if not os.path.exists(checker_path):
                    print(f"Warning: Checker not found for service {service_name}")
                    continue

                print(f"\nChecking {service_name}:")
                threads = []
                for team in range(1, self.num_teams + 1):
                    thread = threading.Thread(
                        target=self.check_team_service,
                        args=(service_name, tick, team, checker_path)
                    )
                    threads.append(thread)
                    thread.start()
                for thread in threads:
                    thread.join()
                    
            end = time.time()
            print(f"\n\n\n[*] Tick #{tick} took {end-start}s for healthcheck\n\n\n", flush=True)

            self.db.calculate_round_score(tick)
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

    # Execute healthcheck script
    def run_checker(self, checker_path, team, flag):
        service_name = os.path.basename(checker_path).replace('_checker.py', '')
        print(f"Running checker script for f{service_name}")
        result = subprocess.run(['python', checker_path, f'team{team}', flag], capture_output=True, text=True)
        return result.stdout.strip()

    # Update database and scoreboard with service status
    def update_service_status(self, service_name, status, team):
        print(f"  Team {team}: {status}")
        self.db.update_service_status(service_name, status, team)
        self.db.update_service_score(service_name, status, team, self.scoreboard.current_tick)

if __name__ == '__main__':
    controller = ServiceController()
    services = controller.db.get_services()
    controller.run_healthchecks(services)
