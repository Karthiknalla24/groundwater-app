# test_gemini.py (introspect google.generativeai / google-ai-generativelanguage)
import os, sys, traceback
print("Python:", sys.version.replace('\\n',' '))
print("GOOGLE_API_KEY present:", bool(os.environ.get("GOOGLE_API_KEY")))

try:
    import google
    print("google package:", google.__version__ if hasattr(google, "__version__") else "no __version__")
except Exception as e:
    print("Import google failed:", e)

print("\n--- importing google.generativeai ---")
try:
    import google.generativeai as genai
    print("Imported google.generativeai as genai")
    print("genai module file:", getattr(genai, "__file__", "n/a"))
    names = sorted([n for n in dir(genai) if not n.startswith("_")])
    print("Top-level names in google.generativeai:")
    print(names)
except Exception as e:
    print("Import google.generativeai failed:", repr(e))
    traceback.print_exc()

# Try a few common helper names (no network call unless we do it explicitly)
candidates = [
    "generate_text",
    "generate",
    "chat",
    "chat.completions",
    "ChatCompletion",
    "chat_completion",
    "generate_text_with_model",
    "TextGeneration",
    "Client",
    "configure",
    "configure_api_key",
    "set_api_key",
    "get_model",
    "predict",
]

print("\n--- checking presence of common helper names ---")
try:
    import google.generativeai as genai
    for name in candidates:
        parts = name.split(".")
        obj = genai
        found = True
        for p in parts:
            if hasattr(obj, p):
                obj = getattr(obj, p)
            else:
                found = False
                break
        print(f"{name:25} -> {'callable' if found and callable(obj) else ('present' if found else 'missing')}")
except Exception as e:
    print("Skipping presence checks because import failed:", e)

# Try lower-level google.ai.generativelanguage client if available
print("\n--- trying google.ai.generativelanguage client ---")
try:
    from google.ai import generativelanguage as gl
    print("Imported google.ai.generativelanguage, client module members:", [n for n in dir(gl) if not n.startswith("_")][:40])
    # try constructing a client if available
    if hasattr(gl, "TextServiceClient"):
        try:
            client = gl.TextServiceClient()
            print("Constructed TextServiceClient successfully (no network called yet).")
            # show method names
            print("TextServiceClient methods:", [n for n in dir(client) if not n.startswith("_")][:40])
        except Exception as e:
            print("Constructing TextServiceClient failed:", repr(e))
    else:
        print("TextServiceClient not present on google.ai.generativelanguage")
except Exception as e:
    print("Import google.ai.generativelanguage failed:", repr(e))

# Small safe runtime test: attempt a lightweight generation with whichever function seems available.
print("\n--- attempting a light generation if safe function detected ---")
try:
    import google.generativeai as genai
    # Ensure API key present
    key = os.environ.get("GOOGLE_API_KEY")
    if not key:
        print("No GOOGLE_API_KEY set — skipping network calls.")
    else:
        print("GOOGLE_API_KEY present; trying a few safe invocation patterns...")
        tried = []
        # 1) genai.generate_text(...)
        try:
            if hasattr(genai, "generate_text"):
                print("Calling genai.generate_text(...)")
                resp = genai.generate_text(model="models/text-bison-001", prompt="Say hello", max_output_tokens=32)
                print("resp (generate_text) type:", type(resp))
                print("Sample text:", getattr(resp, "text", str(resp)[:200]))
                tried.append("generate_text ok")
        except Exception as e:
            print("generate_text call failed:", repr(e))
            tried.append("generate_text failed")

        # 2) genai.chat.completions.create or similar
        try:
            if hasattr(genai, "chat") and hasattr(genai.chat, "completions"):
                print("Calling genai.chat.completions.create(...)")
                resp = genai.chat.completions.create(model="models/chat-bison-001", messages=[{"role":"user","content":"Say hello"}], max_output_tokens=64)
                print("resp (chat) type:", type(resp))
                print("Sample:", str(resp)[:200])
                tried.append("chat.completions ok")
        except Exception as e:
            print("chat.completions call failed:", repr(e))
            tried.append("chat.completions failed")

        # 3) genai.ChatCompletion.create
        try:
            if hasattr(genai, "ChatCompletion") and hasattr(genai.ChatCompletion, "create"):
                print("Calling genai.ChatCompletion.create(...)")
                resp = genai.ChatCompletion.create(model="gpt-4o-mini", messages=[{"role":"user","content":"Say hello"}], max_output_tokens=64)
                print("resp (ChatCompletion) type:", type(resp))
                print("Sample:", str(resp)[:200])
                tried.append("ChatCompletion ok")
        except Exception as e:
            print("ChatCompletion call failed:", repr(e))
            tried.append("ChatCompletion failed")

        # 4) try lower-level google.ai.generativelanguage client generate_text if available
        try:
            from google.ai import generativelanguage as gl
            if hasattr(gl, "TextServiceClient"):
                print("Using TextServiceClient.generate for sample")
                client = gl.TextServiceClient()
                resp = client.generate_text(parent="projects/your-project/locations/global", model="models/text-bison-001", prompt="Say hello", max_output_tokens=32)
                print("TextServiceClient response type:", type(resp))
                tried.append("TextServiceClient ok")
        except Exception as e:
            print("TextServiceClient call failed (likely requires proper project/parent):", repr(e))
            tried.append("TextServiceClient failed")

        print("Tried:", tried)
except Exception as e:
    print("Runtime test encountered an error:", repr(e))
    traceback.print_exc()
