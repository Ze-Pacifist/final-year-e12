import requests
import time
from pprint import pprint
import threading
from api_server import CTFServer, CTFDatabase, TeamManager, ServiceManager, FlagManager, GameController
import os

def run_server(server):
    server.app.run(port=5000)

def test_api():
    # Initialize server
    server = CTFServer('test_ctf.db')

    # Start server in a separate thread
    server_thread = threading.Thread(target=run_server, args=(server,))
    server_thread.daemon = True
    server_thread.start()

    # Wait for server to start
    time.sleep(2)

    base_url = "http://localhost:5000"

    print("\n=== Testing Team Creation ===")
    teams = []
    for team_name in ["team1", "team2", "team3"]:
        response = requests.post(f"{base_url}/team", json={"name": team_name})
        assert response.status_code == 201, f"Failed to create team: {response.text}"
        team = response.json()
        teams.append(team)
        print(f"Created team: {team}")

    print("\n=== Testing Team Listing ===")
    response = requests.get(f"{base_url}/teams")
    assert response.status_code == 200, "Failed to get teams"
    print("Current teams:")
    pprint(response.json())

    print("\n=== Adding Services ===")
    services = []
    service_configs = [
        {
            "name": "WebApp",
            "port": 8001,
            "timeout": 30,
            "checker_host": "localhost",
            "checker_port": 9001
        },
        {
            "name": "Database",
            "port": 8002,
            "timeout": 30,
            "checker_host": "localhost",
            "checker_port": 9002
        }
    ]

    for config in service_configs:
        service = server.service_manager.add_service(**config)
        services.append(service)
        print(f"Created service: {service}")

    print("\n=== Creating and Starting Round ===")
    round_id = server.game_controller.start_new_round()
    print(f"Started round {round_id}")
    server.game_controller.generate_flags(round_id)
    print("Generated flags for round")

    print("\n=== Current Flags ===")
    flags = server.flag_manager.dump_flags()
    for flag in flags:
        print(f"Team: {flag['team_name']}, Service: {flag['service_name']}, Flag: {flag['flag']}")

    if flags:
        # Try submitting a flag from team1 to team2
        team1_flag = next(f['flag'] for f in flags if f['team_name'] == "team1")
        print(f"\n=== Testing Flag Submission ===")

        # Test submitting own flag (should fail)
        print("\nTrying to submit own flag (should fail):")
        response = requests.post(f"{base_url}/submit_flag", json={
            "team_id": teams[0]['id'],  # RedTeam
            "flag": team1_flag
        })
        print(f"Response ({response.status_code}):", response.json())

        # Test submitting valid flag
        print("\nSubmitting flag to another team:")
        response = requests.post(f"{base_url}/submit_flag", json={
            "team_id": teams[1]['id'],  # BlueTeam
            "flag": team1_flag
        })
        print(f"Response ({response.status_code}):", response.json())

        # Test submitting same flag again (should fail)
        print("\nTrying to submit same flag again (should fail):")
        response = requests.post(f"{base_url}/submit_flag", json={
            "team_id": teams[2]['id'],  # GreenTeam
            "flag": team1_flag
        })
        print(f"Response ({response.status_code}):", response.json())

    print("\n=== Testing Scoreboard (After Flag Submissions) ===")
    response = requests.get(f"{base_url}/scoreboard")
    assert response.status_code == 200, "Failed to get scoreboard"
    print("Final scoreboard:")
    pprint(response.json())

if __name__ == "__main__":
    # Clean up any existing test database
    if os.path.exists('test_ctf.db'):
        os.remove('test_ctf.db')

    try:
        test_api()
    except requests.exceptions.ConnectionError:
        print("Failed to connect to server. Make sure no other instance is running on port 5000.")
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
    except Exception as e:
        print(f"Test failed: {e}")
