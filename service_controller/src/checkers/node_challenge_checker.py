import sys
import requests

def check_node_challenge(team):
    try:
        response = requests.get(f"http://{team}:3000/health", timeout=5)
        if response.status_code == 200 and "Node.js Challenge is running!" in response.text:
            return "UP"
        else:
            return "DOWN"
    except requests.RequestException:
        return "DOWN"

def plant_flag(team,flag):
    try:
        response=requests.get(f"http://{team}:3000/flag?flag={flag}", timeout=5)
    except Exception as e:
        pass
        # print("Error planting flag")

if __name__ == "__main__":
    if len(sys.argv) > 2:
        team = sys.argv[1]
        flag = sys.argv[2]
    else:
        team = input("Enter team (e.g., team1): ")
    
    result = check_node_challenge(team)
    plant_flag(team,flag)
    print(result)
