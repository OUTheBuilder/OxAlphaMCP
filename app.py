import time, json
import httpx
from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from jose import jwt, JWTError
from database import get_db, init_db, hash_password, INVITE_CODES
from agents import AGENTS, PROVIDERS, build_prompt

SECRET = "oxalpha-change-me-secret"
app = FastAPI(title="Ox Alpha")
templates = Jinja2Templates(directory="templates")
init_db()

def make_token(user_id: int):
    return jwt.encode({"sub": str(user_id), "exp": time.time() + 86400 * 7}, SECRET, algorithm="HS256")

def current_user(request: Request):
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    if not token:
        raise HTTPException(401, "Not logged in")
    try:
        payload = jwt.decode(token, SECRET, algorithms=["HS256"])
    except JWTError:
        raise HTTPException(401, "Session expired")
    db = get_db()
    user = db.execute("SELECT * FROM users WHERE id=?", (payload["sub"],)).fetchone()
    db.close()
    if not user:
        raise HTTPException(401, "User not found")
    return user

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/api/register")
async def register(request: Request):
    data = await request.json()
    username, password, invite = data.get("username","").strip(), data.get("password",""), data.get("invite","").strip()
    if not username or not password:
        raise HTTPException(400, "Username and password required")
    if invite not in INVITE_CODES:
        raise HTTPException(403, "Invalid invite code")
    db = get_db()
    try:
        db.execute("INSERT INTO users (username, password_hash, invite_code, created_at) VALUES (?,?,?,?)",
                   (username, hash_password(password), invite, time.time()))
        db.commit()
    except Exception:
        raise HTTPException(400, "Username already taken")
    user = db.execute("SELECT * FROM users WHERE username=?", (username,)).fetchone()
    db.close()
    return {"token": make_token(user["id"]), "username": username}

@app.post("/api/login")
async def login(request: Request):
    data = await request.json()
    db = get_db()
    user = db.execute("SELECT * FROM users WHERE username=?", (data.get("username","").strip(),)).fetchone()
    db.close()
    if not user or user["password_hash"] != hash_password(data.get("password","")):
        raise HTTPException(401, "Wrong username or password")
    return {"token": make_token(user["id"]), "username": user["username"]}

@app.get("/api/me")
async def me(user=Depends(current_user)):
    return {"username": user["username"], "provider": user["provider"],
            "has_key": bool(user["api_key"]), "model": user["model"]}

@app.post("/api/settings")
async def save_settings(request: Request, user=Depends(current_user)):
    data = await request.json()
    db = get_db()
    db.execute("UPDATE users SET api_key=?, provider=?, model=? WHERE id=?",
               (data.get("api_key", user["api_key"]), data.get("provider", user["provider"]),
                data.get("model", user["model"]), user["id"]))
    db.commit(); db.close()
    return {"ok": True}

@app.get("/api/agents")
async def list_agents():
    return [{"key": k, "name": v["name"], "icon": v["icon"]} for k, v in AGENTS.items()]

@app.get("/api/pills")
async def list_pills(user=Depends(current_user)):
    db = get_db()
    pills = db.execute("SELECT * FROM pills WHERE user_id=? ORDER BY created_at DESC", (user["id"],)).fetchall()
    db.close()
    return [dict(p) for p in pills]

@app.post("/api/pills")
async def create_pill(request: Request, user=Depends(current_user)):
    data = await request.json()
    if not data.get("name") or not data.get("prompt"):
        raise HTTPException(400, "Name and prompt required")
    db = get_db()
    db.execute("INSERT INTO pills (user_id, name, icon, prompt, created_at) VALUES (?,?,?,?,?)",
               (user["id"], data["name"], data.get("icon","💊"), data["prompt"], time.time()))
    db.commit(); db.close()
    return {"ok": True}

@app.delete("/api/pills/{pill_id}")
async def delete_pill(pill_id: int, user=Depends(current_user)):
    db = get_db()
    db.execute("DELETE FROM pills WHERE id=? AND user_id=?", (pill_id, user["id"]))
    db.commit(); db.close()
    return {"ok": True}

@app.get("/api/messages")
async def get_messages(user=Depends(current_user)):
    db = get_db()
    msgs = db.execute("SELECT * FROM messages WHERE user_id=? ORDER BY created_at", (user["id"],)).fetchall()
    db.close()
    return [dict(m) for m in msgs]

@app.post("/api/chat")
async def chat(request: Request, user=Depends(current_user)):
    data = await request.json()
    text = data.get("text", "").strip()
    agent_key = data.get("agent", "chat")
    if not text:
        raise HTTPException(400, "Empty message")
    if not user["api_key"]:
        raise HTTPException(400, "Add your AI key in ⚙️ Settings first")

    prompt = build_prompt(agent_key, text)
    provider = PROVIDERS.get(user["provider"], PROVIDERS["openrouter"])

    db = get_db()
    db.execute("INSERT INTO messages (user_id, role, content, agent, created_at) VALUES (?,?,?,?,?)",
               (user["id"], "user", text, agent_key, time.time()))
    db.commit(); db.close()

    try:
        async with httpx.AsyncClient(timeout=120) as client:
            r = await client.post(provider["url"],
                headers={"Authorization": f"Bearer {user['api_key']}",
                         "HTTP-Referer": "https://oxalpha.app", "X-Title": "Ox Alpha"},
                json={"model": user["model"],
                      "messages": [{"role": "user", "content": prompt}]})
            r.raise_for_status()
            reply = r.json()["choices"][0]["message"]["content"]
    except Exception as e:
        reply = f"⚠️ AI request failed: {e}"

    db = get_db()
    db.execute("INSERT INTO messages (user_id, role, content, agent, created_at) VALUES (?,?,?,?,?)",
               (user["id"], "assistant", reply, agent_key, time.time()))
    db.commit(); db.close()
    return {"reply": reply, "agent": agent_key}
