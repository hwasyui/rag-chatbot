from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from dotenv import load_dotenv
import os

from chatbot import load_books, create_faiss_index
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationalRetrievalChain

# Load .env
load_dotenv()
os.environ["GOOGLE_API_KEY"] = os.getenv("GOOGLE_API_KEY")

# Load documents and FAISS index
docs = load_books("data/cleaned_fantasy_books.json")
vectorstore = create_faiss_index(docs)
retriever = vectorstore.as_retriever(search_type="similarity", k=3)

# Initialize LLM and memory
llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash")
memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)

# Create conversational chain
qa_chain = ConversationalRetrievalChain.from_llm(
    llm=llm,
    retriever=retriever,
    memory=memory
)

# FastAPI setup
app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Store full chat log in memory for frontend
chat_log = []

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "chat": chat_log, "books": []})

@app.post("/", response_class=HTMLResponse)
async def chat(request: Request, question: str = Form(...)):
    result = qa_chain({"question": question})
    answer = result["answer"]

    # Store user + bot message
    chat_log.append({"question": question, "answer": answer})

    # Fetch retrieved docs
    docs = retriever.get_relevant_documents(question)
    books = [
        {
            "title": doc.metadata.get("title"),
            "image": doc.metadata.get("image_url"),
            "text": doc.page_content
        }
        for doc in docs
    ]

    return templates.TemplateResponse("index.html", {
        "request": request,
        "chat": chat_log,
        "books": books
    })
