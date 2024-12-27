import sys
import os

parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)
os.chdir(parent_dir)

import setup_adf
import psutil
import time
import subprocess


def measure_cpu_ram():
    base_cpu, base_ram = [], []
    for _ in range(5):
        base_cpu.append(psutil.cpu_percent())
        base_ram.append(psutil.virtual_memory().percent)
        time.sleep(1)

    base_cpu_perc = round(sum(base_cpu) / len(base_cpu), 2)
    base_cpu = round(base_cpu_perc * psutil.cpu_count() / 100, 2)
    base_ram_perc = round(sum(base_ram) / len(base_ram), 2)
    base_ram = round((base_ram_perc * psutil.virtual_memory().total / 100) / (1024*1024), 2)

    print(f"[+] CPU => Perc: {base_cpu_perc}%, Util: {base_cpu} cpus")
    print(f"[+] RAM => Perc: {base_ram_perc}%, Util: {base_ram} MiB")

    return (base_cpu, base_ram)


if __name__ == "__main__":

    # Setup AD
    team_count = int(input("Enter number of teams: "))
    teams = [f"team{i}" for i in range(team_count)]
    services = [
        ("python_challenge", 5000, 10),
        ("node_challenge", 3000, 10)
    ]

    setup_adf.initialize_database(teams, services)
    vpn_subnet = "10.13.13.0/24"
    team_subnet = "172.30.0.0/16"

    setup_adf.generate_services(team_count, vpn_subnet, team_subnet)

    try:
        subprocess.check_call("rm -rf vpn/config", shell=True)
        subprocess.check_call("docker-compose up -d vpn --remove-orphans --force-recreate", shell=True)
        time.sleep(5)
        subprocess.check_call("docker-compose down vpn", shell=True)
    except:
        print("Unable to generate vpn configs")
        exit(1)
    print("[*] Setup AD complete!")

    # Measure baseline
    print("[*] Measuring baseline CPU and RAM usage")
    measure_cpu_ram()

    print("\n[*] Starting AD platform")
    try:
        subprocess.check_call("docker-compose up -d --remove-orphans --force-recreate", shell=True)
        time.sleep(10)
    except:
        print("Unable to start AD")
        exit(1)

    print(f"[*] Measuring CPU and RAM usage with {team_count} teams")
    measure_cpu_ram()

    print("\n[*] Stopping AD platform")
    try:
        subprocess.check_call("docker-compose down", shell=True)
    except:
        print("Unable to stop AD")
        exit(1)

    print("[*] Done!")
    