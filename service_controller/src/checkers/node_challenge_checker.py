import sys
import requests

def check_node_challenge(team, port):
    try:
        response = requests.get(f"http://{team}:3000/health", timeout=5)
        if response.status_code == 200 and "Node.js Challenge is running!" in response.text:
            return "UP"
        else:
            return "DOWN"
    except requests.RequestException:
        return "DOWN"

if __name__ == "__main__":
    if len(sys.argv) > 1:
        team = sys.argv[1]
    else:
        team = input("Enter team (e.g., team1): ")
    
    result = check_node_challenge(team)
    print(result)
