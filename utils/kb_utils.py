import os
import boto3
from botocore.exceptions import ClientError

AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
KNOWLEDGE_BASE_ID = os.environ["KNOWLEDGE_BASE_ID"]
DATA_SOURCE_ID = os.environ["DATA_SOURCE_ID"]
MODEL_ARN = os.getenv("CLAUDE_MODEL_ARN")
print("MODEL_ARN FROM ENV =", repr(MODEL_ARN))

bedrock_agent = boto3.client("bedrock-agent", region_name=AWS_REGION)
bedrock_agent_runtime = boto3.client("bedrock-agent-runtime", region_name=AWS_REGION)


def start_kb_ingestion_job(description: str | None = None):
    response = bedrock_agent.start_ingestion_job(
        knowledgeBaseId=KNOWLEDGE_BASE_ID,
        dataSourceId=DATA_SOURCE_ID,
        description=description or "Triggered from Flask upload endpoint.",
    )
    return response["ingestionJob"]


def get_kb_ingestion_job(ingestion_job_id: str):
    response = bedrock_agent.get_ingestion_job(
        knowledgeBaseId=KNOWLEDGE_BASE_ID,
        dataSourceId=DATA_SOURCE_ID,
        ingestionJobId=ingestion_job_id,
    )
    return response["ingestionJob"]


def ask_knowledge_base(question: str, top_k: int = 5):
    response = bedrock_agent_runtime.retrieve_and_generate(
        input={"text": question},
        retrieveAndGenerateConfiguration={
            "type": "KNOWLEDGE_BASE",
            "knowledgeBaseConfiguration": {
                "knowledgeBaseId": KNOWLEDGE_BASE_ID,
                "modelArn": MODEL_ARN,
                "retrievalConfiguration": {
                    "vectorSearchConfiguration": {
                        "numberOfResults": top_k
                    }
                },
                "generationConfiguration": {
    "promptTemplate": {
        "textPromptTemplate": """
You are a helpful assistant.
Answer the user's question using only the retrieved knowledge base context.
Do not output tool calls, actions, function calls, or search commands.
If the answer is not found in the retrieved context, say: "I don't know based on the uploaded documents."

<context>
$search_results$
</context>

Question: $query$

Answer:
"""
    },
    "inferenceConfig": {
        "textInferenceConfig": {
            "maxTokens": 512,
            "temperature": 0.2,
            "topP": 0.9,
        }
    }
}
            }
        }
    )

    citations = []
    for item in response.get("citations", []):
        citation_text = ""
        generated_response_part = item.get("generatedResponsePart", {})
        text_response_part = generated_response_part.get("textResponsePart", {})
        citation_text = text_response_part.get("text", "")

        refs = []
        for ref in item.get("retrievedReferences", []):
            location = ref.get("location", {})
            s3_loc = location.get("s3Location", {})
            refs.append({
                "text": ref.get("content", {}).get("text", ""),
                "s3_uri": s3_loc.get("uri"),
                "metadata": ref.get("metadata", {}),
            })

        citations.append({
            "generated_text": citation_text,
            "references": refs,
        })

    return {
        "answer": response.get("output", {}).get("text", ""),
        "session_id": response.get("sessionId"),
        "citations": citations,
        "raw_response": response,
    }
