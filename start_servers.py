import subprocess
import time
import sys

# Define all the backend microservices
services = [
    ("Lore Vault", 8001, "saga_lore_module"),
    ("World Architect", 8002, "saga_architect"),
    ("Character Engine", 8003, "saga_character_engine"),
    ("Chronos Engine", 8004, "saga_chronos"),
    ("Item Foundry", 8005, "saga_item_engine"),
    ("Skill Engine", 8006, "saga_skill_engine"),
    ("Clash Engine", 8007, "saga_clash_engine"),
    ("Encounter Engine", 8009, "saga_encounter_engine"),
    ("Core Game Master", 8000, "saga_gamemaster"),
    ("Campaign Weaver", 8010, "saga_campaign_weaver"),
]

processes = []

try:
    print("========================================")
    print("🚀 STARTING TALEWEAVERS ENGINE 🚀")
    print("========================================")
    
    # Start Python Backends
    for name, port, folder in services:
        print(f"[*] Starting {name} (Port {port})")
        
        # We redirect stdout and stderr to DEVNULL so the console isn't 
        # completely spammed with 10 different APIs printing "INFO: Application startup complete"
        # but we keep the main window clean.
        p = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "main:app", "--port", str(port), "--reload"],
            cwd=folder
        )
        processes.append(p)
    
    print("\n[*] Starting VTT Client (Frontend)")
    # We let the React frontend print to the console so the user can see the localhost URL
    p_vtt = subprocess.Popen(
        ["npm", "run", "dev"],
        cwd="saga_vtt_client",
        shell=True
    )
    processes.append(p_vtt)
    
    print("\n========================================")
    print("🟢 ALL SERVICES RUNNING 🟢")
    print("-> Press Ctrl+C in this window to cleanly shut down everything.")
    print("========================================\n")
    
    # Keep the script alive
    while True:
        time.sleep(1)

except KeyboardInterrupt:
    print("\n[!] Shutting down all TALEWEAVERS services...")
    for p in processes:
        p.terminate()
    print("Goodbye!")
    sys.exit(0)
