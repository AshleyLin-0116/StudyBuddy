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

# ── Supabase ───────────────────────────────────────────────────────────────
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

    t = db("sessions")
    if t:
        try:
            t.insert({
                "user_id": user_id,
                "messages": messages,
                "reply": reply,
                "created_at": datetime.utcnow().isoformat()
            }).execute()
        except Exception as e:
            print(f"Session log error: {e}")

    return jsonify({"reply": reply})

# ── PDF / text upload ──────────────────────────────────────────────────────
@app.route("/api/upload-exam", methods=["POST"])
def upload_exam():
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file     = request.files["file"]
    filename = file.filename or ""
    user_id  = request.form.get("user_id", "default")
    course   = request.form.get("course", "")

    if filename.endswith(".txt"):
        text  = file.read().decode("utf-8", errors="ignore")
        pages = None
    elif filename.endswith(".pdf"):
        try:
            import pypdf, io
            reader = pypdf.PdfReader(io.BytesIO(file.read()))
            pages  = len(reader.pages)
            text   = "\n\n".join(p.extract_text() or "" for p in reader.pages)
        except ImportError:
            text  = "[PDF uploaded — questions generated from course format]"
            pages = None
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    else:
        return jsonify({"error": "Unsupported file type"}), 400

    # Save to Supabase
    saved_id = None
    t = db("uploaded_exams")
    if t:
        try:
            result = t.insert({
                "user_id":    user_id,
                "course":     course,
                "name":       filename,
                "text":       text,
                "pages":      pages,
                "created_at": datetime.utcnow().isoformat()
            }).execute()
            saved_id = result.data[0]["id"] if result.data else None
        except Exception as e:
            print(f"Exam save error: {e}")

    return jsonify({"text": text, "pages": pages, "id": saved_id, "name": filename})

# ── Get uploaded exams per course ──────────────────────────────────────────
@app.route("/api/uploaded-exams", methods=["GET"])
def get_uploaded_exams():
    user_id = request.args.get("user_id", "default")
    course  = request.args.get("course")
    t = db("uploaded_exams")
    if not t:
        return jsonify([])
    try:
        q = t.select("id, user_id, course, name, pages, created_at").eq("user_id", user_id)
        if course:
            q = q.eq("course", course)
        return jsonify(q.order("created_at", desc=True).execute().data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ── Get full exam text by ID ───────────────────────────────────────────────
@app.route("/api/uploaded-exams/<exam_id>", methods=["GET"])
def get_exam_text(exam_id):
    t = db("uploaded_exams")
    if not t:
        return jsonify({})
    try:
        result = t.select("*").eq("id", exam_id).execute()
        return jsonify(result.data[0] if result.data else {})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ── Delete uploaded exam ───────────────────────────────────────────────────
@app.route("/api/uploaded-exams/<exam_id>", methods=["DELETE"])
def delete_exam(exam_id):
    t = db("uploaded_exams")
    if not t:
        return jsonify({"status": "ok (no db)"})
    try:
        t.delete().eq("id", exam_id).execute()
        return jsonify({"status": "ok"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ── Save practice problem ──────────────────────────────────────────────────
@app.route("/api/practice-problems", methods=["POST"])
def save_practice_problem():
    data = request.json
    t = db("practice_problems")
    if not t:
        return jsonify({"status": "ok (no db)"})
    try:
        t.insert({
            "user_id":     data.get("user_id", "default"),
            "course":      data.get("course", ""),
            "mode":        data.get("mode", "buddy"),
            "question":    data.get("question", ""),
            "user_answer": data.get("user_answer", ""),
            "feedback":    data.get("feedback", ""),
            "weak_spot":   data.get("weak_spot", False),
            "created_at":  datetime.utcnow().isoformat()
        }).execute()
        return jsonify({"status": "ok"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ── Get practice problems per course ──────────────────────────────────────
@app.route("/api/practice-problems", methods=["GET"])
def get_practice_problems():
    user_id = request.args.get("user_id", "default")
    course  = request.args.get("course")
    limit   = int(request.args.get("limit", 50))
    t = db("practice_problems")
    if not t:
        return jsonify([])
    try:
        q = t.select("*").eq("user_id", user_id)
        if course:
            q = q.eq("course", course)
        return jsonify(q.order("created_at", desc=True).limit(limit).execute().data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

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
            t.update({
                "count":      existing.data[0]["count"] + 1,
                "updated_at": datetime.utcnow().isoformat()
            }).eq("id", existing.data[0]["id"]).execute()
        else:
            t.insert({
                **data,
                "count":      1,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }).execute()
        return jsonify({"status": "ok"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ── Exam schedule ──────────────────────────────────────────────────────────
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
        t.insert({
            **data,
            "created_at": datetime.utcnow().isoformat()
        }).execute()
        return jsonify({"status": "ok"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/exams/<exam_id>", methods=["PATCH"])
def update_exam(exam_id):
    data = request.json
    t = db("exams")
    if not t:
        return jsonify({"status": "ok (no db)"})
    try:
        t.update(data).eq("id", exam_id).execute()
        return jsonify({"status": "ok"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)