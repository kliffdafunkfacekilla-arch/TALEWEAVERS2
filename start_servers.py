import subprocess
import time
import sys
import os
import json

# Load the dynamic registry if it exists
REGISTRY_FILE = "saga_registry.json"
registry = {}
if os.path.exists(REGISTRY_FILE):
    try:
        with open(REGISTRY_FILE, "r") as f:
            registry = json.load(f)
            print(f"[BOOT] Loaded dynamic service registry from {REGISTRY_FILE}")
    except Exception as e:
        print(f"[BOOT] Error loading registry: {e}")

# Map of service keys in registry to their folder names
SERVICE_MAP = {
    "director": ("saga_director", 8000),
    "lore_vault": ("saga_lore_module", 8001),
    "world_architect": ("saga_architect", 8002),   # Python World Simulation Engine
    "char_engine": ("saga_character_engine", 8003),
    "encounter_engine": ("saga_encounter_engine", 8004),
    "item_foundry": ("saga_item_engine", 8005),
    "skill_engine": ("saga_skill_engine", 8006),
    "clash_engine": ("saga_clash_engine", 8007),
    "dmag_engine": ("saga_dmag_engine", 8008),
    "campaign_weaver": ("saga_campaign_weaver", 8010),
    "asset_foundry": ("saga_asset_foundry", 8010),
    "chronos": ("saga_chronos", 9000)
}

processes = []

def start_services():
    # 1. Build the ENV mapping for sibling discovery
    peer_env = os.environ.copy()
    for key, port in registry.items():
        # Map registry keys to the ENV names used in microservices
        env_key = f"{key.upper()}_URL"
        peer_env[env_key] = f"http://localhost:{port}"

    # 2. Spawn each service on its assigned port
    for key, (folder, default_port) in SERVICE_MAP.items():
        port = registry.get(key, default_port)
        
        if not os.path.exists(folder):
            print(f"[!] Warning: Folder {folder} not found. Skipping {key}.")
            continue
            
        print(f"[BOOT] Launching {key} on Port {port}...")
        
        # Inject the peer environment into the microservice
        p = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "main:app", "--port", str(port)],
            cwd=folder,
            env=peer_env
        )
        processes.append(p)

    # 3. Launch VTT Client (Vite)
    vtt_folder = "saga_vtt_client"
    if os.path.exists(vtt_folder):
        vtt_port = registry.get("vtt", 5173)
        print(f"[BOOT] Launching VTT Frontend on Port {vtt_port}...")
        try:
            # Note: Using shell=True for npm on Windows
            vtt_p = subprocess.Popen(
                ["npm.cmd", "run", "dev", "--", "--port", str(vtt_port)],
                cwd=vtt_folder,
                shell=True,
                env=peer_env
            )
            processes.append(vtt_p)
        except Exception as e:
            print(f"[!] Vite failed to start: {e}")

    print("\n[READY] All SAGA systems ignited. Press Ctrl+C to collapse the tower.")

if __name__ == "__main__":
    try:
        start_services()
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[SHUTDOWN] Collapsing process tree...")
        for p in processes:
            try:
                if sys.platform == "win32":
                    subprocess.run(["taskkill", "/F", "/T", "/PID", str(p.pid)], capture_output=True)
                else:
                    p.terminate()
            except:
                pass
        print("[DONE] System offline.")
