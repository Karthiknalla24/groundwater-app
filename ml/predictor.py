# import os
# import pickle
# import pandas as pd

# # ===============================
# # Model & Transformer Paths
# # ===============================
# BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# MODELS_DIR = os.path.join(BASE_DIR, "Models")

# DRINKING_MODEL = os.path.join(MODELS_DIR, "random_forest.h5")
# IRRIGATION_MODEL = DRINKING_MODEL   # using same model unless you have separate

# BOXCOX_PATH = os.path.join(MODELS_DIR, "boxcox_transformer.pkl")
# YEO_PATH = os.path.join(MODELS_DIR, "yeojohnson_transformer.pkl")
# ENCODER_PATH = os.path.join(MODELS_DIR, "label_encoder.pkl")
# FEATURE_PATH = os.path.join(MODELS_DIR, "feature_columns.pkl")


# # ===============================
# # Load once (no globals needed)
# # ===============================
# def load_all():
#     """Loads models and transformers only once."""
#     with open(DRINKING_MODEL, "rb") as f:
#         drinking_model = pickle.load(f)

#     with open(IRRIGATION_MODEL, "rb") as f:
#         irrigation_model = pickle.load(f)

#     with open(BOXCOX_PATH, "rb") as f:
#         boxcox = pickle.load(f)

#     with open(YEO_PATH, "rb") as f:
#         yeo = pickle.load(f)

#     with open(ENCODER_PATH, "rb") as f:
#         encoder = pickle.load(f)

#     with open(FEATURE_PATH, "rb") as f:
#         feature_cols = pickle.load(f)

#     return drinking_model, irrigation_model, boxcox, yeo, encoder, feature_cols


# # ===============================
# # Column groups
# # ===============================
# BOXCOX_COLS = [
#     "pH","Electrical_Conductivity","Total_Dissolved_Solids",
#     "Chloride","Fluoride","Sulfate","Sodium",
#     "Calcium","Magnesium","Total_Hardness","Sodium_Adsorption_Ratio"
# ]

# YEO_COLS = ["Carbonate","Nitrate","Residual_Sodium_Carbonate"]

# NUM_COLS = [
#     "pH","Electrical_Conductivity","Total_Dissolved_Solids",
#     "Carbonate","Bicarbonate","Chloride","Fluoride","Nitrate",
#     "Sulfate","Sodium","Calcium","Magnesium",
#     "Total_Hardness","Sodium_Adsorption_Ratio","Residual_Sodium_Carbonate"
# ]


# # ===============================
# # Prepare dataframe
# # ===============================
# def prepare(input_dict, boxcox, yeo, feature_cols):
#     df = pd.DataFrame([input_dict])

#     # Missing columns → fill
#     for col in NUM_COLS:
#         if col not in df.columns:
#             df[col] = 0

#     df[BOXCOX_COLS] = boxcox.transform(df[BOXCOX_COLS])
#     df[YEO_COLS] = yeo.transform(df[YEO_COLS])

#     df = df.reindex(columns=feature_cols, fill_value=0)
#     return df


# # ===============================
# # MAIN FUNCTION (used in app.py)
# # ===============================
# def predict_quality(mode, input_dict):
#     """
#     mode = 'drinking' or 'irrigation'
#     input_dict = dictionary of numeric values
#     """

#     drinking_model, irrigation_model, boxcox, yeo, encoder, feature_cols = load_all()

#     df = prepare(input_dict, boxcox, yeo, feature_cols)

#     model = irrigation_model if mode == "irrigation" else drinking_model

#     encoded = model.predict(df)[0]
#     decoded = encoder.inverse_transform([encoded])[0]

#     print("=== Prediction ===")
#     print("Mode:", mode)
#     print("Input:", input_dict)
#     print("Output:", decoded)
    
#     return decoded



# ml/predictor.py
import os
import logging
import pickle
import joblib
from typing import Dict, Any

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELS_DIR = os.path.join(BASE_DIR, "Models")

# Default artifacts (your Models folder already contains these pickles)
DRINKING_MODEL = os.path.join(MODELS_DIR, "random_forest.pkl")  # recommended rename
# Fallback: keep allowing .h5 that is actually a pickle
DRINKING_MODEL_ALT = os.path.join(MODELS_DIR, "random_forest.h5")

BOXCOX_PATH = os.path.join(MODELS_DIR, "boxcox_transformer.pkl")
YEO_PATH = os.path.join(MODELS_DIR, "yeojohnson_transformer.pkl")
ENCODER_PATH = os.path.join(MODELS_DIR, "label_encoder.pkl")
FEATURE_PATH = os.path.join(MODELS_DIR, "feature_columns.pkl")


BOXCOX_COLS = [
    "pH","Electrical_Conductivity","Total_Dissolved_Solids",
    "Chloride","Fluoride","Sulfate","Sodium",
    "Calcium","Magnesium","Total_Hardness","Sodium_Adsorption_Ratio"
]

YEO_COLS = ["Carbonate","Nitrate","Residual_Sodium_Carbonate"]

NUM_COLS = [
    "pH","Electrical_Conductivity","Total_Dissolved_Solids",
    "Carbonate","Bicarbonate","Chloride","Fluoride","Nitrate",
    "Sulfate","Sodium","Calcium","Magnesium",
    "Total_Hardness","Sodium_Adsorption_Ratio","Residual_Sodium_Carbonate"
]


def _load_pickle(path):
    with open(path, "rb") as f:
        return pickle.load(f)


def _load_sklearn_pickle(path):
    """
    Try joblib.load then fallback to pickle.load.
    """
    try:
        return joblib.load(path)
    except Exception as e:
        logger.debug("joblib.load failed (%s); trying pickle.load", e)
        with open(path, "rb") as f:
            return pickle.load(f)


def _load_transformers_and_encoder():
    missing = []
    for p in (BOXCOX_PATH, YEO_PATH, ENCODER_PATH, FEATURE_PATH):
        if not os.path.exists(p):
            missing.append(p)
    if missing:
        raise FileNotFoundError(f"Missing transformer/encoder/feature files: {missing}")

    boxcox = _load_pickle(BOXCOX_PATH)
    yeo = _load_pickle(YEO_PATH)
    encoder = _load_pickle(ENCODER_PATH)
    feature_cols = _load_pickle(FEATURE_PATH)
    return boxcox, yeo, encoder, feature_cols


def _find_model_path():
    # Prefer explicit .pkl
    if os.path.exists(DRINKING_MODEL):
        return DRINKING_MODEL
    if os.path.exists(DRINKING_MODEL_ALT):
        return DRINKING_MODEL_ALT
    # fallback: scan Models for any .pkl/.joblib/.h5
    for f in os.listdir(MODELS_DIR):
        if f.lower().endswith((".pkl", ".joblib", ".h5")):
            return os.path.join(MODELS_DIR, f)
    return None


def prepare(input_dict, boxcox, yeo, feature_cols):
    df = pd.DataFrame([input_dict])
    for col in NUM_COLS:
        if col not in df.columns:
            df[col] = 0.0

    # Apply transforms (these are sklearn transformers)
    try:
        df.loc[:, BOXCOX_COLS] = boxcox.transform(df[BOXCOX_COLS])
    except Exception as e:
        logger.exception("BoxCox transform failed: %s", e)
        raise

    try:
        df.loc[:, YEO_COLS] = yeo.transform(df[YEO_COLS])
    except Exception as e:
        logger.exception("Yeo-Johnson transform failed: %s", e)
        raise

    df = df.reindex(columns=feature_cols, fill_value=0.0)
    return df


def predict_quality(mode: str, input_dict: Dict[str, Any]):
    """
    mode: 'drinking' or 'irrigation'
    input_dict: {feature_name: float, ...}
    """
    # Load transformers & encoder
    boxcox, yeo, encoder, feature_cols = _load_transformers_and_encoder()

    # Find model file
    model_path = _find_model_path()
    if not model_path:
        raise FileNotFoundError(f"No model file found in {MODELS_DIR}. Place a .pkl/.joblib or (pickle-named) .h5 there.")

    logger.info("Loading model from %s", model_path)
    # Try loading as sklearn pickle
    try:
        model = _load_sklearn_pickle(model_path)
    except Exception as e:
        logger.exception("Failed to load model as sklearn pickle: %s", e)
        raise

    # Prepare input dataframe
    df = prepare(input_dict, boxcox, yeo, feature_cols)

    # Predict using sklearn model
    if hasattr(model, "predict"):
        pred = model.predict(df)
        pred0 = pred[0] if hasattr(pred, "__len__") else pred
        # attempt to decode using your label encoder
        try:
            decoded = encoder.inverse_transform([pred0])[0]
        except Exception:
            # maybe encoder.classes_ exists and pred0 is numeric index
            try:
                if hasattr(encoder, "classes_"):
                    classes = list(encoder.classes_)
                    decoded = classes[int(pred0)] if int(pred0) < len(classes) else str(pred0)
                else:
                    decoded = str(pred0)
            except Exception:
                decoded = str(pred0)
        logger.info("Prediction: %s", decoded)
        return decoded

    # If the object has no predict method, raise
    raise RuntimeError("Loaded model does not have a predict method.")
