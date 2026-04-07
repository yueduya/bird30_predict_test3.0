from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Optional
import bcrypt
from datetime import timedelta

from auth.jwt_handler import create_access_token
from auth.dependencies import get_current_user
from database.mysql import get_user_by_username, create_user, update_last_login
from config import settings
from fastapi.templating import Jinja2Templates

router = APIRouter(prefix="/user", tags=["用户"])
templates = Jinja2Templates(directory="templates")

class LoginRequest(BaseModel):
    username: str
    password: str

class RegisterRequest(BaseModel):
    username: str
    password: str
    email: Optional[str] = None
    nickname: Optional[str] = None

@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@router.post("/login")
async def login(data: LoginRequest):
    user = get_user_by_username(data.username)
    if not user:
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    
    if not bcrypt.checkpw(data.password.encode(), user["password_hash"].encode()):
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    
    update_last_login(user["uuid"])
    
    token = create_access_token(
        data={"sub": user["uuid"]},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    
    return {
        "success": True,
        "data": {
            "access_token": token,
            "token_type": "bearer",
            "user": {
                "username": user["username"],
                "nickname": user["nickname"],
                "avatar": user["avatar"]
            }
        }
    }

@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@router.post("/register")
async def register(data: RegisterRequest):
    if get_user_by_username(data.username):
        raise HTTPException(status_code=400, detail="用户名已存在")
    
    password_hash = bcrypt.hashpw(data.password.encode(), bcrypt.gensalt()).decode()
    
    user_uuid = create_user(
        username=data.username,
        password_hash=password_hash,
        email=data.email,
        nickname=data.nickname
    )
    
    return {"success": True, "message": "注册成功", "user_uuid": user_uuid}

@router.get("/me")
async def get_user_info(user = get_current_user):
    return {"success": True, "data": user}
