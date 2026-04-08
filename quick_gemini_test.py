# quick_gemini_test.py
import os
import google.generativeai as genai

key = os.environ.get("GOOGLE_API_KEY")
if not key:
    raise SystemExit("GOOGLE_API_KEY not set in environment")

# configure
genai.configure(api_key=key)

# Use a model that exists for your SDK; common modern name is "gemini-2.5-flash" or "gemini-2.0"
try:
    model = genai.GenerativeModel("gemini-2.5-flash")
except Exception as e:
    print("Could not initialize GenerativeModel, falling back to get_model():", e)
    try:
        model = genai.get_model("gemini-2.5-flash")
    except Exception as e2:
        raise SystemExit("No model available via SDK: " + str(e2))

resp = model.generate_content("Write a short one-line greeting.")
print("RESPONSE:\n", getattr(resp, "text", str(resp))[:1000])
