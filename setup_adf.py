#!/usr/bin/env python
import subprocess
import time

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
      - ./vpn/config/peer1/peer1.conf:/etc/wireguard/admin.conf
    ports:
      - "8080:8080"
    restart: unless-stopped\n\n""" % team_count


def generate_team_services(team_count: int):

    for i in range(1,team_count+1):
        yield """  team1:
    build:
      context: ./teams
      dockerfile: Dockerfile
    container_name: team1
    networks:
      - team%s_network
    environment:
      TEAM_ID: %s
    restart: unless-stopped\n\n""" % (i, i)


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
    composef.write("services:\n")

    composef.write(generate_vpn_service(team_count, vpn_subnet, team_subnet))

    composef.write(generate_controller_service(team_count))

    for service in generate_team_services(team_count):
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

    team_count = input("Team count (1): ")
    team_count = int(team_count) if team_count else 1

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

    print("[+] Generated vpn configs")



    

    