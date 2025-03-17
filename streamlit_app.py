import os
import subprocess
import requests
import zipfile
import gzip
import shutil
import json
import psutil  # For monitoring CPU usage
import threading  # For running CPU monitoring in a separate thread

# Function to monitor CPU usage
def monitor_cpu_usage():
    while True:
        cpu_usage = psutil.cpu_percent(interval=1)
        print(f"CPU Usage: {cpu_usage}%")

# Step 1: Download and extract libzip5 and libssl1.1
print("Downloading libzip5 and libssl1.1...")
libzip_url = "http://archive.ubuntu.com/ubuntu/pool/universe/libz/libzip/libzip5_1.5.1-0ubuntu1_amd64.deb"
libssl_url = "http://archive.ubuntu.com/ubuntu/pool/main/o/openssl/libssl1.1_1.1.1f-1ubuntu2_amd64.deb"
libzip_deb = "libzip5_1.5.1-0ubuntu1_amd64.deb"
libssl_deb = "libssl1.1_1.1.1f-1ubuntu2_amd64.deb"
lib_dir = "libs"

os.makedirs(lib_dir, exist_ok=True)

for url, deb in [(libzip_url, libzip_deb), (libssl_url, libssl_deb)]:
    response = requests.get(url)
    with open(deb, "wb") as f:
        f.write(response.content)
    subprocess.run(["dpkg-deb", "-x", deb, lib_dir])
    os.remove(deb)

libzip_lib_path = os.path.join(lib_dir, "usr", "lib", "x86_64-linux-gnu")
libssl_lib_path = os.path.join(lib_dir, "lib", "x86_64-linux-gnu")
os.environ["LD_LIBRARY_PATH"] = f"{libzip_lib_path}:{libssl_lib_path}"

# Step 2: Download and unzip KataGo (Eigen version)
print("Downloading KataGo (Eigen version)...")
katago_url = "https://github.com/lightvector/KataGo/releases/download/v1.15.3/katago-v1.15.3-eigen-linux-x64.zip"
katago_zip = "katago-v1.15.3-eigen-linux-x64.zip"
katago_dir = "katago"

response = requests.get(katago_url)
with open(katago_zip, "wb") as f:
    f.write(response.content)

with zipfile.ZipFile(katago_zip, "r") as zip_ref:
    zip_ref.extractall(katago_dir)
os.remove(katago_zip)
os.chmod(os.path.join(katago_dir, "katago"), 0o755)

# Step 3: Download the KataGo model
print("Downloading KataGo model...")
model_url = "https://media.katagotraining.org/uploaded/networks/models/kata1/kata1-b18c384nbt-s9937771520-d4300882049.bin.gz"
model_gz = "kata1-b18c384nbt-s9937771520-d4300882049.bin.gz"
model_bin = "kata1-b18c384nbt-s9937771520-d4300882049.bin"

response = requests.get(model_url)
with open(model_gz, "wb") as f:
    f.write(response.content)

with gzip.open(model_gz, "rb") as gz_file:
    with open(os.path.join(katago_dir, model_bin), "wb") as bin_file:
        shutil.copyfileobj(gz_file, bin_file)
os.remove(model_gz)

# Step 4: Download gtp2ogs
print("Downloading gtp2ogs...")
gtp2ogs_url = "https://github.com/online-go/gtp2ogs/releases/download/9.0/gtp2ogs-9.0.0-linux"
gtp2ogs_binary = "gtp2ogs"

response = requests.get(gtp2ogs_url)
with open(gtp2ogs_binary, "wb") as f:
    f.write(response.content)
os.chmod(gtp2ogs_binary, 0o755)

# Step 5: Modify default_gtp.cfg
print("Updating default_gtp.cfg...")
default_gtp_cfg_path = os.path.join(katago_dir, "default_gtp.cfg")

# Read the file
with open(default_gtp_cfg_path, "r") as f:
    lines = f.readlines()

# Apply the original changes
lines[54] = "logSearchInfo = true\n"
lines[63] = "ogsChatToStderr = True\n"
lines[300] = "# maxVisits = 500\n"
lines[302] = "maxTime = 1.0\n"
lines[305] = "ponderingEnabled = true\n"

# Apply the new rules configuration (lines 113 to 149)
lines[113:150] = [
    "# rules = tromp-taylor\n",
    "\n",
    "# By default, the \"rules\" parameter is used, but if you comment it out and\n",
    "# uncomment one option in each of the sections below, you can specify an\n",
    "# arbitrary combination of individual rules.\n",
    "\n",
    "# koRule = SIMPLE       # Simple ko rules (triple ko = no result)\n",
    "koRule = POSITIONAL   # Positional superko\n",
    "# koRule = SITUATIONAL  # Situational superko\n",
    "\n",
    "scoringRule = AREA       # Area scoring\n",
    "# scoringRule = TERRITORY  # Territory scoring (special computer-friendly territory rules)\n",
    "\n",
    "taxRule = NONE  # All surrounded empty points are scored\n",
    "# taxRule = SEKI  # Eyes in seki do NOT count as points\n",
    "# taxRule = ALL   # All groups are taxed up to 2 points for the two eyes needed to live\n",
    "\n",
    "# Is multiple-stone suicide legal? (Single-stone suicide is always illegal).\n",
    "# multiStoneSuicideLegal = false\n",
    "multiStoneSuicideLegal = true  # Allow multi-stone suicide\n",
    "\n",
    "# \"Button go\" - the first pass when area scoring awards 0.5 points and does\n",
    "# not count for ending the game.\n",
    "# Allows area scoring rulesets that have far simpler rules to achieve the same\n",
    "# final scoring precision and reward for precise play as territory scoring.\n",
    "# hasButton = false\n",
    "# hasButton = true\n",
    "\n",
    "# Is this a human ruleset where it's okay to pass before having physically\n",
    "# captured and removed all dead stones?\n",
    "# friendlyPassOk = false\n",
    "friendlyPassOk = true  # Allow friendly pass\n",
    "\n",
    "# How handicap stones in handicap games are compensated\n",
    "# whiteHandicapBonus = 0    # White gets no compensation for black's handicap stones (Tromp-taylor, NZ, JP)\n",
    "# whiteHandicapBonus = N-1  # White gets N-1 points for black's N handicap stones (AGA)\n",
    "# whiteHandicapBonus = N    # White gets N points for black's N handicap stones (Chinese)\n",
]

# Write the updated content back to the file
with open(default_gtp_cfg_path, "w") as f:
    f.writelines(lines)

print("default_gtp.cfg has been updated successfully!")

# Step 6: Generate kata_speed.json5
print("Generating kata_speed.json5...")
kata_speed_config = {
    "blacklist": ["Tilano", "ujykfyijhgf", "Benneviss", "world2049","extoom"],
    "whitelist": ["xqqzldh", "Golaxy 9D", "俱乐部AI", "Doudoubot", "Katagui40b", "Kata_speed"],
    "allow_ranked": True,
    "decline_new_challenges": False,
    "max_games_per_player": 1,
    "hidden": False,
    "allowed_board_sizes": [9, 13, 19],
    "engine": "KataGo b18 network with usually only 7 visits, takes about 10 seconds or more per move. Support us at https://changcheng967.github.io/Kata_web/ to make the play speed faster and play with more people!",
    "allow_unranked": True,
    "farewellscore": True,
    "bot": {
        "send_pv_data": True,
        "send_chats": True
    },
    # Disable correspondence games
    "allowed_correspondence_settings": None
}

with open("kata_speed.json5", "w", encoding="utf-8") as f:
    json.dump(kata_speed_config, f, indent=4, ensure_ascii=False)

# Step 7: Run gtp2ogs with KataGo
print("Running gtp2ogs with KataGo...")
api_key = "140871f7fa53e30b42fa272755173763ff171d73"
command = [
    "./gtp2ogs",
    "--apikey", api_key,
    "--config", "kata_speed.json5",
    "--",
    os.path.join(katago_dir, "katago"),
    "gtp",
    "-config", os.path.join(katago_dir, "default_gtp.cfg"),
    "-model", os.path.join(katago_dir, model_bin)
]

# Start CPU monitoring in a separate thread
cpu_monitor_thread = threading.Thread(target=monitor_cpu_usage, daemon=True)
cpu_monitor_thread.start()

# Run gtp2ogs with KataGo
subprocess.run(command)
