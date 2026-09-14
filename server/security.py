import json
import os
import time
import secrets
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError

security_router = APIRouter(prefix="/api/security", tags=["security"])
bearer_scheme = HTTPBearer(auto_error=False)

JWT_SECRET = os.environ.get("SIWAN_JWT_SECRET", os.environ.get("FLATNOTES_SECRET_KEY", "siwan-secret-key-super-secure-2026"))
JWT_ALGORITHM = "HS256"

def get_data_dir() -> str:
    try:
        from system_config import get_current_storage_path
        return get_current_storage_path()
    except Exception:
        return os.environ.get("SIWAN_PATH", os.environ.get("FLATNOTES_PATH", "/data"))

def get_permissions_file() -> str:
    return os.path.join(get_data_dir(), ".siwan_permissions.json")

def get_comments_file() -> str:
    return os.path.join(get_data_dir(), ".siwan_comments.json")

def get_ip_stats_file() -> str:
    return os.path.join(get_data_dir(), ".siwan_ip_stats.json")

# Default Admin credentials
ADMIN_USERNAME = os.environ.get("SIWAN_USERNAME", os.environ.get("FLATNOTES_USERNAME", "admin"))
ADMIN_PASSWORD = os.environ.get("SIWAN_PASSWORD", os.environ.get("FLATNOTES_PASSWORD", "admin123"))

class AdminLoginRequest(BaseModel):
    username: str
    password: str
    remember_me: bool = True

class CommentCreateRequest(BaseModel):
    author: str
    content: str

class BlacklistRequest(BaseModel):
    ip: str
    action: str  # 'add' or 'remove'

class PublicNotesRequest(BaseModel):
    public_notes: List[str]
    all_public: Optional[bool] = None

class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str

# --- Storage Helpers ---
def load_json(filepath: str, default: Any) -> Any:
    if os.path.exists(filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"[Security] Load {filepath} error: {e}")
    return default

def save_json(filepath: str, data: Any) -> None:
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_permissions() -> Dict[str, Any]:
    default = {
        "public_notes": [],
        "all_public": True,
        "admin_password": ADMIN_PASSWORD
    }
    return load_json(get_permissions_file(), default)

def save_permissions(data: Dict[str, Any]) -> None:
    save_json(get_permissions_file(), data)

def get_comments_data() -> Dict[str, List[Dict[str, Any]]]:
    return load_json(get_comments_file(), {})

def save_comments_data(data: Dict[str, List[Dict[str, Any]]]) -> None:
    save_json(get_comments_file(), data)

def get_ip_data() -> Dict[str, Any]:
    default = {
        "stats": {},
        "blacklist": []
    }
    return load_json(get_ip_stats_file(), default)

def save_ip_data(data: Dict[str, Any]) -> None:
    save_json(get_ip_stats_file(), data)

# --- Admin Auth Helpers ---
def create_access_token(username: str, remember_me: bool = True) -> str:
    expires_delta = timedelta(days=30 if remember_me else 1)
    expire = datetime.utcnow() + expires_delta
    payload = {"sub": username, "role": "admin", "exp": expire}
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def is_admin_token(token: Optional[str]) -> bool:
    if not token:
        return False
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload.get("role") == "admin"
    except JWTError:
        return False

def verify_admin(credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme)) -> bool:
    if not credentials or not is_admin_token(credentials.credentials):
        raise HTTPException(status_code=401, detail="需要管理员权限，请先登录管理员账号。")
    return True

def get_client_ip(request: Request) -> str:
    # Handle X-Forwarded-For if behind reverse proxy
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip.strip()
    return request.client.host if request.client else "127.0.0.1"

# --- Middleware Helper for IP Tracking & Blacklist ---
def check_ip_and_track(request: Request) -> None:
    ip = get_client_ip(request)
    ip_data = get_ip_data()
    
    # Check blacklist
    if ip in ip_data.get("blacklist", []):
        raise HTTPException(status_code=403, detail="您的 IP 地址已被管理员列入黑名单，禁止访问。")
    
    # Track stats (ignore static assets requests)
    path = request.url.path
    if not path.startswith("/assets") and not path.endswith((".js", ".css", ".png", ".ico", ".ttf", ".woff", ".woff2")):
        stats = ip_data.setdefault("stats", {})
        if ip not in stats:
            stats[ip] = {
                "ip": ip,
                "visits": 1,
                "first_seen": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "last_seen": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "last_path": path,
                "user_agent": request.headers.get("User-Agent", "")[:100]
            }
        else:
            stats[ip]["visits"] = stats[ip].get("visits", 0) + 1
            stats[ip]["last_seen"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            stats[ip]["last_path"] = path
        save_ip_data(ip_data)

# --- Endpoints ---

@security_router.post("/login")
def admin_login(req: AdminLoginRequest):
    perms = get_permissions()
    expected_password = perms.get("admin_password", ADMIN_PASSWORD)
    
    if req.username.strip().lower() == ADMIN_USERNAME.lower() and req.password == expected_password:
        token = create_access_token(req.username, remember_me=req.remember_me)
        return {
            "status": "success",
            "token": token,
            "access_token": token,
            "username": req.username,
            "role": "admin",
            "message": "管理员登录成功"
        }
    raise HTTPException(status_code=401, detail="管理员账号或密码错误，请核实后重试")

@security_router.post("/change-password")
def change_password(req: ChangePasswordRequest, request: Request):
    auth_header = request.headers.get("Authorization", "").replace("Bearer ", "").strip()
    if not is_admin_token(auth_header):
        raise HTTPException(status_code=403, detail="无权限：仅管理员登录后可修改密码。")
    
    perms = get_permissions()
    current_expected = perms.get("admin_password", ADMIN_PASSWORD)
    if req.old_password != current_expected:
        raise HTTPException(status_code=400, detail="原密码不正确，请重新输入。")
    
    new_pwd = req.new_password.strip()
    if len(new_pwd) < 4:
        raise HTTPException(status_code=400, detail="新密码长度不能少于 4 位字符。")
    
    perms["admin_password"] = new_pwd
    save_permissions(perms)
    return {"status": "success", "message": "管理员密码修改成功，后续登录请使用新密码。"}

@security_router.get("/status")
def get_user_status(credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme)):
    is_admin = is_admin_token(credentials.credentials) if credentials else False
    return {
        "role": "admin" if is_admin else "visitor",
        "is_admin": is_admin
    }

# --- Public Notes Selection ---
@security_router.get("/public-notes")
def get_public_notes(credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme)):
    perms = get_permissions()
    is_admin = is_admin_token(credentials.credentials) if credentials else False
    stored = perms.get("public_notes")
    if stored is None:
        try:
            import sys
            mod = sys.modules.get("main")
            if mod and hasattr(mod, "get_note_storage"):
                notes = mod.get_note_storage().search("*")
                stored = [n.title for n in notes]
            else:
                stored = []
        except Exception:
            stored = []
    return {
        "public_notes": stored,
        "is_admin": is_admin
    }

@security_router.post("/public-notes")
def set_public_notes(req: PublicNotesRequest, _: bool = Depends(verify_admin)):
    perms = get_permissions()
    perms["public_notes"] = req.public_notes
    save_permissions(perms)
    return {
        "status": "success",
        "message": f"已成功更新对外文档设置（共开放 {len(req.public_notes)} 篇）",
        "public_notes": req.public_notes
    }

import re

# Disallowed system or generic placeholder nickname patterns
SYSTEM_NAME_PATTERNS = [
    r"^访客\d*$",
    r"^游客\d*$",
    r"^热心访客$",
    r"^匿名.*$",
    r"^user\d*$",
    r"^guest\d*$",
    r"^default.*$",
    r"^未知.*$",
]

# Official / System reserved words (Disallowed for non-admin users)
RESERVED_OFFICIAL_WORDS = [
    "admin", "administrator", "管理员", "官方", "系统", "system", "root",
    "客服", "版主", "站长", "superadmin", "moderator", "owner",
    "siwannote", "siwan_note", "siwan", "flatnotes"
]

# Abusive, offensive, vulgar, or illegal words (Disallowed in nickname and comments)
SENSITIVE_WORDS = [
    # 辱骂/人身攻击
    "傻逼", "煞笔", "沙比", "煞逼", "煞b", "沙b", "sb", "shabi",
    "操你", "草泥马", "操你妈", "cnm", "nmsl", "你妈死了", "你妈的", "妈逼", "马勒戈壁", "他妈的", "tmd",
    "弱智", "脑残", "智障", "白痴", "蠢货", "蠢猪", "狗逼", "狗日的", "死全家", "去死", "王八蛋",
    "贱人", "婊子", "杂种", "畜生", "贱货", "下流", "下贱", "死妈", "孤儿", "臭傻逼", "死绝",
    # 低俗/污秽
    "鸡巴", "jb", "屌", "逼", "屄", "做爱", "性交", "约炮", "嫖娼", "卖淫", "操批", "抽插", "插你",
    # 英文辱骂
    "fuck", "fucking", "fucker", "fxxk", "shit", "bitch", "asshole", "cunt",
    "motherfucker", "dick", "pussy", "bastard", "idiot", "retard", "nigger", "faggot", "whore", "slut",
    # 违禁/违法/赌毒暴
    "枪支", "迷药", "代开发票", "赌博", "百家乐", "六合彩", "吸毒", "大麻", "海隆因", "海洛因", "冰毒",
    "炸弹", "恐怖袭击", "暴恐"
]

def normalize_text_for_filter(text: str) -> str:
    cleaned = re.sub(r"[\s\.\-_*#@!~,，。/\\`\'\"+=|\(\)\[\]\{\}：；！？]+", "", text)
    return cleaned.lower()

def check_sensitive_content(text: str) -> Optional[str]:
    """Returns the matched sensitive keyword or None"""
    normalized = normalize_text_for_filter(text)
    lower_raw = text.lower()
    for word in SENSITIVE_WORDS:
        word_norm = normalize_text_for_filter(word)
        if word_norm and word_norm in normalized:
            return word
        if word.lower() in lower_raw:
            return word
    return None

def validate_nickname(nickname: str, is_admin: bool = False) -> None:
    if not nickname or not nickname.strip():
        raise HTTPException(status_code=400, detail="昵称为必填项，请输入您的个性化自定义昵称")
    
    nick = nickname.strip()
    if len(nick) < 2 or len(nick) > 20:
        raise HTTPException(status_code=400, detail="昵称长度须在 2 ~ 20 个字符之间")
    
    if is_admin:
        return
    
    # Check generic placeholder patterns
    for pat in SYSTEM_NAME_PATTERNS:
        if re.search(pat, nick, re.IGNORECASE):
            raise HTTPException(status_code=400, detail="禁止使用系统默认或占位昵称（如访客/游客/匿名），请自定义独有昵称")
    
    # Check reserved official words
    nick_norm = normalize_text_for_filter(nick)
    for reserved in RESERVED_OFFICIAL_WORDS:
        if reserved in nick_norm or reserved in nick.lower():
            raise HTTPException(status_code=400, detail=f"昵称不能包含官方保留词（如 {reserved}），仅管理员可使用")
    
    # Check sensitive words
    matched = check_sensitive_content(nick)
    if matched:
        raise HTTPException(status_code=400, detail="昵称包含违规、敏感或辱骂词汇，请修改后重试")

def validate_comment_content(content: str) -> None:
    if not content or not content.strip():
        raise HTTPException(status_code=400, detail="留言内容不能为空")
    
    c = content.strip()
    if len(c) > 1000:
        raise HTTPException(status_code=400, detail="留言内容过长，不能超过 1000 字")
    
    matched = check_sensitive_content(c)
    if matched:
        raise HTTPException(status_code=400, detail="留言内容包含违规、敏感或辱骂词汇，请文明交流")

# --- Comments API ---
@security_router.get("/comments/{title}")
def get_comments(title: str):
    comments_data = get_comments_data()
    return {"status": "success", "comments": comments_data.get(title, [])}

@security_router.post("/comments/{title}")
def add_comment(title: str, req: CommentCreateRequest, request: Request):
    auth_header = request.headers.get("Authorization", "").replace("Bearer ", "").strip()
    is_admin = is_admin_token(auth_header)

    author = req.author.strip() if req.author else ""
    validate_nickname(author, is_admin=is_admin)

    content = req.content.strip() if req.content else ""
    validate_comment_content(content)

    ip = get_client_ip(request)
    comments_data = get_comments_data()
    note_comments = comments_data.setdefault(title, [])

    comment_id = f"c_{int(time.time())}_{secrets.token_hex(3)}"
    new_comment = {
        "id": comment_id,
        "author": author,
        "content": content,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "ip": ip
    }
    note_comments.append(new_comment)
    save_comments_data(comments_data)

    return {"status": "success", "comments": note_comments, "comment": new_comment}

@security_router.delete("/comments/{title}/{comment_id}")
def delete_comment(title: str, comment_id: str, _: bool = Depends(verify_admin)):
    comments_data = get_comments_data()
    note_comments = comments_data.get(title, [])
    filtered = [c for c in note_comments if c.get("id") != comment_id]
    comments_data[title] = filtered
    save_comments_data(comments_data)
    return {"status": "success", "comments": filtered, "message": "评论已删除"}

# --- IP Management & Blacklist API (Admin Only) ---
@security_router.get("/ip-stats")
def get_ip_stats(_: bool = Depends(verify_admin)):
    ip_data = get_ip_data()
    blacklist = set(ip_data.get("blacklist", []))
    stats_list = list(ip_data.get("stats", {}).values())
    for item in stats_list:
        ip = item.get("ip", "")
        item["is_blacklisted"] = ip in blacklist
        item["count"] = item.get("visits", 1)
        item["last_visit"] = item.get("last_seen", "")
    stats_list.sort(key=lambda x: x.get("last_seen", ""), reverse=True)
    return {
        "stats": stats_list,
        "blacklist": list(blacklist)
    }

@security_router.post("/blacklist")
def manage_blacklist(req: BlacklistRequest, request: Request, _: bool = Depends(verify_admin)):
    ip = req.ip.strip()
    if not ip:
        raise HTTPException(status_code=400, detail="IP 地址不能为空")
    
    current_ip = get_client_ip(request)
    if req.action == "add" and (ip in ("127.0.0.1", "localhost", "::1") or ip == current_ip):
        raise HTTPException(status_code=400, detail="为防止管理员锁死自身，禁止拉黑当前访问 IP 或本地回环地址")
    
    ip_data = get_ip_data()
    blacklist = set(ip_data.get("blacklist", []))

    if req.action == "add":
        blacklist.add(ip)
        msg = f"IP {ip} 已被加入黑名单，禁止访问"
    elif req.action == "remove":
        blacklist.discard(ip)
        msg = f"IP {ip} 已从黑名单中移除"
    else:
        raise HTTPException(status_code=400, detail="无效的操作类型")

    ip_data["blacklist"] = list(blacklist)
    save_ip_data(ip_data)
    return {"status": "success", "message": msg, "blacklist": ip_data["blacklist"]}
