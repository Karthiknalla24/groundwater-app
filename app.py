# from flask import Flask, render_template, request, redirect, url_for, flash
# from ml.predictor import predict_quality
# from ml.recommendations import get_recommendations
# from ml.insights import classify_param   # For progress-bar insights

# # =====================================================
# # Flask App Setup
# # =====================================================
# app = Flask(__name__)

# # NOTE: change this in a real deployment
# app.secret_key = "change_this_secret_key"


# # =====================================================
# # Routes
# # =====================================================

# @app.route("/")
# def index():
#     """
#     Home page – shows project information.
#     """
#     return render_template("index.html")


# @app.route("/predict", methods=["GET", "POST"])
# def predict():
#     """
#     GET  -> Show the prediction form.
#     POST -> Read form inputs, call ML model, and show result page.
#     """
#     if request.method == "GET":
#         return render_template("predict.html")

#     # -----------------------------------------------------------------
#     # POST: handle form submission
#     # -----------------------------------------------------------------
#     mode = request.form.get("mode", "drinking")  # 'drinking' or 'irrigation'

#     # Features expected from the form (names MUST match form's name attributes)
#     feature_names = [
#         "pH",
#         "Electrical_Conductivity",
#         "Total_Dissolved_Solids",
#         "Carbonate",
#         "Bicarbonate",
#         "Chloride",
#         "Fluoride",
#         "Nitrate",
#         "Sulfate",
#         "Sodium",
#         "Calcium",
#         "Magnesium",
#         "Total_Hardness",
#         "Sodium_Adsorption_Ratio",
#         "Residual_Sodium_Carbonate",
#     ]

#     input_data = {}
#     errors = []

#     # Safely parse inputs from form
#     for name in feature_names:
#         raw_value = request.form.get(name)

#         if raw_value is None or raw_value.strip() == "":
#             errors.append(f"Missing value for {name}")
#             continue

#         try:
#             input_data[name] = float(raw_value)
#         except ValueError:
#             errors.append(f"Invalid numeric value for {name}: {raw_value}")

#     # If there are parsing/validation errors, show them and redirect back
#     if errors:
#         for e in errors:
#             flash(e, "danger")
#         return redirect(url_for("predict"))

#     # Debug: check what is actually being sent to the model
#     print("=== PREDICTION REQUEST ===")
#     print("Mode:", mode)
#     print("Input data:", input_data)

#     # Call your ML prediction helper
#     try:
#         predicted_class = predict_quality(mode, input_data)
#         print("Predicted class:", predicted_class)
#     except Exception as e:
#         # Log the error in console and show a flash message to the user
#         print("Error while making prediction:", str(e))
#         flash(f"Error while making prediction: {e}", "danger")
#         return redirect(url_for("predict"))

#     # --------------------------------------------
#     # Build per-parameter insight data
#     # (for progress bars / status cards on result page)
#     # --------------------------------------------
#     insights = {}
#     for key, val in input_data.items():
#         insights[key] = classify_param(key, val)
#         # insights[key] -> { "status": ..., "color": ..., "percent": ... }

#     # --------------------------------------------
#     # Get recommendations (Gemini-based text)
#     # Pass insights as well so LLM knows Low/Normal/High for each parameter
#     # --------------------------------------------
#     try:
#         recommendations_text = get_recommendations(
#             mode,
#             predicted_class,
#             input_data,
#             insights,          # <-- pass insights here
#         )
#     except Exception as e:
#         # If recommendation generation fails, don't block the result page
#         print("Error while generating recommendations:", str(e))
#         recommendations_text = None
#         flash("Could not generate detailed recommendations. Showing prediction only.", "warning")

#     # Render result page with all details
#     return render_template(
#         "result.html",
#         mode=mode,
#         input_data=input_data,
#         predicted_class=predicted_class,
#         recommendations=recommendations_text,
#         insights=insights,          # <-- pass to template for gauges
#     )


# # =====================================================
# # Main Entry
# # =====================================================
# if __name__ == "__main__":
#     # debug=True is fine for local development
#     app.run(debug=True)



# import os
# import uuid
# import json
# import tempfile
# from typing import List, Dict, Any
# from config import GOOGLE_API_KEY
# from dotenv import load_dotenv
# import os

# load_dotenv()
# API_KEY = os.getenv("GOOGLE_API_KEY")



# from flask import (
#     Flask,
#     render_template,
#     request,
#     redirect,
#     url_for,
#     flash,
#     send_file,
# )

# import pandas as pd
# from werkzeug.utils import secure_filename

# # === Your ML helpers (use existing functions) ===
# from ml.predictor import predict_quality
# from ml.recommendations import get_recommendations
# from ml.insights import classify_param

# # =====================================================
# # Flask App Setup
# # =====================================================
# app = Flask(__name__)
# app.secret_key = os.environ.get("FLASK_SECRET", "change_this_secret_key")

# # Upload settings
# ALLOWED_EXTENSIONS = {"xls", "xlsx", "csv"}
# MAX_CONTENT_LENGTH = 32 * 1024 * 1024  # 32 MB
# app.config["MAX_CONTENT_LENGTH"] = MAX_CONTENT_LENGTH

# TMP_DIR = tempfile.gettempdir()

# # The exact feature names expected (must match form inputs / excel header)
# FEATURE_NAMES = [
#     "pH",
#     "Electrical_Conductivity",
#     "Total_Dissolved_Solids",
#     "Carbonate",
#     "Bicarbonate",
#     "Chloride",
#     "Fluoride",
#     "Nitrate",
#     "Sulfate",
#     "Sodium",
#     "Calcium",
#     "Magnesium",
#     "Total_Hardness",
#     "Sodium_Adsorption_Ratio",
#     "Residual_Sodium_Carbonate",
# ]


# def allowed_file(filename: str) -> bool:
#     return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


# def session_path(token: str) -> str:
#     safe = secure_filename(token)
#     return os.path.join(TMP_DIR, f"gw_session_{safe}.json")


# def save_rows(token: str, rows: List[Dict[str, Any]]):
#     path = session_path(token)
#     with open(path, "w", encoding="utf-8") as f:
#         json.dump(rows, f, ensure_ascii=False, indent=2)


# def load_rows(token: str) -> List[Dict[str, Any]]:
#     path = session_path(token)
#     if not os.path.exists(path):
#         return []
#     with open(path, "r", encoding="utf-8") as f:
#         return json.load(f)


# # Expose helper to Jinja templates (used to show session length)
# @app.context_processor
# def utility_processor():
#     return dict(load_rows=lambda token: load_rows(token) if token else [])


# # =====================================================
# # Routes
# # =====================================================


# @app.route("/")
# def index():
#     """Home page – shows project information."""
#     return render_template("index.html")


# @app.route("/predict", methods=["GET", "POST"])
# def predict():
#     """
#     GET  -> Show the prediction form (blank).
#     POST -> Read form inputs, call ML model, and show result page.
#             Accepts optional 'session_token' and 'sample_idx' to stay in review loop.
#     """
#     if request.method == "GET":
#         return render_template("predict.html", row=None, session_token=None, sample_idx=None, has_prev=False, has_next=False)

#     # POST
#     mode = request.form.get("mode", "drinking")
#     session_token = request.form.get("session_token")
#     sample_idx = request.form.get("sample_idx")
#     try:
#         sample_idx = int(sample_idx) if sample_idx is not None and sample_idx != "" else None
#     except Exception:
#         sample_idx = None

#     input_data = {}
#     errors = []
#     for name in FEATURE_NAMES:
#         raw_value = request.form.get(name)
#         if raw_value is None or raw_value.strip() == "":
#             errors.append(f"Missing value for {name}")
#             continue
#         try:
#             input_data[name] = float(raw_value)
#         except ValueError:
#             errors.append(f"Invalid numeric value for {name}: {raw_value}")

#     if errors:
#         for e in errors:
#             flash(e, "danger")
#         if session_token and sample_idx is not None:
#             return redirect(url_for("review_sample", token=session_token, idx=sample_idx))
#         return redirect(url_for("predict"))

#     # Prediction
#     try:
#         predicted_class = predict_quality(mode, input_data)
#     except Exception as e:
#         print("Error while making prediction:", str(e))
#         flash(f"Error while making prediction: {e}", "danger")
#         if session_token and sample_idx is not None:
#             return redirect(url_for("review_sample", token=session_token, idx=sample_idx))
#         return redirect(url_for("predict"))

#     # Insights
#     insights = {}
#     for key, val in input_data.items():
#         try:
#             insights[key] = classify_param(key, val)
#         except Exception:
#             insights[key] = {"status": "unknown", "color": "secondary", "percent": 0}

#     # Recommendations (best effort)
#     recommendations_text = None
#     try:
#         recommendations_text = get_recommendations(mode, predicted_class, input_data, insights)
#     except Exception as e:
#         print("Error while generating recommendations:", str(e))
#         flash("Could not generate detailed recommendations (LLM); showing prediction only.", "warning")
#         recommendations_text = None

#     # Decide where to go after prediction
#     action = request.form.get("action")  # 'predict' or 'predict_and_next'
#     if session_token and (session_rows := load_rows(session_token)):
#         if sample_idx is None:
#             sample_idx = 0
#         next_idx = sample_idx + 1
#         prev_idx = sample_idx - 1

#         # persist result in session rows (optional)
#         try:
#             session_rows[sample_idx]["predicted_class"] = predicted_class
#             session_rows[sample_idx]["recommendation"] = recommendations_text
#             save_rows(session_token, session_rows)
#         except Exception:
#             pass

#         if action == "predict_and_next":
#             if next_idx < len(session_rows):
#                 return redirect(url_for("review_sample", token=session_token, idx=next_idx))
#             else:
#                 flash("This was the last sample. Showing result.", "info")

#         return render_template(
#             "result.html",
#             mode=mode,
#             input_data=input_data,
#             predicted_class=predicted_class,
#             recommendations=recommendations_text,
#             insights=insights,
#             session_token=session_token,
#             sample_idx=sample_idx,
#             has_prev=(prev_idx >= 0),
#             has_next=(next_idx < len(session_rows)),
#         )

#     # Single-sample flow
#     return render_template(
#         "result.html",
#         mode=mode,
#         input_data=input_data,
#         predicted_class=predicted_class,
#         recommendations=recommendations_text,
#         insights=insights,
#         session_token=None,
#         sample_idx=None,
#         has_prev=False,
#         has_next=False,
#     )


# @app.route("/upload_excel", methods=["POST"])
# def upload_excel():
#     """
#     Accept an uploaded Excel/CSV file, validate expected columns, create a temporary
#     session with rows, and redirect to review the first sample.
#     """
#     if "excel_file" not in request.files:
#         flash("No file part in request", "danger")
#         return redirect(url_for("predict"))

#     file = request.files["excel_file"]
#     if file.filename == "":
#         flash("No file selected", "danger")
#         return redirect(url_for("predict"))

#     if not allowed_file(file.filename):
#         flash("Unsupported file type. Allowed: .xls .xlsx .csv", "danger")
#         return redirect(url_for("predict"))

#     filename = secure_filename(file.filename)
#     try:
#         ext = filename.rsplit(".", 1)[1].lower()
#         if ext == "csv":
#             df = pd.read_csv(file)
#         else:
#             df = pd.read_excel(file)
#     except Exception as e:
#         flash(f"Could not read uploaded file: {e}", "danger")
#         return redirect(url_for("predict"))

#     missing = [c for c in FEATURE_NAMES if c not in df.columns]
#     if missing:
#         flash(f"Missing required columns in uploaded file: {', '.join(missing)}", "danger")
#         return redirect(url_for("predict"))

#     rows = []
#     for _, r in df.iterrows():
#         row = {}
#         for c in FEATURE_NAMES:
#             v = r.get(c)
#             if pd.isna(v):
#                 row[c] = None
#             else:
#                 try:
#                     row[c] = float(v)
#                 except Exception:
#                     row[c] = v
#         rows.append(row)

#     token = uuid.uuid4().hex
#     save_rows(token, rows)

#     return redirect(url_for("review_sample", token=token, idx=0))


# @app.route("/review/<token>/<int:idx>", methods=["GET"])
# def review_sample(token: str, idx: int):
#     rows = load_rows(token)
#     if not rows:
#         flash("Session not found or expired. Please upload again.", "danger")
#         return redirect(url_for("predict"))

#     if idx < 0 or idx >= len(rows):
#         flash("Sample index out of range.", "danger")
#         return redirect(url_for("predict"))

#     row = rows[idx]
#     has_prev = idx > 0
#     has_next = idx < (len(rows) - 1)
#     return render_template(
#         "predict.html",
#         row=row,
#         session_token=token,
#         sample_idx=idx,
#         has_prev=has_prev,
#         has_next=has_next,
#     )


# @app.route("/download_session/<token>", methods=["GET"])
# def download_session(token: str):
#     rows = load_rows(token)
#     if not rows:
#         flash("Session not found or expired.", "danger")
#         return redirect(url_for("predict"))

#     df = pd.DataFrame(rows)
#     tmpfile = os.path.join(TMP_DIR, f"gw_predictions_{secure_filename(token)}.xlsx")
#     df.to_excel(tmpfile, index=False, sheet_name="predictions")
#     return send_file(tmpfile, as_attachment=True, download_name=f"predictions_{token}.xlsx")


# # =====================================================
# # Main Entry
# # =====================================================
# if __name__ == "__main__":
#     app.run(debug=True, host="0.0.0.0", port=5000)






# import os
# import uuid
# import json
# import tempfile
# from typing import List, Dict, Any
# from config import GOOGLE_API_KEY
# from dotenv import load_dotenv
# import os

# load_dotenv()
# API_KEY = os.getenv("GOOGLE_API_KEY")

# from flask import (
#     Flask,
#     render_template,
#     request,
#     redirect,
#     url_for,
#     flash,
#     send_file,
#     abort,
# )

# import pandas as pd
# from werkzeug.utils import secure_filename

# # === Your ML helpers (use existing functions) ===
# from ml.predictor import predict_quality
# from ml.recommendations import get_recommendations
# from ml.insights import classify_param

# # =====================================================
# # Flask App Setup
# # =====================================================
# app = Flask(__name__)
# app.secret_key = os.environ.get("FLASK_SECRET", "change_this_secret_key")

# # Upload settings
# ALLOWED_EXTENSIONS = {"xls", "xlsx", "csv"}
# MAX_CONTENT_LENGTH = 32 * 1024 * 1024  # 32 MB
# app.config["MAX_CONTENT_LENGTH"] = MAX_CONTENT_LENGTH

# TMP_DIR = tempfile.gettempdir()

# # The exact feature names expected (must match form inputs / excel header)
# FEATURE_NAMES = [
#     "pH",
#     "Electrical_Conductivity",
#     "Total_Dissolved_Solids",
#     "Carbonate",
#     "Bicarbonate",
#     "Chloride",
#     "Fluoride",
#     "Nitrate",
#     "Sulfate",
#     "Sodium",
#     "Calcium",
#     "Magnesium",
#     "Total_Hardness",
#     "Sodium_Adsorption_Ratio",
#     "Residual_Sodium_Carbonate",
# ]


# def allowed_file(filename: str) -> bool:
#     return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


# def session_path(token: str) -> str:
#     safe = secure_filename(token)
#     return os.path.join(TMP_DIR, f"gw_session_{safe}.json")


# def save_rows(token: str, rows: List[Dict[str, Any]]):
#     path = session_path(token)
#     with open(path, "w", encoding="utf-8") as f:
#         json.dump(rows, f, ensure_ascii=False, indent=2)


# def load_rows(token: str) -> List[Dict[str, Any]]:
#     path = session_path(token)
#     if not os.path.exists(path):
#         return []
#     with open(path, "r", encoding="utf-8") as f:
#         return json.load(f)


# def clamp_serial(serial_value: Any, total_count: int) -> int:
#     """
#     Accepts a serial (1-based) and returns 0-based index if valid.
#     Returns None if invalid.
#     """
#     try:
#         s = int(serial_value)
#     except Exception:
#         return None
#     if s < 1 or s > total_count:
#         return None
#     return s - 1  # convert to 0-based index


# # Expose helper to Jinja templates (used to show session length)
# @app.context_processor
# def utility_processor():
#     return dict(load_rows=lambda token: load_rows(token) if token else [])


# # =====================================================
# # Routes
# # =====================================================


# @app.route("/")
# def index():
#     """Home page – shows project information."""
#     return render_template("index.html")


# @app.route("/predict", methods=["GET", "POST"])
# def predict():
#     """
#     GET  -> Show the prediction form (blank).
#     POST -> Read form inputs, call ML model, and show result page.
#             Accepts optional 'session_token' and 'sample_idx' to stay in review loop.
#     """
#     if request.method == "GET":
#         return render_template(
#             "predict.html", row=None, session_token=None, sample_idx=None, has_prev=False, has_next=False
#         )

#     # POST
#     mode = request.form.get("mode", "drinking")
#     session_token = request.form.get("session_token")
#     sample_idx = request.form.get("sample_idx")
#     try:
#         sample_idx = int(sample_idx) if sample_idx is not None and sample_idx != "" else None
#     except Exception:
#         sample_idx = None

#     input_data = {}
#     errors = []
#     for name in FEATURE_NAMES:
#         raw_value = request.form.get(name)
#         if raw_value is None or raw_value.strip() == "":
#             errors.append(f"Missing value for {name}")
#             continue
#         try:
#             input_data[name] = float(raw_value)
#         except ValueError:
#             errors.append(f"Invalid numeric value for {name}: {raw_value}")

#     if errors:
#         for e in errors:
#             flash(e, "danger")
#         if session_token and sample_idx is not None:
#             return redirect(url_for("review_sample", token=session_token, idx=sample_idx))
#         return redirect(url_for("predict"))

#     # Prediction
#     try:
#         predicted_class = predict_quality(mode, input_data)
#     except Exception as e:
#         print("Error while making prediction:", str(e))
#         flash(f"Error while making prediction: {e}", "danger")
#         if session_token and sample_idx is not None:
#             return redirect(url_for("review_sample", token=session_token, idx=sample_idx))
#         return redirect(url_for("predict"))

#     # Insights
#     insights = {}
#     for key, val in input_data.items():
#         try:
#             insights[key] = classify_param(key, val)
#         except Exception:
#             insights[key] = {"status": "unknown", "color": "secondary", "percent": 0}

#     # Recommendations (best effort)
#     recommendations_text = None
#     try:
#         recommendations_text = get_recommendations(mode, predicted_class, input_data, insights)
#     except Exception as e:
#         print("Error while generating recommendations:", str(e))
#         flash("Could not generate detailed recommendations (LLM); showing prediction only.", "warning")
#         recommendations_text = None

#     # Decide where to go after prediction
#     action = request.form.get("action")  # 'predict' or 'predict_and_next'
#     if session_token and (session_rows := load_rows(session_token)):
#         if sample_idx is None:
#             sample_idx = 0
#         next_idx = sample_idx + 1
#         prev_idx = sample_idx - 1

#         # persist result in session rows (optional)
#         try:
#             session_rows[sample_idx]["predicted_class"] = predicted_class
#             session_rows[sample_idx]["recommendation"] = recommendations_text
#             save_rows(session_token, session_rows)
#         except Exception:
#             pass

#         if action == "predict_and_next":
#             if next_idx < len(session_rows):
#                 return redirect(url_for("review_sample", token=session_token, idx=next_idx))
#             else:
#                 flash("This was the last sample. Showing result.", "info")

#         return render_template(
#             "result.html",
#             mode=mode,
#             input_data=input_data,
#             predicted_class=predicted_class,
#             recommendations=recommendations_text,
#             insights=insights,
#             session_token=session_token,
#             sample_idx=sample_idx,
#             has_prev=(prev_idx >= 0),
#             has_next=(next_idx < len(session_rows)),
#         )

#     # Single-sample flow
#     return render_template(
#         "result.html",
#         mode=mode,
#         input_data=input_data,
#         predicted_class=predicted_class,
#         recommendations=recommendations_text,
#         insights=insights,
#         session_token=None,
#         sample_idx=None,
#         has_prev=False,
#         has_next=False,
#     )


# @app.route("/upload_excel", methods=["POST"])
# def upload_excel():
#     """
#     Accept an uploaded Excel/CSV file, validate expected columns, create a temporary
#     session with rows, and redirect to review the first sample.
#     """
#     if "excel_file" not in request.files:
#         flash("No file part in request", "danger")
#         return redirect(url_for("predict"))

#     file = request.files["excel_file"]
#     if file.filename == "":
#         flash("No file selected", "danger")
#         return redirect(url_for("predict"))

#     if not allowed_file(file.filename):
#         flash("Unsupported file type. Allowed: .xls .xlsx .csv", "danger")
#         return redirect(url_for("predict"))

#     filename = secure_filename(file.filename)
#     try:
#         ext = filename.rsplit(".", 1)[1].lower()
#         if ext == "csv":
#             df = pd.read_csv(file)
#         else:
#             df = pd.read_excel(file)
#     except Exception as e:
#         flash(f"Could not read uploaded file: {e}", "danger")
#         return redirect(url_for("predict"))

#     missing = [c for c in FEATURE_NAMES if c not in df.columns]
#     if missing:
#         flash(f"Missing required columns in uploaded file: {', '.join(missing)}", "danger")
#         return redirect(url_for("predict"))

#     rows = []
#     for _, r in df.iterrows():
#         row = {}
#         for c in FEATURE_NAMES:
#             v = r.get(c)
#             if pd.isna(v):
#                 row[c] = None
#             else:
#                 try:
#                     row[c] = float(v)
#                 except Exception:
#                     row[c] = v
#         rows.append(row)

#     token = uuid.uuid4().hex
#     save_rows(token, rows)

#     return redirect(url_for("review_sample", token=token, idx=0))


# @app.route("/review/<token>/<int:idx>", methods=["GET"])
# def review_sample(token: str, idx: int):
#     rows = load_rows(token)
#     if not rows:
#         flash("Session not found or expired. Please upload again.", "danger")
#         return redirect(url_for("predict"))

#     if idx < 0 or idx >= len(rows):
#         flash("Sample index out of range.", "danger")
#         return redirect(url_for("predict"))

#     row = rows[idx]
#     has_prev = idx > 0
#     has_next = idx < (len(rows) - 1)
#     total = len(rows)
#     # 1-based serial for display
#     serial_1_based = idx + 1
#     return render_template(
#         "predict.html",
#         row=row,
#         session_token=token,
#         sample_idx=idx,
#         has_prev=has_prev,
#         has_next=has_next,
#         total=total,
#         serial=serial_1_based,
#     )


# @app.route("/goto/<token>", methods=["POST"])
# def goto_serial(token: str):
#     """
#     Accepts form param 'serial_input' (1..N). Validates and redirects to review/<token>/<idx>.
#     """
#     rows = load_rows(token)
#     if not rows:
#         flash("Session not found or expired. Please upload again.", "danger")
#         return redirect(url_for("predict"))

#     total = len(rows)
#     serial_val = request.form.get("serial_input")
#     target_idx = clamp_serial(serial_val, total)
#     if target_idx is None:
#         flash(f"Enter a valid serial between 1 and {total}.", "danger")
#         # Redirect back to current view if available, else to first
#         # If form included current_idx param we could use it; fallback to first
#         return redirect(url_for("review_sample", token=token, idx=0))

#     return redirect(url_for("review_sample", token=token, idx=target_idx))


# @app.route("/download_session/<token>", methods=["GET"])
# def download_session(token: str):
#     rows = load_rows(token)
#     if not rows:
#         flash("Session not found or expired.", "danger")
#         return redirect(url_for("predict"))

#     df = pd.DataFrame(rows)
#     tmpfile = os.path.join(TMP_DIR, f"gw_predictions_{secure_filename(token)}.xlsx")
#     df.to_excel(tmpfile, index=False, sheet_name="predictions")
#     return send_file(tmpfile, as_attachment=True, download_name=f"predictions_{token}.xlsx")


# # =====================================================
# # Main Entry
# # =====================================================
# if __name__ == "__main__":
#     app.run(debug=True, host="0.0.0.0", port=5000)















# import os
# import uuid
# import json
# import tempfile
# from typing import List, Dict, Any

# from dotenv import load_dotenv
# load_dotenv()

# from flask import (
#     Flask,
#     render_template,
#     request,
#     redirect,
#     url_for,
#     flash,
#     send_file,
# )

# import pandas as pd
# from werkzeug.utils import secure_filename

# # ================= ML HELPERS =================
# from ml.predictor import predict_quality
# from ml.recommendations import get_recommendations
# from ml.insights import classify_param

# # ================= APP SETUP =================
# app = Flask(__name__)
# app.secret_key = os.environ.get("FLASK_SECRET", "change_this_secret_key")

# ALLOWED_EXTENSIONS = {"xls", "xlsx", "csv"}
# MAX_CONTENT_LENGTH = 32 * 1024 * 1024
# app.config["MAX_CONTENT_LENGTH"] = MAX_CONTENT_LENGTH

# TMP_DIR = tempfile.gettempdir()

# # ================= FEATURES =================
# FEATURE_NAMES = [
#     "pH",
#     "Electrical_Conductivity",
#     "Total_Dissolved_Solids",
#     "Carbonate",
#     "Bicarbonate",
#     "Chloride",
#     "Fluoride",
#     "Nitrate",
#     "Sulfate",
#     "Sodium",
#     "Calcium",
#     "Magnesium",
#     "Total_Hardness",
#     "Sodium_Adsorption_Ratio",
#     "Residual_Sodium_Carbonate",
# ]

# # ================= HELPERS =================
# def allowed_file(filename):
#     return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


# def session_path(token):
#     return os.path.join(TMP_DIR, f"gw_session_{secure_filename(token)}.json")


# def save_rows(token, rows):
#     with open(session_path(token), "w", encoding="utf-8") as f:
#         json.dump(rows, f, indent=2)


# def load_rows(token):
#     path = session_path(token)
#     if not os.path.exists(path):
#         return []
#     with open(path, "r", encoding="utf-8") as f:
#         return json.load(f)


# def safe_float(val):
#     """Cleans bad numbers like 8..05"""
#     try:
#         if pd.isna(val):
#             return None
#         return float(str(val).replace("..", "."))
#     except Exception:
#         return None


# def clamp_serial(serial, total):
#     try:
#         s = int(serial)
#         if 1 <= s <= total:
#             return s - 1
#     except Exception:
#         pass
#     return None


# # ================= JINJA ACCESS =================
# @app.context_processor
# def utility_processor():
#     return dict(load_rows=load_rows)

# # ================= ROUTES =================
# @app.route("/")
# def index():
#     return render_template("index.html")


# @app.route("/predict", methods=["GET", "POST"])
# def predict():
#     if request.method == "GET":
#         return render_template("predict.html", row=None)

#     mode = request.form.get("mode", "drinking")
#     input_data = {}
#     errors = []

#     for name in FEATURE_NAMES:
#         val = request.form.get(name)
#         if not val:
#             errors.append(f"Missing value for {name}")
#             continue
#         try:
#             input_data[name] = float(val)
#         except Exception:
#             errors.append(f"Invalid value for {name}: {val}")

#     if errors:
#         for e in errors:
#             flash(e, "danger")
#         return redirect(url_for("predict"))

#     try:
#         predicted_class = predict_quality(mode, input_data)
#     except Exception as e:
#         flash(str(e), "danger")
#         return redirect(url_for("predict"))

#     insights = {
#         k: classify_param(k, v) for k, v in input_data.items()
#     }

#     recommendations = None
#     try:
#         recommendations = get_recommendations(
#             mode, predicted_class, input_data, insights
#         )
#     except Exception:
#         flash("AI recommendations unavailable", "warning")

#     return render_template(
#         "result.html",
#         mode=mode,
#         input_data=input_data,
#         predicted_class=predicted_class,
#         insights=insights,
#         recommendations=recommendations,
#     )


# @app.route("/upload_excel", methods=["POST"])
# def upload_excel():
#     file = request.files.get("excel_file")
#     if not file or file.filename == "":
#         flash("No file selected", "danger")
#         return redirect(url_for("predict"))

#     if not allowed_file(file.filename):
#         flash("Invalid file type", "danger")
#         return redirect(url_for("predict"))

#     try:
#         df = (
#             pd.read_csv(file)
#             if file.filename.endswith(".csv")
#             else pd.read_excel(file)
#         )
#     except Exception as e:
#         flash(f"File read error: {e}", "danger")
#         return redirect(url_for("predict"))

#     if "Village" not in df.columns:
#         flash("Village column missing in Excel", "danger")
#         return redirect(url_for("predict"))

#     missing = [c for c in FEATURE_NAMES if c not in df.columns]
#     if missing:
#         flash(f"Missing columns: {', '.join(missing)}", "danger")
#         return redirect(url_for("predict"))

#     rows = []
#     for _, r in df.iterrows():
#         row = {"Village": str(r.get("Village", "")).strip()}
#         for c in FEATURE_NAMES:
#             row[c] = safe_float(r.get(c))
#         rows.append(row)

#     token = uuid.uuid4().hex
#     save_rows(token, rows)

#     return redirect(url_for("review_sample", token=token, idx=0))


# @app.route("/review/<token>/<int:idx>")
# def review_sample(token, idx):
#     rows = load_rows(token)
#     if not rows or idx < 0 or idx >= len(rows):
#         flash("Invalid session or index", "danger")
#         return redirect(url_for("predict"))

#     villages = list(dict.fromkeys(r["Village"] for r in rows if r.get("Village")))

#     return render_template(
#         "predict.html",
#         row=rows[idx],
#         session_token=token,
#         sample_idx=idx,
#         total=len(rows),
#         serial=idx + 1,
#         villages=villages,
#         selected_village=rows[idx].get("Village"),
#         has_prev=idx > 0,
#         has_next=idx < len(rows) - 1,
#     )


# @app.route("/goto/<token>", methods=["GET", "POST"])
# def goto_serial(token):
#     rows = load_rows(token)
#     if not rows:
#         flash("Session not found or expired.", "danger")
#         return redirect(url_for("predict"))

#     # ---- CASE 1: Jump by Village (GET) ----
#     village = request.args.get("village")
#     if village:
#         for idx, row in enumerate(rows):
#             if row.get("Village") == village:
#                 return redirect(url_for("review_sample", token=token, idx=idx))

#         flash(f"Village '{village}' not found.", "danger")
#         return redirect(url_for("review_sample", token=token, idx=0))

#     # ---- CASE 2: Jump by Serial (POST) ----
#     serial_val = request.form.get("serial_input")
#     try:
#         serial = int(serial_val)
#         if 1 <= serial <= len(rows):
#             return redirect(url_for("review_sample", token=token, idx=serial - 1))
#     except:
#         pass

#     flash("Invalid selection.", "danger")
#     return redirect(url_for("review_sample", token=token, idx=0))



# @app.route("/download_session/<token>")
# def download_session(token):
#     rows = load_rows(token)
#     if not rows:
#         flash("Session expired", "danger")
#         return redirect(url_for("predict"))

#     df = pd.DataFrame(rows)
#     path = os.path.join(TMP_DIR, f"predictions_{token}.xlsx")
#     df.to_excel(path, index=False)
#     return send_file(path, as_attachment=True)


# # ================= MAIN =================
# if __name__ == "__main__":
#     app.run(debug=True, host="0.0.0.0", port=5000)






import os
import uuid
import json
import tempfile
from typing import List, Dict, Any

from dotenv import load_dotenv
load_dotenv()

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    send_file,
)

import pandas as pd
from werkzeug.utils import secure_filename

# ================= ML HELPERS =================
from ml.predictor import predict_quality
from ml.recommendations import get_recommendations
from ml.insights import classify_param

# ================= APP SETUP =================
app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET", "change_this_secret_key")

ALLOWED_EXTENSIONS = {"xls", "xlsx", "csv"}
MAX_CONTENT_LENGTH = 32 * 1024 * 1024
app.config["MAX_CONTENT_LENGTH"] = MAX_CONTENT_LENGTH

TMP_DIR = tempfile.gettempdir()

# ================= FEATURES =================
FEATURE_NAMES = [
    "pH",
    "Electrical_Conductivity",
    "Total_Dissolved_Solids",
    "Carbonate",
    "Bicarbonate",
    "Chloride",
    "Fluoride",
    "Nitrate",
    "Sulfate",
    "Sodium",
    "Calcium",
    "Magnesium",
    "Total_Hardness",
    "Sodium_Adsorption_Ratio",
    "Residual_Sodium_Carbonate",
]

# ================= HELPERS =================
def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def session_path(token):
    return os.path.join(TMP_DIR, f"gw_session_{secure_filename(token)}.json")


def save_rows(token, rows):
    with open(session_path(token), "w", encoding="utf-8") as f:
        json.dump(rows, f, indent=2)


def load_rows(token):
    path = session_path(token)
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def safe_float(val):
    """Cleans bad numbers like 8..05"""
    try:
        if pd.isna(val):
            return None
        return float(str(val).replace("..", "."))
    except Exception:
        return None


def clamp_serial(serial, total):
    try:
        s = int(serial)
        if 1 <= s <= total:
            return s - 1
    except Exception:
        pass
    return None


# ================= JINJA ACCESS =================
@app.context_processor
def utility_processor():
    return dict(load_rows=load_rows)

# ================= ROUTES =================
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/predict", methods=["GET", "POST"])
def predict():
    if request.method == "GET":
        return render_template("predict.html", row=None)

    mode = request.form.get("mode", "drinking")
    input_data = {}
    errors = []

    for name in FEATURE_NAMES:
        val = request.form.get(name)
        if not val:
            errors.append(f"Missing value for {name}")
            continue
        try:
            input_data[name] = float(val)
        except Exception:
            errors.append(f"Invalid value for {name}: {val}")

    if errors:
        for e in errors:
            flash(e, "danger")
        return redirect(url_for("predict"))

    try:
        predicted_class = predict_quality(mode, input_data)
    except Exception as e:
        flash(str(e), "danger")
        return redirect(url_for("predict"))

    insights = {
        k: classify_param(k, v) for k, v in input_data.items()
    }

    recommendations = None
    try:
        recommendations = get_recommendations(
            mode, predicted_class, input_data, insights
        )
    except Exception:
        flash("AI recommendations unavailable", "warning")

    return render_template(
        "result.html",
        mode=mode,
        input_data=input_data,
        predicted_class=predicted_class,
        insights=insights,
        recommendations=recommendations,
    )


@app.route("/upload_excel", methods=["POST"])
def upload_excel():
    file = request.files.get("excel_file")
    if not file or file.filename == "":
        flash("No file selected", "danger")
        return redirect(url_for("predict"))

    if not allowed_file(file.filename):
        flash("Invalid file type", "danger")
        return redirect(url_for("predict"))

    try:
        df = (
            pd.read_csv(file)
            if file.filename.endswith(".csv")
            else pd.read_excel(file)
        )
    except Exception as e:
        flash(f"File read error: {e}", "danger")
        return redirect(url_for("predict"))

    if "Village" not in df.columns:
        flash("Village column missing in Excel", "danger")
        return redirect(url_for("predict"))

    missing = [c for c in FEATURE_NAMES if c not in df.columns]
    if missing:
        flash(f"Missing columns: {', '.join(missing)}", "danger")
        return redirect(url_for("predict"))

    rows = []
    for _, r in df.iterrows():
        row = {"Village": str(r.get("Village", "")).strip()}
        for c in FEATURE_NAMES:
            row[c] = safe_float(r.get(c))
        rows.append(row)

    token = uuid.uuid4().hex
    save_rows(token, rows)

    return redirect(url_for("review_sample", token=token, idx=0))


@app.route("/review/<token>/<int:idx>")
def review_sample(token, idx):
    rows = load_rows(token)
    if not rows or idx < 0 or idx >= len(rows):
        flash("Invalid session or index", "danger")
        return redirect(url_for("predict"))

    villages = list(dict.fromkeys(r["Village"] for r in rows if r.get("Village")))

    return render_template(
        "predict.html",
        row=rows[idx],
        session_token=token,
        sample_idx=idx,
        total=len(rows),
        serial=idx + 1,
        villages=villages,
        selected_village=rows[idx].get("Village"),
        has_prev=idx > 0,
        has_next=idx < len(rows) - 1,
    )


@app.route("/goto/<token>", methods=["GET", "POST"])
def goto_serial(token):
    rows = load_rows(token)
    if not rows:
        flash("Session not found or expired.", "danger")
        return redirect(url_for("predict"))

    # ---- CASE 1: Jump by Village (GET) ----
    village = request.args.get("village")
    if village:
        for idx, row in enumerate(rows):
            if row.get("Village") == village:
                return redirect(url_for("review_sample", token=token, idx=idx))

        flash(f"Village '{village}' not found.", "danger")
        return redirect(url_for("review_sample", token=token, idx=0))

    # ---- CASE 2: Jump by Serial (POST) ----
    serial_val = request.form.get("serial_input")
    try:
        serial = int(serial_val)
        if 1 <= serial <= len(rows):
            return redirect(url_for("review_sample", token=token, idx=serial - 1))
    except:
        pass

    flash("Invalid selection.", "danger")
    return redirect(url_for("review_sample", token=token, idx=0))


@app.route("/download_session/<token>")
def download_session(token):
    rows = load_rows(token)
    if not rows:
        flash("Session expired", "danger")
        return redirect(url_for("predict"))

    df = pd.DataFrame(rows)
    path = os.path.join(TMP_DIR, f"predictions_{token}.xlsx")
    df.to_excel(path, index=False)
    return send_file(path, as_attachment=True)


# ================= MAIN =================
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
