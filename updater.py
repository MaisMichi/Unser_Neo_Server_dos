import sys
import requests
from pathlib import Path

# ====== ANPASSEN ======
MODS_JSON_URL = "https://github.com/MaisMichi/Unser_Neo_Server_dos/releases/download/Mods/modlist.json"
MODRINTH_API = "https://api.modrinth.com/v2"
# =====================

def log(msg):
    print(f"[ModUpdater] {msg}")

def load_config():
    log("Lade mods.json von GitHub …")
    r = requests.get(MODS_JSON_URL, timeout=15)
    r.raise_for_status()
    return r.json()

def get_latest_version(project_id, mc_version, loader, allowed_types):
    r = requests.get(f"{MODRINTH_API}/project/{project_id}/version")
    r.raise_for_status()
    for v in r.json():
        if (
            mc_version in v["game_versions"]
            and loader in v["loaders"]
            and v["version_type"] in allowed_types
        ):
            return v
    return None

def main():
    if len(sys.argv) < 2:
        print("Usage: python update_mods.py <mods_directory>")
        sys.exit(1)

    mods_dir = Path(sys.argv[1])
    mods_dir.mkdir(parents=True, exist_ok=True)

    cfg = load_config()

    for slug in cfg["mods"]:
        try:
            log(f"Mod: {slug}")
            project = requests.get(f"{MODRINTH_API}/project/{slug}").json()

            version = get_latest_version(
                project["id"],
                cfg["minecraft_version"],
                cfg["loader"],
                cfg["allowed_release_types"]
            )

            if not version:
                log("  ⚠ Keine passende Version gefunden")
                continue

            file_info = version["files"][0]
            dest = mods_dir / file_info["filename"]

            if not dest.exists():
                log(f"  ⬇ Download {dest.name}")
                dest.write_bytes(requests.get(file_info["url"]).content)

            # Alte Versionen derselben Mod löschen
            base = dest.stem.split("-")[0].lower()
            for old in mods_dir.iterdir():
                if old.is_file() and old.name != dest.name:
                    if old.stem.lower().startswith(base):
                        old.unlink()

        except Exception as e:
            log(f"  ❌ Fehler: {e}")

    log("✅ Mod-Update abgeschlossen (Client-Mods wurden NICHT angerührt)")

if __name__ == "__main__":
    main()