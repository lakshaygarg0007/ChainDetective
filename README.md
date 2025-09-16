# 🚨 ChainDetective  

ChainDetective is an AI-powered investigative assistant that helps law enforcement analyze interrogation videos, generate searchable reports, and retrieve insights instantly using **TiDB Serverless**, **AWS Transcribe**, and **Google Gemini**. It also integrates with the **FBI Most Wanted API** and can notify **nearest police stations** via **Twilio SMS/WhatsApp alerts**.  

🔗 **Live Demo:** [https://chaindetective.onrender.com](https://chaindetective.onrender.com)  

---

## ⚙️ Prerequisites  

- **Python 3.9+ environment**  
- **TiDB Serverless** on TiDB Cloud (for vector search).  
- **AWS Account** with:  
  - S3 bucket (for video storage).  
  - Transcribe service enabled (for video-to-text).  
- **API Keys**:  
  - Hugging Face token (for embeddings).  
  - Google Gemini API key (for LLM queries).  
  - Twilio credentials (for SMS/WhatsApp alerts).  

### Install Dependencies  
```bash
pip install -r requirements.txt
```

### Code Flow

  Upload Video → Interrogation recordings are uploaded to AWS S3 (demo videos already available).
  
  Transcription → Videos are converted into text reports using AWS Transcribe
  (function: transcribe_interrogation_video_to_text).
  
  Chunking → Reports are split into smaller chunks using LangChain RecursiveCharacterTextSplitter (chunk size = 200).
  
  Embeddings → Each chunk is converted into embeddings using SentenceTransformer (Hugging Face model).
  
  Storage in TiDB → Chunks + embeddings are stored in a TiDB Vector Table (one table per criminal).
  
  Querying →
  
  Officer enters a query (e.g., “Did the suspect mention the weapon?”).
  
  Query → converted into embedding.
  
  Vector Search performed in TiDB to find top-k relevant chunks
  (function: find_similar_case_review_data).
  
  LLM Processing → Similar chunks + query are sent to Gemini LLM for a final refined answer.
  
  Alerting (Optional) → If suspect matches FBI Most Wanted, nearest police stations are informed via Twilio SMS/WhatsApp API.


### Testing via UI

Install dependencies:
    pip install -r requirements.txt
Run Flask server locally:
    set FLASK_APP=app.py
    flask run
