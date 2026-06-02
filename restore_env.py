import re, os
backup_path = os.path.expanduser("~/main_backup_20260520.py")
env_path = os.path.expanduser("~/.env")

with open(backup_path, "r", encoding="utf-8") as f:
    content = f.read()

app_key = re.search(r'APP_KEY\s*=\s*"([^"]+)"', content).group(1)
app_secret = re.search(r'APP_SECRET\s*=\s*"([^"]+)"', content).group(1)

with open(env_path, "w", encoding="utf-8") as f:
    f.write(f'KIS_APP_KEY="{app_key}"\n')
    f.write(f'KIS_APP_SECRET="{app_secret}"\n')

print("--- ENV RESTORED SUCCESSFULLY ---")
