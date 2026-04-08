# inspect_model_file.py
import os, sys, binascii, pickle, joblib

BASE = os.path.dirname(os.path.abspath(__file__))
MODELS = os.path.join(BASE, "Models")
FNAME = "random_forest.h5"
PATH = os.path.join(MODELS, FNAME)

def hexdump_head(path, n=256):
    with open(path, "rb") as f:
        data = f.read(n)
    # print bytes and ascii preview
    print("First %d bytes (hex):" % n)
    print(binascii.hexlify(data[:n]).decode("ascii"))
    print("ASCII preview (non-printable replaced with .):")
    print("".join((chr(b) if 32 <= b < 127 else ".") for b in data[:200]))

def try_hdf5(path):
    try:
        import h5py
        print("\nTrying h5py.File(...)")
        f = h5py.File(path, "r")
        print("h5py.File opened OK. keys:", list(f.keys()))
        f.close()
        return True
    except Exception as e:
        print("h5py open failed:", repr(e))
        return False

def try_joblib(path):
    try:
        print("\nTrying joblib.load(...)")
        obj = joblib.load(path)
        print("joblib.load succeeded. Type:", type(obj))
        try:
            print("repr(obj)[:1000]:", repr(obj)[:1000])
        except Exception:
            pass
        return True
    except Exception as e:
        print("joblib.load failed:", repr(e))
        return False

def try_pickle(path):
    try:
        print("\nTrying pickle.load(...)")
        with open(path, "rb") as f:
            obj = pickle.load(f)
        print("pickle.load succeeded. Type:", type(obj))
        try:
            print("repr(obj)[:1000]:", repr(obj)[:1000])
        except Exception:
            pass
        return True
    except Exception as e:
        print("pickle.load failed:", repr(e))
        return False

def try_numpy_npz(path):
    try:
        import numpy as np
        print("\nTrying numpy.load(..., allow_pickle=True)")
        data = np.load(path, allow_pickle=True)
        print("numpy.load succeeded. Type:", type(data))
        try:
            print("keys (if any):", getattr(data, "files", None))
        except Exception:
            pass
        return True
    except Exception as e:
        print("numpy.load failed:", repr(e))
        return False

if not os.path.exists(PATH):
    print("File not found:", PATH)
    sys.exit(1)

print("File:", PATH)
print("Size (bytes):", os.path.getsize(PATH))

hexdump_head(PATH, n=512)

# Try detection attempts (in safe order)
ok = try_hdf5(PATH)
if not ok:
    ok = try_joblib(PATH)
if not ok:
    ok = try_pickle(PATH)
if not ok:
    ok = try_numpy_npz(PATH)

if not ok:
    print("\nAll detection/loading attempts failed. The file may be corrupted or in a custom format.")
else:
    print("\nOne of the load attempts succeeded (see above).")
