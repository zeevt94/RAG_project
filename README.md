# AWS Bedrock Knowledge Base RAG App

This project is a Flask-based RAG application that uses **Amazon Bedrock Knowledge Bases** instead of managing embeddings and vector search manually.

## Flow

1. User uploads files through the browser.
2. Flask uploads the files to **Amazon S3** using `boto3`.
3. Flask starts a **Knowledge Base ingestion job**.
4. Amazon Bedrock Knowledge Base syncs the S3 data source.
5. User asks a question through the UI.
6. Flask calls `retrieve_and_generate` using the Knowledge Base and Claude.
7. The app returns a grounded answer with citations.

## Project Structure

```text
aws-rag-kb-app/
├── app.py
├── requirements.txt
├── .env.example
├── README.md
├── templates/
│   └── index.html
├── utils/
│   ├── kb_utils.py
│   └── s3_utils.py
├── scripts/
│   └── smoke_test.py
└── systemd/
    └── rag-kb-api.service
```

## Prerequisites

- Python 3.11+
- AWS account
- S3 bucket
- Amazon Bedrock Knowledge Base
- Data source connected to the S3 bucket
- Access to an Anthropic Claude model in Bedrock
- IAM permissions for:
  - `s3:PutObject`
  - `s3:ListBucket`
  - `bedrock:RetrieveAndGenerate`
  - Bedrock Knowledge Base ingestion actions

## Setup

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure environment

Copy `.env.example` to `.env` and fill in the values:

```bash
cp .env.example .env
```

### 3. Run locally

```bash
python app.py
```

Open:

```text
http://127.0.0.1:5000
```

## Suggested AWS Setup

- Create an **S3 bucket**
- Create a **Knowledge Base** in Amazon Bedrock
- Connect the Knowledge Base to the S3 bucket as a **data source**
- Note the:
  - `KNOWLEDGE_BASE_ID`
  - `DATA_SOURCE_ID`
  - Claude model ARN

## Notes

- This version intentionally uses **Knowledge Base** because the project requirement says it is mandatory.
- The app uploads to S3 from the UI, then starts a Knowledge Base sync.
- Since retrieval is managed by Bedrock Knowledge Bases, you do not need manual FAISS/OpenSearch code in the Flask app.
- Depending on your vector store and ingestion timing, newly uploaded files may take a short time to become queryable after ingestion completes.

## Example endpoints

- `GET /health`
- `GET /files`
- `POST /upload`
- `GET /ingestion/<job_id>`
- `POST /ask`

## Example `/ask` request

```json
{
  "question": "What are the main topics in the uploaded documents?",
  "top_k": 5
}
```
