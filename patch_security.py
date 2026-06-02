import os

file_path = os.path.expanduser("~/main.py")
with open(file_path, "r", encoding="utf-8") as f:
    lines = f.readlines()

# 1. Add dotenv import if missing
if "load_dotenv" not in "".join(lines):
    lines.insert(0, "import os\nfrom dotenv import load_dotenv\nload_dotenv()\n")

# 2. Replace hardcoded keys
for i, line in enumerate(lines):
    if line.strip().startswith("APP_KEY ="):
        lines[i] = 'APP_KEY = os.environ.get("KIS_APP_KEY")\n'
    elif line.strip().startswith("APP_SECRET ="):
        lines[i] = 'APP_SECRET = os.environ.get("KIS_APP_SECRET")\n'

with open(file_path, "w", encoding="utf-8") as f:
    f.writelines(lines)

print("--- Security Patch Applied Successfully ---")
