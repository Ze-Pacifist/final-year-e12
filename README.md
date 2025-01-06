# final-year-e12
# Seamlessly Deployable Lightweight Attack-Defence CTF Platform for Security Training

This project is a lightweight, containerized platform for hosting Attack-Defense CTF competitions. It leverages modern technologies to provide a gamified environment for hands-on cybersecurity training, simulating both offensive and defensive roles.

---

## Getting Started

### Prerequisites
- Docker and Docker Compose
- `curl` for HTTP requests (optional, but recommended for testing)
- custom challenges within teams folder

### How to Set-up and run:
1. Clone this repository:
   ```bash
   git clone <repository_url>
   cd <repository_name>```
2. Run the setup script and provide details like team name, challenge name etc.
    ```bash
    python3 setup_adf.py
    ```
3. Run the bash script which sets up the environment and runs docker
    ```bash
    bash run.sh
    ```

---

### Scoreboard
Scoreboard is accessible via HTTP GET request at 
```bash
curl http://<ip>:9090/scoreboard
```
Replace <ip> with the ip of the service controller or use docker hostname - `service_controller`


---

### Flag Submission
Flags can be submitted via HTTP POST request like follows:
```bash
curl -X POST http://<ip>:9090/submit_flags \
-H "Content-Type: application/json" \
-d '{
  "team_id": 1,
  "flags": ["flag{example1}", "flag{example2}"]
}'
```
Replace <ip> with the ip of the service controller or use docker hostname - `service_controller`
