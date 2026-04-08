# inspect_model.py
import os, sys, re
import pickle
import joblib

MODEL_PATH = "path/to/your/model_file.pkl"  # <-- CHANGE THIS LINE


print("Python:", sys.version)
print("Runtime scikit-learn:", end=" ")
try:
    import sklearn
    print(sklearn.__version__)
except Exception as e:
    print("sklearn not importable:", e)

print("\nTrying to read file bytes (searching for version-like tokens)...")
with open(MODEL_PATH, "rb") as f:
    data = f.read()

# print some human-readable ASCII chunks to look for embedded version strings
print("\n--- printable ASCII snippets around 'scikit' or 'sklearn' ---")
for m in re.finditer(rb"(scikit[-_ ]?learn|sklearn|scipy)[^\n\r]{0,40}", data, flags=re.I):
    start = max(0, m.start() - 60)
    end = min(len(data), m.end() + 60)
    chunk = data[start:end]
    try:
        print(chunk.decode("latin1").replace("\x00", " "))
    except Exception:
        print(repr(chunk[:200]))

print("\n--- Attempt to load with joblib (this may raise the same dtype error) ---")
try:
    obj = joblib.load(MODEL_PATH)
    print("Loaded object type:", type(obj))
    # If it's an sklearn estimator, try to print its module and __version__ hint
    try:
        print("Estimator repr:", repr(obj)[:400])
    except Exception:
        pass
except Exception as e:
    import traceback
    print("joblib.load failed with exception:")
    traceback.print_exc()
    print("\nAs fallback, try pickle.load (may fail similarly):")
    try:
        with open(MODEL_PATH, "rb") as f:
            p = pickle.load(f)
            print("pickle.load succeeded, object type:", type(p))
    except Exception as e2:
        print("pickle.load also failed:")
        traceback.print_exc()
