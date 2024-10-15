import sys
import requests

def check_python_challenge(team):
    try:
        response = requests.get(f"http://{team}:5000/health", timeout=5)
        if response.status_code == 200 and "Python Challenge is running!" in response.text:
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
    
    result = check_python_challenge(team)
    print(result)
