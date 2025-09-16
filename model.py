from sentence_transformers import SentenceTransformer
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.output_parsers import StrOutputParser
from langchain.prompts import ChatPromptTemplate
from langchain.embeddings.base import Embeddings
from langchain.schema import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sqlalchemy import create_engine, inspect
from tidb_vector.integrations import TiDBVectorClient
import os
import boto3
import time
import requests
from dotenv import load_dotenv
from check_fbi_most_wanted import check_fbi_most_wanted
from inform_nearest_police_stations import inform_police_stations

# Load environment variables from .env file
load_dotenv()

# ---------------- CONFIG ----------------
connection_string = os.getenv("TIDB_CONNECTION_STRING")
api_key = os.getenv("GEMINI_API_KEY")

# AWS config
bucket_name = os.getenv("AWS_BUCKET_NAME")
aws_region = os.getenv("AWS_REGION")
aws_s3_bucket = os.getenv("AWS_S3_BUCKET")


def find_similar_case_review_data(query_string, db):
    if not isinstance(db, TiDBVectorClient):
        raise TypeError(f"Expected TiDBVectorClient, got {type(db)}")

    docs1 = db.query(text_to_embedding(query_string), k=3)
    print(docs1)
    return docs1

def get_langchain_to_perform_query():
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        temperature=0,
        max_tokens=None,
        timeout=None,
        max_retries=2,
        api_key=api_key,
    )

    template = """
    Based on the context provided, answer the following question as accurately as possible.
    If the information is not available in the context, respond with "I don't know."

    Context: {context}
    Question: {question}
    """
    prompt = ChatPromptTemplate.from_template(template)
    return prompt | llm | StrOutputParser()


def perform_query(query_string, db):
    similar_data = find_similar_case_review_data(query_string, db)
    chain = get_langchain_to_perform_query()
    return chain.invoke({"context": similar_data, "question": query_string})


def upload_video_to_s3(file_path, bucket_name, object_name=None):
    if object_name is None:
        object_name = os.path.basename(file_path)

    s3_client = boto3.client("s3")

    try:
        s3_client.upload_file(file_path, bucket_name, object_name)
        print(f"File {file_path} uploaded to bucket {bucket_name} as {object_name}.")
    except Exception as e:
        print(f"Failed to upload {file_path} to S3: {e}")


def fetch_media_uri_from_s3(criminal_name):
    return f"s3://{aws_s3_bucket}/{criminal_name}.mp4"

embed_model = SentenceTransformer("sentence-transformers/msmarco-MiniLM-L12-cos-v5", trust_remote_code=True)
embed_model_dims = embed_model.get_sentence_embedding_dimension()

def text_to_embedding(text):
    """Generates vector embeddings for the given text."""
    embedding = embed_model.encode(text)
    return embedding.tolist()

def transcribe_interrogation_video_to_text(criminal_name):
    transcribe_client = boto3.client("transcribe", region_name=aws_region)
    video_url = fetch_media_uri_from_s3(criminal_name)
    already_exist = False

    try:
        transcribe_client.start_transcription_job(
            TranscriptionJobName=criminal_name,
            Media={"MediaFileUri": video_url},
            MediaFormat="mp4",
            LanguageCode="en-US",
        )
    except:
        print(f"Transcription job '{criminal_name}' already exists. Checking status...")
        already_exist = True

    while True:
        job = transcribe_client.get_transcription_job(TranscriptionJobName=criminal_name)
        job_status = job["TranscriptionJob"]["TranscriptionJobStatus"]

        if job_status == "COMPLETED":
            print("Transcription completed successfully.")
            break
        elif job_status == "FAILED":
            raise Exception(f"Transcription job '{criminal_name}' failed.")
        else:
            print("Waiting for transcription to complete...")
            time.sleep(10)  # Wait 10 seconds before checking again

    interrogation_report_uri = job["TranscriptionJob"]["Transcript"]["TranscriptFileUri"]
    report_json = requests.get(interrogation_report_uri).json()
    interrogation_report = report_json["results"]["transcripts"][0]["transcript"]
    return interrogation_report, already_exist

# ---------------- MAIN ----------------
def perform_query_from_ui(query_string, criminal_name):
    transcription_text, already_exist = transcribe_interrogation_video_to_text(criminal_name)
    documents = [Document(page_content=transcription_text)]

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=200,
        chunk_overlap=20
    )
    docs = text_splitter.split_documents(documents)
    db = TiDBVectorClient(
        table_name=criminal_name,
        connection_string=connection_string,
        vector_dimension=embed_model_dims,
        drop_existing_table=True,
    )

    for doc in docs:
        db.insert(
            texts=[doc.page_content],
            embeddings=[text_to_embedding(doc.page_content)],  # generate vector
        )

    result =  perform_query(query_string, db)
    try:
        fbi_matches = check_fbi_most_wanted(criminal_name)
        if fbi_matches:
            print(f"⚠️ Suspect {criminal_name} found in FBI Most Wanted:")
            for match in fbi_matches:
                print(match)

        inform_police_stations(criminal_name)
    except Exception as e:
        print(f"Error Occurred {e}")

    return {"llm_result": result, "fbi_matches": fbi_matches}

#print(perform_query_from_ui('Who Killed', 'VincentRomano'))

