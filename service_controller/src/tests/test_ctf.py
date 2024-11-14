from api_server import CTFDatabase, TeamManager, ServiceManager, FlagManager, GameController
import os
import time
from pprint import pprint

def test_ctf():
    # Clean up any existing test database
    if os.path.exists('test_ctf.db'):
        os.remove('test_ctf.db')

    print("\ninit")
    db = CTFDatabase('test_ctf.db')
    team_manager = TeamManager(db)
    service_manager = ServiceManager(db)
    flag_manager = FlagManager(db)
    game = GameController(db)

    print("\nadding teams\n")
    teams = []
    team_names = ["team1", "team2", "team3"]
    for name in team_names:
        team = team_manager.add_team(name)
        teams.append(team)
        print(f"Created team: {team}")

    print("\nget teams")
    all_teams = team_manager.get_teams()
    print("All teams:", all_teams)

    print("\nadd services")
    services = []
    service_configs = [
        {
            "name": "chall1",
            "port": 8001,
            "timeout": 30,
            "checker_host": "localhost",
            "checker_port": 9001
        },
        {
            "name": "chall2",
            "port": 8002,
            "timeout": 30,
            "checker_host": "localhost",
            "checker_port": 9002
        }
    ]

    for config in service_configs:
        service = service_manager.add_service(**config)
        services.append(service)
        print(f"Created service: {service}")

    print("\nmanage rounds")
    # Start first round
    round1_id = game.start_new_round()
    print(f"Started round {round1_id}")
    game.generate_flags(round1_id)

    # Get flags for testing
    with db.get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT flag, team_id, service_id FROM current_flags WHERE round_id = ?", (round1_id,))
        round1_flags = cursor.fetchall()
        print(f"Generated {len(round1_flags)} flags for round 1")

        # Store some flags for testing
        test_flags = {
            'team1': next(flag for flag, team_id, _ in round1_flags if team_id == teams[0]['id']),
            'team2': next(flag for flag, team_id, _ in round1_flags if team_id == teams[1]['id'])
        }
        print(test_flags)

    print("\nUpdate services")
    # Update some service statuses
    for team in teams:
        for service in services:
            status = "up" if team['id'] % 2 == 0 else "down"  # Alternate statuses
            result = service_manager.update_status(team['id'], service['id'], status)
            print(f"Updated status for team {team['name']}, service {service['name']}: {status}")

    print("\n=== Testing Flag Submission ===")
    # Team 2 submits Team 1's flag
    try:
        result = flag_manager.submit_flag(teams[1]['id'], test_flags['team1'])
        print("Flag submission result:", result)
    except ValueError as e:
        print("Expected flag submission failed:", str(e))

    print("\n=== Testing Multiple Rounds ===")
    # Start additional rounds to test flag expiry
    for i in range(2, 5):
        round_id = game.start_new_round()
        print(f"Started round {round_id}")
        game.generate_flags(round_id)
        print(f"Generated flags for round {round_id}")
        print(flag_manager.dump_flags())
        time.sleep(2)  # Increased delay between rounds to avoid locks

    print("\n=== Testing Old Flag Submission ===")
    # Try submitting an old flag (from round 1)
    try:
        result = flag_manager.submit_flag(teams[2]['id'], test_flags['team1'])
        print("Old flag submission result:", result)
    except ValueError as e:
        print("Old flag submission failed:", str(e))

    print("\n=== Final Team Scores ===")
    final_teams = team_manager.get_teams()
    pprint(final_teams)

    print("\n=== Flag Statistics ===")
    with db.get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) from current_flags")
        total_flags = cursor.fetchone()[0]
        print(f"Total flags in database: {total_flags}")

        cursor.execute("""
            SELECT r.round_number, COUNT(f.flag)
            FROM rounds r
            LEFT JOIN current_flags f ON r.id = f.round_id
            GROUP BY r.round_number
            ORDER BY r.round_number
        """)
        flags_per_round = cursor.fetchall()
        print("\nFlags per round:")
        for round_num, count in flags_per_round:
            print(f"Round {round_num}: {count} flags")

if __name__ == "__main__":
    test_ctf()
