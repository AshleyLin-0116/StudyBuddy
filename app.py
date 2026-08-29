import os, json
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from anthropic import Anthropic
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__, static_folder="static", static_url_path="")
CORS(app)

anthropic = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

# ── Supabase (optional — gracefully skipped if not configured) ─────────────
supabase = None
try:
    from supabase import create_client
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")
    if url and key:
        supabase = create_client(url, key)
except Exception as e:
    print(f"Supabase not configured: {e}")

def db(table):
    if supabase:
        return supabase.table(table)
    return None

# ── Serve frontend ─────────────────────────────────────────────────────────
@app.route("/")
def index():
    return send_from_directory("static", "index.html")

# ── Claude chat ────────────────────────────────────────────────────────────
@app.route("/api/chat", methods=["POST"])
def chat():
    data     = request.json
    messages = data.get("messages", [])
    system   = data.get("system", "")
    user_id  = data.get("user_id", "default")

    response = anthropic.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1000,
        system=system,
        messages=messages
    )
    reply = response.content[0].text

    # Log to Supabase if available
    t = db("sessions")
    if t:
        try:
            t.insert({"user_id": user_id, "messages": messages, "reply": reply,
                      "created_at": datetime.utcnow().isoformat()}).execute()
        except Exception as e:
            print(f"Session log error: {e}")

    return jsonify({"reply": reply})

# ── PDF / text upload ──────────────────────────────────────────────────────
@app.route("/api/upload-exam", methods=["POST"])
def upload_exam():
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files["file"]
    filename = file.filename or ""

    if filename.endswith(".txt"):
        text = file.read().decode("utf-8", errors="ignore")
        return jsonify({"text": text, "pages": None})

    if filename.endswith(".pdf"):
        try:
            import pypdf
            import io
            reader = pypdf.PdfReader(io.BytesIO(file.read()))
            pages = len(reader.pages)
            text = "\n\n".join(p.extract_text() or "" for p in reader.pages)
            return jsonify({"text": text, "pages": pages})
        except ImportError:
            return jsonify({"text": "[PDF uploaded — questions generated from course format]", "pages": None})
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    return jsonify({"error": "Unsupported file type"}), 400

# ── Progress ───────────────────────────────────────────────────────────────
@app.route("/api/progress", methods=["GET"])
def get_progress():
    user_id = request.args.get("user_id", "default")
    t = db("progress")
    if not t:
        return jsonify({})
    try:
        r = t.select("*").eq("user_id", user_id).execute()
        return jsonify(r.data[0] if r.data else {})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/progress", methods=["POST"])
def update_progress():
    data    = request.json
    user_id = data.get("user_id", "default")
    t = db("progress")
    if not t:
        return jsonify({"status": "ok (no db)"})
    try:
        existing = t.select("*").eq("user_id", user_id).execute()
        if existing.data:
            t.update(data).eq("user_id", user_id).execute()
        else:
            t.insert(data).execute()
        return jsonify({"status": "ok"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ── Weak spots ─────────────────────────────────────────────────────────────
@app.route("/api/weakspots", methods=["GET"])
def get_weakspots():
    user_id = request.args.get("user_id", "default")
    course  = request.args.get("course")
    t = db("weak_spots")
    if not t:
        return jsonify([])
    try:
        q = t.select("*").eq("user_id", user_id)
        if course:
            q = q.eq("course", course)
        return jsonify(q.execute().data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/weakspots", methods=["POST"])
def add_weakspot():
    data = request.json
    t = db("weak_spots")
    if not t:
        return jsonify({"status": "ok (no db)"})
    try:
        existing = t.select("*") \
            .eq("user_id", data["user_id"]) \
            .eq("course",  data["course"]) \
            .eq("topic",   data["topic"]).execute()
        if existing.data:
            t.update({"count": existing.data[0]["count"] + 1,
                      "updated_at": datetime.utcnow().isoformat()}) \
             .eq("id", existing.data[0]["id"]).execute()
        else:
            t.insert({**data, "count": 1,
                      "created_at": datetime.utcnow().isoformat(),
                      "updated_at": datetime.utcnow().isoformat()}).execute()
        return jsonify({"status": "ok"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ── Exams ──────────────────────────────────────────────────────────────────
@app.route("/api/exams", methods=["GET"])
def get_exams():
    user_id = request.args.get("user_id", "default")
    t = db("exams")
    if not t:
        return jsonify([])
    try:
        return jsonify(t.select("*").eq("user_id", user_id).execute().data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/exams", methods=["POST"])
def save_exam():
    data = request.json
    t = db("exams")
    if not t:
        return jsonify({"status": "ok (no db)"})
    try:
        t.insert({**data, "created_at": datetime.utcnow().isoformat()}).execute()
        return jsonify({"status": "ok"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
