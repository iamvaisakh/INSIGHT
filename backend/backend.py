import os
import tempfile
from dotenv import load_dotenv

from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware

from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains import create_retrieval_chain
from langchain_core.prompts import ChatPromptTemplate

# Load environment variables from .env file
load_dotenv()

# Set up Google API Key
# Make sure to set your GOOGLE_API_KEY in a .env file in the backend folder
# Example .env file content:
# GOOGLE_API_KEY="YOUR_API_KEY_HERE"
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    raise ValueError("GOOGLE_API_KEY environment variable not set!")

# --- FastAPI App Initialization ---
app = FastAPI(title="DocuMentor Backend")

# Configure CORS to allow frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # The origin of your React frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage for document vector stores.
# In a production app, you'd use a persistent database (e.g., Redis, Postgres with pgvector).
vector_store_cache = {}

# --- Core LangChain Logic ---

def process_and_store_document(file_path: str, file_key: str):
    """Loads, splits, embeds, and stores a document in a vector store."""
    
    # 1. Load the document
    loader = PyPDFLoader(file_path)
    docs = loader.load()

    # 2. Split the document into chunks
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    split_docs = text_splitter.split_documents(docs)

    # 3. Create embeddings
    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001", google_api_key=api_key)

    # 4. Create FAISS vector store and store it in our cache
    vector_store = FAISS.from_documents(split_docs, embedding=embeddings)
    vector_store_cache[file_key] = vector_store
    
    return vector_store


def create_conversational_chain(vector_store):
    """Creates a conversational retrieval chain."""

    # Initialize the LLM
    llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", google_api_key=api_key, temperature=0.3)

    # Create the prompt template
    prompt = ChatPromptTemplate.from_template("""
    You are a helpful assistant for question-answering tasks. 
    Answer the following question based only on the provided context.
    If you don't know the answer, just say that you don't know. Don't try to make up an answer.
    
    Context:
    {context}
    
    Question: {input}
    
    Answer:
    """)
    
    # Create the document chain
    document_chain = create_stuff_documents_chain(llm, prompt)
    
    # Create the retriever
    retriever = vector_store.as_retriever(search_kwargs={"k": 3}) # Retrieve top 3 most relevant chunks
    
    # Create the final retrieval chain
    retrieval_chain = create_retrieval_chain(retriever, document_chain)
    
    return retrieval_chain


# --- API Endpoints ---

@app.post("/upload/")
async def upload_document(file: UploadFile = File(...)):
    """
    Endpoint to upload a PDF file. The file is processed and stored in memory.
    """
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed.")
    
    try:
        # Save the uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            tmp_file.write(await file.read())
            tmp_file_path = tmp_file.name

        # Use filename as the key for our cache
        file_key = file.filename
        
        # Process and store the document
        process_and_store_document(tmp_file_path, file_key)
        
        # Clean up the temporary file
        os.unlink(tmp_file_path)

        return {"status": "success", "message": f"'{file.filename}' processed and ready for questions.", "file_key": file_key}

    except Exception as e:
        # Log the error for debugging
        print(f"Error processing file: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to process file: {e}")


@app.post("/query/")
async def query_document(file_key: str = Form(...), question: str = Form(...)):
    """
    Endpoint to ask a question about a previously uploaded document.
    """
    if file_key not in vector_store_cache:
        raise HTTPException(status_code=404, detail="Document not found. Please upload it first.")
        
    try:
        vector_store = vector_store_cache[file_key]
        conversation_chain = create_conversational_chain(vector_store)
        
        # Invoke the chain with the user's question
        response = conversation_chain.invoke({"input": question})
        
        return {"status": "success", "answer": response["answer"]}

    except Exception as e:
        print(f"Error during query: {e}")
        raise HTTPException(status_code=500, detail=f"An error occurred while answering the question: {e}")

@app.get("/")
def read_root():
    return {"message": "Welcome to DocuMentor Backend!"}