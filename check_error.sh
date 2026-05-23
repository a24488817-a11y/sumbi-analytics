echo "[STEP 1] Checking if V3 Code exists in main.py..."
grep -n "SUMBI V3 Score Calculation" /home/ubuntu/main.py || echo "-> NOT FOUND"

echo ""
echo "[STEP 2] Inspecting lines around QUANT FLOW MATRIX..."
grep -n -C 5 "QUANT FLOW MATRIX" /home/ubuntu/main.py

echo ""
echo "[STEP 3] Checking for Streamlit or Python Syntax Errors..."
python3 -m py_compile /home/ubuntu/main.py && echo "-> Syntax OK" || echo "-> Syntax Error Detected"
