# source ~/my_Fastapi/Fastapi_venv/bin/activate
# uvicorn main:app --reload --host 0.0.0.0 --port 8081
from fastapi import FastAPI, Request, Form
from fastapi.templating import Jinja2Templates
import anthropic
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
import os

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key="sec")
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

API_KEY = os.getenv("API_KEY")


client = anthropic.Anthropic(api_key=API_KEY)

@app.get("/", response_class=HTMLResponse)
async def chat(request: Request):
    chat_history = request.session.get("chat_history", [])
    return templates.TemplateResponse("chat.html", {"request": request, "chat_history": chat_history})

@app.post("/chat_post", response_class=HTMLResponse)
async def chat_post(request: Request, chat_input: str = Form(...)):
    chat_history = request.session.get("chat_history", [])
    
    try:

        messages = [{"role": msg["role"], "content": msg["content"]} for msg in chat_history]
        messages.append({"role": "user", "content": chat_input})
        message = client.messages.create(
            model="claude-3-5-sonnet-20240620",
            max_tokens=1000,
            temperature=0,
            # system = "You are Claude, an AI assistant. Respond in Korean.",
            system="""여기는 모델 프롬프트창""",
            messages=messages
        )
        ans = message.content[0].text if message.content else "응답을 생성하지 못했습니다."
        
        chat_history.append({"role": "user", "content": chat_input})
        chat_history.append({"role": "assistant", "content": ans})
        
        # 세션에 채팅 기록 저장 (최대 10개의 메시지 쌍만 유지)
        request.session["chat_history"] = chat_history[-20:]
        
    except Exception as e:
        print(f"Error: {str(e)}")  # 서버 콘솔에 오류 출력
        ans = f"오류 발생: {str(e)}"
        
    # return templates.TemplateResponse("chat.html", {"request": request, "chat_history": chat_history})
    return JSONResponse({"chat_history": chat_history})

@app.post("/clear_chat", response_class=HTMLResponse)
async def clear_chat(request: Request):
    request.session.clear()
    return templates.TemplateResponse("chat.html", {"request": request, "chat_history": []})
