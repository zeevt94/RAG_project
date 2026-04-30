import os
import uuid
from pathlib import Path

from flask import Flask, jsonify, render_template, request
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

print("S3_BUCKET =", os.getenv("S3_BUCKET"))

from utils.s3_utils import upload_file_to_s3, list_uploaded_files
from utils.kb_utils import (
    start_kb_ingestion_job,
    get_kb_ingestion_job,
    ask_knowledge_base,
)

app = Flask(__name__)


ALLOWED_EXTENSIONS = {".txt", ".pdf", ".md", ".docx"}
DEFAULT_TOP_K = int(os.getenv("TOP_K_RESULTS", "5"))


def allowed_file(filename: str) -> bool:
    _, ext = os.path.splitext(filename.lower()) #only right suffix (pdf,word...)
    return ext in ALLOWED_EXTENSIONS


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/debug-env")
def debug_env():
    import os
    return jsonify({
        "AWS_REGION": os.getenv("AWS_REGION"),
        "S3_BUCKET": os.getenv("S3_BUCKET"),
        "KNOWLEDGE_BASE_ID": os.getenv("KNOWLEDGE_BASE_ID"),
        "DATA_SOURCE_ID": os.getenv("DATA_SOURCE_ID"),
        "CLAUDE_MODEL_ARN": os.getenv("CLAUDE_MODEL_ARN"),
        "TOP_K_RESULTS": os.getenv("TOP_K_RESULTS"),
    })

@app.get("/health")
def health():
    return jsonify({"status": "ok"})

from flask import request

@app.post("/delete")
def delete_file():
    from utils.s3_utils import delete_file_from_s3

    data = request.get_json()
    key = data.get("key")

    if not key:
        return {"error": "Missing key"}, 400

    try:
        delete_file_from_s3(key)
        return {"message": "Deleted successfully"}
    except Exception as e:
        return {"error": str(e)}, 500
@app.get("/files")
def files():
    return jsonify({"files": list_uploaded_files()})


@app.post("/upload")
def upload():
    print("UPLOAD START")

    if "files" not in request.files:
        print("NO FILES")
        return jsonify({"error": "Send one or more files under form field 'files'."}), 400

    files = request.files.getlist("files")
    print("FILES COUNT:", len(files))

    uploaded = []

    for f in files:
        print("FILE:", f.filename)

        object_key = f"upload/{uuid.uuid4().hex}_{f.filename}"
        print("S3 UPLOAD START:", object_key)

        upload_file_to_s3(
            fileobj=f,
            object_key=object_key,
            content_type=f.mimetype or "application/octet-stream"
        )

        print("S3 UPLOAD DONE")

        uploaded.append({"filename": f.filename, "s3_key": object_key})

    print("KB INGESTION START")

    ingestion = start_kb_ingestion_job(
        description=f"Manual ingestion triggered from UI for {len(uploaded)} uploaded file(s)."
    )

    print("KB INGESTION DONE:", ingestion)

    return jsonify({
        "message": "Files uploaded to S3 and knowledge base sync started.",
        "uploaded": uploaded,
        "ingestion_job": ingestion,
    })


@app.get("/ingestion/<job_id>")
def ingestion_status(job_id: str):
    data = get_kb_ingestion_job(job_id)
    return jsonify(data)


@app.post("/ask")
def ask():
    payload = request.get_json(silent=True) or {}
    question = (payload.get("question") or "").strip()
    top_k = int(payload.get("top_k") or DEFAULT_TOP_K)

    if not question:
        return jsonify({"error": "Question is required."}), 400

    response = ask_knowledge_base(question=question, top_k=top_k)
    return jsonify(response)


if __name__ == "__main__":
    port = int(os.getenv("PORT", "8080"))
    app.run(host="0.0.0.0", port=port, debug=True)
