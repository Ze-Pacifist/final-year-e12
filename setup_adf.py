#!/usr/bin/env python
import subprocess
import time
import sqlite3
import random
import string
import os
import psutil

passwords = []
CPU_RESERVE = 1
MEM_RESERVE = 2048

def initialize_database(teams: list, services: list):
    try:
        subprocess.check_call(["rm", "-rf", "database"])
        subprocess.check_call(["mkdir", "database"])
    except:
        print("Unable to reset database files")
        exit(1)

    conn = sqlite3.connect("database/ctf.db")
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
                  service_name TEXT NOT NULL,
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

    for team in teams:
        c.execute('''INSERT INTO teams (name) VALUES ('%s')''' % team)

    for service in services:
        c.execute('''INSERT INTO services (name, port, timeout) VALUES ('%s', %s, %s)''' % (service[0], service[1], service[2]))

    for i in range(1, len(teams)+1):
        for service in services:
            c.execute('''INSERT INTO current_status (team_id, service_name, status, last_updated) VALUES (%s, '%s', 'UP', datetime('now'))''' % (i, service[0]))

    conn.commit()
    conn.close()


def generate_vpn_service(peer_count: int, vpn_subnet: str, team_subnet: str):
    return """  vpn:
    image: lscr.io/linuxserver/wireguard:latest
    container_name: vpn
    cap_add:
      - NET_ADMIN
      - SYS_MODULE
    environment:
      - PUID=1000
      - PGID=1000
      - TZ=Etc/IST
      - SERVERURL=vpn
      - SERVERPORT=51820
      - PEERS=%s
      - PEERDNS=auto
      - INTERNAL_SUBNET=%s
      - ALLOWEDIPS=%s
      - LOG_CONFS=true
    volumes:
      - ./vpn/config:/config
      - /lib/modules:/lib/modules
    ports:
      - 51820:51820/udp
    sysctls:
      - net.ipv4.conf.all.src_valid_mark=1
    networks:
%s
      - admin_network
    restart: unless-stopped\n\n""" % (
      peer_count+1, 
      vpn_subnet, 
      vpn_subnet + "," + team_subnet, 
      "\n".join(["      - team%s_network" % i for i in range(1, peer_count+1)])
    )


def generate_controller_service(team_count: int):
    return """  service_controller:
    build:
      context: .
      dockerfile: service_controller/Dockerfile
    container_name: service_controller
    depends_on:
      - vpn
    cap_add:
      - NET_ADMIN
      - SYS_MODULE
    sysctls:
      - net.ipv4.conf.all.src_valid_mark=1
    environment:
      TICK_INTERVAL: 180
      NUM_TEAMS: %s
    networks:
      - admin_network
    volumes:
      - ./database:/app/database
      - ./vpn/config/peer1/peer1.conf:/etc/wireguard/admin.conf
    ports:
      - "8080:9090"
    restart: unless-stopped\n\n""" % team_count


def generate_team_services(team_count: int, cpu: float, memory: int):
    for i in range(1,team_count+1):
        passwords.append(''.join(random.choices(string.ascii_letters + string.digits, k=12)))
        yield """  team%s:
    build:
      context: ./teams
      dockerfile: Dockerfile
    container_name: team%s
    networks:
      - team%s_network
    environment:
      TEAM_ID: %s
      ROOT_PASSWORD: %s
    restart: unless-stopped
    deploy:
      resources:
          limits:
            cpus: '%s'
            memory: %sM\n\n""" % (i, i, i, i, passwords[-1], cpu, memory)


def generate_networks(team_count: int, team_subnet: str):
    
    team_subnet = team_subnet[:-3] + "/24"
    team_subnet = team_subnet.split(".")

    teams = ["admin"] + ["team%s" % _ for _ in range(1, team_count+1)]

    for i in teams:

        team_subnet[2] = str(int(team_subnet[2])+1)
        team_specific_subnet = ".".join([str(_) for _ in team_subnet])

        yield """  %s_network:
    driver: bridge
    ipam:
      config:
        - subnet: %s\n""" % (i, team_specific_subnet)


def generate_services(team_count: int, vpn_subnet: str, team_subnet: str):

    composef = open("docker-compose.yml", "w")
    composef.write("version: '3'\n\n")
    composef.write("services:\n")

    num_cpus = os.cpu_count() - CPU_RESERVE
    total_memory = (psutil.virtual_memory().total // 10**6) - MEM_RESERVE

    composef.write(generate_vpn_service(team_count, vpn_subnet, team_subnet))

    composef.write(generate_controller_service(team_count))

    for service in generate_team_services(team_count, num_cpus/team_count, total_memory//team_count):
        composef.write(service)

    composef.write("networks:\n")
    for network in generate_networks(team_count, team_subnet):
        composef.write(network)

    composef.close()


def generate_shell_script(team_count: int, team_subnet: str):

    shellf = open("run.sh", "w")
    shellf.write("#!/usr/bin/env bash")

    team_subnet = team_subnet[:-3] + "/24"
    team_subnet = team_subnet.split(".")
    team_subnet[2] = "$i"
    team_subnet = ".".join(team_subnet)

    script = """
create_rules() {
    # Flush existing rules in DOCKER-USER chain
    iptables -F DOCKER-USER

    # Allow traffic within each subnet and isolate between subnets
    for i in $(seq 1 %s); do
        iptables -A DOCKER-USER -s %s -d %s -j ACCEPT
    done

    for i in $(seq 1 %s); do
        for j in $(seq 1 %s); do
            if [ $i -ne $j ]; then
                iptables -A DOCKER-USER -s %s -d %s -j DROP
            fi
        done
    done
}

delete_rules() {
    # Flush all rules in the DOCKER-USER chain
    iptables -F DOCKER-USER
}

# Check if running as root
if [ "$EUID" -ne 0 ]; then
  echo "Please run as root"
  exit 1
fi

# Check for -u (update/create) or -d (delete) argument
if [ "$1" == "-u" ]; then
    create_rules
    docker-compose up -d --remove-orphans --force-recreate
elif [ "$1" == "-d" ]; then
    delete_rules
    docker-compose down
else
    echo "Usage: $0 -u (to up) or -d (to down)"
    exit 1
fi
""" % (
    team_count+1, 
    team_subnet, team_subnet,
    team_count+1, team_count+1,
    team_subnet, team_subnet.replace("$i", "$j")
    )

    shellf.write(script)
    shellf.close()

if __name__ == "__main__":

    service_count = input("Service count (1): ")
    service_count = int(service_count) if service_count else 1
    services = [ (input("\nService #%s\nEnter name: " % i), 
                  int(input("Enter port: ")),
                  int(input("Enter timeout: "))) for i in range(1,service_count+1) ]

    team_count = input("\nTeam count (1): ")
    team_count = int(team_count) if team_count else 1
    teams = [ input("Enter name for team #%s: " % i) for  i in range(1,team_count+1)]

    initialize_database(teams, services)
    print("[+] Initialized the database")

    vpn_subnet = input("VPN subnet (10.13.13.0/24): ")
    vpn_subnet = vpn_subnet if vpn_subnet else "10.13.13.0/24"

    team_subnet = input("Team subnet (172.30.0.0/16): ")
    team_subnet = team_subnet if team_subnet else "172.30.0.0/16"

    generate_services(team_count, vpn_subnet, team_subnet)
    print("[+] Generated docker-compose.yml")

    generate_shell_script(team_count, team_subnet)
    print("[+] Generated shell script")

    try:
        subprocess.check_call("rm -rf vpn/config", shell=True)
        subprocess.check_call("docker-compose up -d vpn --remove-orphans --force-recreate", shell=True)
        time.sleep(5)
        subprocess.check_call("docker-compose down vpn", shell=True)
    except:
        print("Unable to generate vpn configs")
        exit(1)

    print("[+] Generated vpn configs")

    try:
        for i in range(2, len(passwords)+2):
            subprocess.check_call("echo '%s' > vpn/config/peer%s/password.txt" % (passwords[i-2], i), shell=True)
    except:
        print("Unable to generate password files")
        exit(1)

    print("[+] Generated password text files")



    

    