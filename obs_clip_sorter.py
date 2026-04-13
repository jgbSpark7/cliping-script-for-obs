"""
OBS Clip Sorter — ShadowPlay-style auto-sorting replay clips
=============================================================
Saves replay buffer clips into game-specific folders based on
detected running game processes. Works in fullscreen.

SETUP:
1. In OBS → Settings → Output → Replay Buffer → Enable Replay Buffer
2. Set your max replay length (e.g. 30–120 seconds)
3. Go to Tools → Scripts → + → select this file
4. Set your base clips folder in the script settings
5. Go to Settings → Hotkeys → find "Save & Sort Clip" and bind a key
"""

import obspython as obs
import subprocess
import os
import re
import shutil
import time
import glob

# --- Settings ---
base_clips_path = ""
custom_games_text = ""

# ===== GAME PROCESS DATABASE =====
# Maps process name (lowercase) -> friendly folder name
# Add more as needed!
KNOWN_GAMES = {
    # The Finals
    "discovery.exe": "The FInals",
    "discovery-d.exe": "The FInals",
    # Fortnite
    "fortniteclient-win64-shipping.exe": "Fortnite",
    "fortnitelauncher.exe": "Fortnite",
    # osu!
    "osu!.exe": "osu!",
    "osu.exe": "osu!",
    # Popular games (pre-loaded for convenience)
    "valorant.exe": "Valorant",
    "valorant-win64-shipping.exe": "Valorant",
    "r5apex.exe": "Apex Legends",
    "overwatch.exe": "Overwatch 2",
    "cs2.exe": "Counter-Strike 2",
    "csgo.exe": "CS GO",
    "rocketleague.exe": "Rocket League",
    "gta5.exe": "GTA V",
    "gtav.exe": "GTA V",
    "eldenring.exe": "Elden Ring",
    "minecraft.exe": "Minecraft",
    "javaw.exe": "Minecraft",
    "cod.exe": "Call of Duty",
    "modernwarfare.exe": "Call of Duty",
    "cod23-cod.exe": "Call of Duty",
    "leagueclient.exe": "League of Legends",
    "league of legends.exe": "League of Legends",
    "deadlock.exe": "Deadlock",
    "marvelrivals.exe": "Marvel Rivals",
    "pubdg.exe": "PUBG",
    "tslgame.exe": "PUBG",
    "rainbowsix.exe": "Rainbow Six Siege",
    "destiny2.exe": "Destiny 2",
    "warframe.exe": "Warframe",
    "diablo iv.exe": "Diablo IV",
    "baldursgate3.exe": "Baldurs Gate 3",
    "bg3.exe": "Baldurs Gate 3",
    "palworld.exe": "Palworld",
    "helldivers2.exe": "Helldivers 2",
    "lethal company.exe": "Lethal Company",
    "phasmophobia.exe": "Phasmophobia",
}

# Custom games added by user (populated from settings)
custom_games = {}

# Job state
_job_active = False
_job_game_name = ""
_job_before_time = 0
_job_attempts = 0
_job_source_dir = ""


def get_running_game():
    """Scan running processes for known games."""
    try:
        result = subprocess.run(
            ['powershell', '-NoProfile', '-Command',
             'Get-Process | Select-Object -ExpandProperty ProcessName'],
            capture_output=True, text=True, timeout=5
        )
        processes = set()
        for line in result.stdout.strip().splitlines():
            processes.add(line.strip().lower() + ".exe")

        # Check custom games first (user overrides take priority)
        all_games = {**KNOWN_GAMES, **custom_games}

        for proc, game_name in all_games.items():
            if proc.lower() in processes:
                return game_name

        return None
    except Exception as e:
        obs.script_log(obs.LOG_WARNING, f"Process scan failed: {e}")
        return None


def find_newest_replay(directory, before_time):
    patterns = ['*.mp4', '*.mkv', '*.flv', '*.mov', '*.ts']
    newest = None
    newest_time = before_time
    for pat in patterns:
        for f in glob.glob(os.path.join(directory, pat)):
            mtime = os.path.getmtime(f)
            if mtime > newest_time:
                newest = f
                newest_time = mtime
    return newest


def get_obs_output_dir():
    profile_config = obs.obs_frontend_get_profile_config()
    if profile_config:
        path = obs.config_get_string(profile_config, "SimpleOutput", "FilePath")
        if path:
            return path
    return None


def _tick():
    global _job_active, _job_attempts

    if not _job_active:
        return

    _job_attempts += 1

    clip_file = find_newest_replay(_job_source_dir, _job_before_time)
    if not clip_file and _job_source_dir != base_clips_path:
        clip_file = find_newest_replay(base_clips_path, _job_before_time)

    if not clip_file:
        if _job_attempts >= 5:
            obs.script_log(obs.LOG_WARNING, "No replay file found. Giving up.")
            _job_active = False
        return

    _job_active = False

    game_folder = os.path.join(base_clips_path, _job_game_name)
    os.makedirs(game_folder, exist_ok=True)

    ts = time.strftime("%Y-%m-%d_%H-%M-%S")
    ext = os.path.splitext(clip_file)[1]
    new_name = f"{_job_game_name}_{ts}{ext}"
    dest = os.path.join(game_folder, new_name)

    counter = 1
    while os.path.exists(dest):
        new_name = f"{_job_game_name}_{ts}_{counter}{ext}"
        dest = os.path.join(game_folder, new_name)
        counter += 1

    try:
        shutil.move(clip_file, dest)
        obs.script_log(obs.LOG_INFO, f"Clip saved: {dest}")
    except Exception as e:
        obs.script_log(obs.LOG_ERROR, f"Failed to move clip: {e}")


def save_and_sort_clip(pressed):
    global _job_active, _job_game_name, _job_before_time, _job_attempts, _job_source_dir

    if not pressed:
        return

    if not base_clips_path:
        obs.script_log(obs.LOG_WARNING, "Base clips path not set!")
        return

    if _job_active:
        obs.script_log(obs.LOG_INFO, "Already waiting for a clip...")
        return

    # Detect game by running process
    detected = get_running_game()
    if detected:
        _job_game_name = detected
        obs.script_log(obs.LOG_INFO, f"Detected game: {_job_game_name}")
    else:
        _job_game_name = "Unknown"
        obs.script_log(obs.LOG_INFO, "No known game detected, using 'Unknown'")

    _job_source_dir = get_obs_output_dir() or base_clips_path
    _job_before_time = time.time() - 1
    _job_attempts = 0
    _job_active = True

    obs.obs_frontend_replay_buffer_save()
    obs.script_log(obs.LOG_INFO, "Replay buffer save triggered...")


# --- OBS Script Interface ---

hotkey_id = obs.OBS_INVALID_HOTKEY_ID


def script_description():
    return (
        "<h2>Clip Sorter \u2014 ShadowPlay-style</h2>"
        "<p>Saves replay buffer clips into <b>game-specific folders</b> "
        "by detecting running game processes. <b>Works in fullscreen.</b></p>"
        "<p>Bind the <b>Save &amp; Sort Clip</b> hotkey in OBS settings.</p>"
        "<p>Pre-loaded games: The Finals, Fortnite, osu!, Valorant, "
        "Apex, CS2, Rocket League, and more. Add your own below.</p>"
    )


def script_properties():
    props = obs.obs_properties_create()
    obs.obs_properties_add_path(
        props, "base_clips_path", "Base Clips Folder",
        obs.OBS_PATH_DIRECTORY, "", ""
    )
    obs.obs_properties_add_text(
        props, "custom_games_text",
        "Custom Games (one per line: processname.exe=FolderName)",
        obs.OBS_TEXT_MULTILINE
    )
    return props


def script_defaults(settings):
    obs.obs_data_set_default_string(
        settings, "base_clips_path",
        os.path.join(os.path.expanduser("~"), "Videos", "Clips")
    )
    obs.obs_data_set_default_string(settings, "custom_games_text", "")


def script_update(settings):
    global base_clips_path, custom_games

    base_clips_path = obs.obs_data_get_string(settings, "base_clips_path")
    cg_text = obs.obs_data_get_string(settings, "custom_games_text")

    custom_games = {}
    for line in cg_text.strip().splitlines():
        if '=' in line:
            key, val = line.split('=', 1)
            custom_games[key.strip().lower()] = val.strip()

    obs.script_log(obs.LOG_INFO, f"Clips folder: {base_clips_path}")
    if custom_games:
        obs.script_log(obs.LOG_INFO, f"Custom games: {custom_games}")


def script_load(settings):
    global hotkey_id
    hotkey_id = obs.obs_hotkey_register_frontend(
        "save_sort_clip", "Save & Sort Clip", save_and_sort_clip
    )
    hotkey_save_array = obs.obs_data_get_array(settings, "save_sort_clip_hotkey")
    obs.obs_hotkey_load(hotkey_id, hotkey_save_array)
    obs.obs_data_array_release(hotkey_save_array)
    obs.timer_add(_tick, 2000)


def script_unload():
    obs.timer_remove(_tick)


def script_save(settings):
    hotkey_save_array = obs.obs_hotkey_save(hotkey_id)
    obs.obs_data_set_array(settings, "save_sort_clip_hotkey", hotkey_save_array)
    obs.obs_data_array_release(hotkey_save_array)
