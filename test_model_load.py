# test_model_load.py
import os
import pickle
from tensorflow.keras.models import load_model

BASE = os.path.dirname(os.path.abspath(__file__))
MODELS = os.path.join(BASE, "Models")

print("Models folder:", MODELS)
print("Files:", os.listdir(MODELS))

# Load Keras model
h5 = None
for f in os.listdir(MODELS):
    if f.lower().endswith(".h5"):
        h5 = os.path.join(MODELS, f)
        break

if not h5:
    raise SystemExit("No .h5 model found")

print("Loading model:", h5)
m = load_model(h5)
m.summary()

# Load encoder
enc_path = os.path.join(MODELS, "label_encoder.pkl")
if os.path.exists(enc_path):
    enc = pickle.load(open(enc_path, "rb"))
    print("Encoder type:", type(enc))
    if hasattr(enc, "classes_"):
        print("Encoder classes:", getattr(enc, "classes_"))
    else:
        print("Encoder object does not have classes_")
else:
    print("Encoder file not found:", enc_path)
