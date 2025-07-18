from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.responses import FileResponse
from dotenv import load_dotenv
import os
from chatbot import load_books_from_mongo, load_faiss_index
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationalRetrievalChain
import markdown
from starlette.middleware.sessions import SessionMiddleware

# Load .env
load_dotenv()

# Load documents and FAISS index
vectorstore = load_faiss_index()
retriever = vectorstore.as_retriever(search_type="similarity", k=3)

# Initialize LLM and memory
llm = ChatGoogleGenerativeAI(model="gemini-2.5-pro")
memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True, output_key="answer")

# Create conversational chain
qa_chain = ConversationalRetrievalChain.from_llm(
    llm=llm,
    retriever=retriever,
    memory=memory,
    return_source_documents=True,
    output_key="answer"
)

# FastAPI setup
app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key="super-secret-session-key")
app.mount("/static", StaticFiles(directory="static"), name="static")
@app.get("/favicon.ico")
async def favicon():
    return FileResponse("static/favicon.ico")
templates = Jinja2Templates(directory="templates")

# Store full chat log in memory for frontend
chat_log = []

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    # Get chat from session
    chat_log = request.session.get("chat_log", [])
    return templates.TemplateResponse("index.html", {"request": request, "chat": chat_log, "books": []})

@app.post("/", response_class=HTMLResponse)
async def chat(request: Request, question: str = Form(...)):
    result = qa_chain.invoke({"question": question})
    raw_answer = result["answer"]
    answer = markdown.markdown(raw_answer)

    # Update session chat log
    chat_log = request.session.get("chat_log", [])
    chat_log.append({"question": question, "answer": answer})
    request.session["chat_log"] = chat_log

    # Fetch retrieved docs
    retrieved_docs = result["source_documents"] if "source_documents" in result else []

    # DEBUG: Print metadata to console
    for doc in retrieved_docs:
        print("======== RETRIEVED DOC ========")
        print("PAGE CONTENT PREVIEW:\n", doc.page_content[:200])
        print("FULL METADATA:", doc.metadata)
        print("================================\n")
    books = [
        {
            "title": doc.metadata.get("title"),
            "image": doc.metadata.get("image_url"),
            "author": doc.metadata.get("author"),
            "description": doc.metadata.get("description"),
            "rating_score": doc.metadata.get("rating_score"),
            "rating_count": doc.metadata.get("rating_count"),
            "text": doc.page_content
        }
        for doc in retrieved_docs
    ]

    return templates.TemplateResponse("index.html", {
        "request": request,
        "chat": chat_log,
        "books": books
    })

@app.post("/delete", response_class=HTMLResponse)
async def delete_chat(request: Request):
    request.session["chat_log"] = []
    return RedirectResponse(url="/", status_code=303)
