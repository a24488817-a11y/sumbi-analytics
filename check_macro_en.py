from macro_engine import MacroShockEngine
import traceback

try:
    print("Start Scanning...")
    engine = MacroShockEngine("66f8e6a39938571b83bcdf4bae9b9418")
    df = engine.aggregate_macro_metrics()
    print("--- COLUMN NAMES ---")
    if df is not None:
        print(df.columns.tolist())
    else:
        print("Data is None")
except Exception as e:
    print("--- ERROR ---")
    traceback.print_exc()
