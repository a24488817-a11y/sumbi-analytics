echo "[STEP 1] Checking Running Streamlit Process..."
ps aux | grep streamlit | grep -v grep

echo ""
echo "[STEP 2] Finding all main.py files in ubuntu..."
find /home/ubuntu -name "main.py" -type f
