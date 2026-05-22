import re, os
file_path = os.path.expanduser("~/main.py")

with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()
    
def decode_match(m):
    return m.group(0).encode('ascii').decode('unicode_escape')
    
cleaned_content = re.sub(r'(\\u[0-9a-fA-F]{4})+', decode_match, content)

with open(file_path, "w", encoding="utf-8") as f:
    f.write(cleaned_content)
    
print("--- ALIEN CODE TRANSLATED TO KOREAN SUCCESSFULLY ---")
