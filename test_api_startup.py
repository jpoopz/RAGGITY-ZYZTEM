import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("Step 1: Testing imports...", file=sys.stderr)
try:
    from flask import Flask
    print("   Flask imported", file=sys.stderr)
except Exception as e:
    print(f"   Flask import failed: {e}", file=sys.stderr)
    sys.exit(1)

try:
    from flask_cors import CORS
    print("   Flask-CORS imported", file=sys.stderr)
except Exception as e:
    print(f"   Flask-CORS import failed: {e}", file=sys.stderr)
    sys.exit(1)

try:
    from query_llm import answer, retrieve_local_context
    print("   query_llm imported", file=sys.stderr)
except Exception as e:
    print(f"   query_llm import failed: {e}", file=sys.stderr)
    import traceback
    traceback.print_exc(file=sys.stderr)
    sys.exit(1)

print("Step 2: Creating Flask app...", file=sys.stderr)
app = Flask(__name__)
CORS(app)

@app.route('/health', methods=['GET'])
def health():
    return {"status": "ok"}

print("Step 3: Starting server...", file=sys.stderr)
if __name__ == '__main__':
    try:
        app.run(host='127.0.0.1', port=5000, debug=False)
    except Exception as e:
        print(f" Server failed to start: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)
