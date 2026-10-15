import json
import os
import time
import secrets
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set, Tuple
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError

security_router = APIRouter(prefix="/api/security", tags=["security"])
bearer_scheme = HTTPBearer(auto_error=False)

try:
    from helpers import atomic_save_json
except ImportError:
    from server.helpers import atomic_save_json

JWT_ALGORITHM = "HS256"

def get_jwt_secret() -> str:
    """Retrieve or dynamically generate a strong persistent 256-bit JWT secret."""
    env_secret = os.environ.get("SIWAN_JWT_SECRET") or os.environ.get("FLATNOTES_SECRET_KEY")
    if env_secret and env_secret.strip():
        return env_secret.strip()
    secret_file = os.path.join(get_data_dir(), ".siwan_jwt_secret")
    if os.path.exists(secret_file):
        try:
            with open(secret_file, "r", encoding="utf-8") as f:
                s = f.read().strip()
                if len(s) >= 32:
                    return s
        except Exception:
            pass
    new_secret = secrets.token_hex(32)
    try:
        os.makedirs(os.path.dirname(secret_file), exist_ok=True)
        with open(secret_file, "w", encoding="utf-8") as f:
            f.write(new_secret)
        try:
            os.chmod(secret_file, 0o600)
        except Exception:
            pass
    except Exception as e:
        print(f"[Security] Warning: Could not persist JWT secret: {e}")
    return new_secret

def get_data_dir() -> str:
    try:
        from system_config import get_current_storage_path
        return get_current_storage_path()
    except Exception:
        try:
            from server.system_config import get_current_storage_path
            return get_current_storage_path()
        except Exception:
            return os.environ.get("SIWAN_PATH", os.environ.get("FLATNOTES_PATH", "/data"))

def get_permissions_file() -> str:
    return os.path.join(get_data_dir(), ".siwan_permissions.json")

def get_comments_file() -> str:
    return os.path.join(get_data_dir(), ".siwan_comments.json")

def get_annotations_file() -> str:
    return os.path.join(get_data_dir(), ".siwan_annotations.json")

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

class AnnotationCreateRequest(BaseModel):
    quote: str
    comment: str
    author_type: Optional[str] = "user"
    comment_type: Optional[str] = None
    status: Optional[str] = "accepted"
    model: Optional[str] = None

class AnnotationUpdateRequest(BaseModel):
    status: Optional[str] = None
    comment: Optional[str] = None

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
    atomic_save_json(filepath, data)

def get_permissions() -> Dict[str, Any]:
    default = {
        "public_notes": [],
        "all_public": False,
        "admin_password": ADMIN_PASSWORD,
        "token_version": 1
    }
    data = load_json(get_permissions_file(), default)
    if not isinstance(data, dict):
        data = default
    if "token_version" not in data:
        data["token_version"] = 1
    if "all_public" not in data:
        data["all_public"] = False
    return data

def save_permissions(data: Dict[str, Any]) -> None:
    save_json(get_permissions_file(), data)

def get_comments_data() -> Dict[str, List[Dict[str, Any]]]:
    return load_json(get_comments_file(), {})

def save_comments_data(data: Dict[str, List[Dict[str, Any]]]) -> None:
    save_json(get_comments_file(), data)

def get_annotations_data() -> Dict[str, List[Dict[str, Any]]]:
    return load_json(get_annotations_file(), {})

def save_annotations_data(data: Dict[str, List[Dict[str, Any]]]) -> None:
    save_json(get_annotations_file(), data)

def get_note_comments_paths(title: str) -> Tuple[str, str]:
    """
    Returns (per_note_comments_file, dir_comments_file) in the note's same directory.
    e.g. note at /data/SLAM/intro.md:
      per_note: /data/SLAM/intro.comments.json
      dir_comments: /data/SLAM/.comments.json
    """
    storage_path = get_data_dir()
    clean_title = title.replace("\\", "/").strip("/")
    note_path = os.path.join(storage_path, clean_title + ".md")
    note_dir = os.path.dirname(note_path)
    base_name = os.path.splitext(os.path.basename(note_path))[0]
    per_note_file = os.path.join(note_dir, f"{base_name}.comments.json")
    dir_comments_file = os.path.join(note_dir, ".comments.json")
    return per_note_file, dir_comments_file

def get_note_summary_path(title: str) -> str:
    storage_path = get_data_dir()
    clean_title = title.replace("\\", "/").strip("/")
    note_path = os.path.join(storage_path, clean_title + ".md")
    note_dir = os.path.dirname(note_path)
    base_name = os.path.splitext(os.path.basename(note_path))[0]
    return os.path.join(note_dir, f"{base_name}.summary.json")

def get_note_summary(title: str) -> Dict[str, Any]:
    summary_file = get_note_summary_path(title)
    if os.path.exists(summary_file):
        return load_json(summary_file, {})
    return {}

def save_note_summary(title: str, summary_data: Dict[str, Any]) -> None:
    summary_file = get_note_summary_path(title)
    os.makedirs(os.path.dirname(summary_file), exist_ok=True)
    save_json(summary_file, summary_data)

def get_note_annotations(title: str) -> List[Dict[str, Any]]:
    per_note_file, dir_comments_file = get_note_comments_paths(title)

    # 1. Per-note structured comments file: {title}.comments.json
    if os.path.exists(per_note_file):
        data = load_json(per_note_file, [])
        if isinstance(data, list):
            return data
        if isinstance(data, dict) and "annotations" in data:
            return data["annotations"]

    # 2. Directory-level .comments.json in note's same directory
    if os.path.exists(dir_comments_file):
        dir_data = load_json(dir_comments_file, {})
        base_name = os.path.splitext(os.path.basename(title))[0]
        if title in dir_data and isinstance(dir_data[title], list):
            return dir_data[title]
        if base_name in dir_data and isinstance(dir_data[base_name], list):
            return dir_data[base_name]

    # 3. Fallback to global legacy annotations file
    legacy_data = get_annotations_data()
    return legacy_data.get(title, [])

def save_note_annotations(title: str, annotations: List[Dict[str, Any]]) -> None:
    per_note_file, dir_comments_file = get_note_comments_paths(title)
    note_dir = os.path.dirname(per_note_file)
    os.makedirs(note_dir, exist_ok=True)

    # 1. Save per-note file in same directory
    save_json(per_note_file, annotations)

    # 2. Also sync to .comments.json in the same directory
    dir_data = load_json(dir_comments_file, {}) if os.path.exists(dir_comments_file) else {}
    base_name = os.path.splitext(os.path.basename(title))[0]
    dir_data[base_name] = annotations
    dir_data[title] = annotations
    save_json(dir_comments_file, dir_data)

    # 3. Keep legacy global file in sync for backward compatibility
    try:
        global_data = get_annotations_data()
        global_data[title] = annotations
        save_annotations_data(global_data)
    except Exception:
        pass

_CACHED_IP_DATA: Optional[Dict[str, Any]] = None
_LAST_IP_DISK_SAVE: float = 0.0
_IP_SAVE_INTERVAL: float = 30.0  # seconds

def get_ip_data() -> Dict[str, Any]:
    global _CACHED_IP_DATA
    if _CACHED_IP_DATA is not None:
        return _CACHED_IP_DATA
    default = {
        "stats": {},
        "blacklist": []
    }
    _CACHED_IP_DATA = load_json(get_ip_stats_file(), default)
    if not isinstance(_CACHED_IP_DATA, dict):
        _CACHED_IP_DATA = default
    return _CACHED_IP_DATA

def save_ip_data(data: Dict[str, Any], force: bool = False) -> None:
    global _CACHED_IP_DATA, _LAST_IP_DISK_SAVE
    _CACHED_IP_DATA = data
    now = time.time()
    if force or (now - _LAST_IP_DISK_SAVE >= _IP_SAVE_INTERVAL):
        save_json(get_ip_stats_file(), data)
        _LAST_IP_DISK_SAVE = now

# --- Admin Auth Helpers ---
def create_access_token(username: str, remember_me: bool = True) -> str:
    perms = get_permissions()
    token_ver = perms.get("token_version", 1)
    expires_delta = timedelta(days=30 if remember_me else 1)
    expire = datetime.utcnow() + expires_delta
    payload = {
        "sub": username,
        "role": "admin",
        "ver": token_ver,
        "exp": expire
    }
    return jwt.encode(payload, get_jwt_secret(), algorithm=JWT_ALGORITHM)

def is_admin_token(token: Optional[str]) -> bool:
    if not token or not isinstance(token, str):
        return False
    clean_token = token.replace("Bearer ", "").strip()
    if not clean_token:
        return False
    try:
        payload = jwt.decode(clean_token, get_jwt_secret(), algorithms=[JWT_ALGORITHM])
        if payload.get("role") != "admin":
            return False
        perms = get_permissions()
        current_ver = perms.get("token_version", 1)
        if payload.get("ver") != current_ver:
            return False
        return True
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

# --- Login Rate Limiting (Brute-Force Protection) ---
_FAILED_LOGINS: Dict[str, List[float]] = {}
_LOGIN_LOCKOUT_SECONDS = 600  # 10 minutes
_MAX_FAILED_ATTEMPTS = 5

def check_login_rate_limit(ip: str) -> None:
    now = time.time()
    attempts = _FAILED_LOGINS.get(ip, [])
    attempts = [t for t in attempts if now - t < _LOGIN_LOCKOUT_SECONDS]
    _FAILED_LOGINS[ip] = attempts
    if len(attempts) >= _MAX_FAILED_ATTEMPTS:
        wait_seconds = int(_LOGIN_LOCKOUT_SECONDS - (now - attempts[0]))
        wait_mins = max(1, wait_seconds // 60)
        raise HTTPException(
            status_code=429,
            detail=f"密码错误次数过多，该 IP 已被临时锁定。请在 {wait_mins} 分钟后再试。"
        )

def record_login_failure(ip: str) -> None:
    now = time.time()
    attempts = _FAILED_LOGINS.setdefault(ip, [])
    attempts.append(now)

def clear_login_failures(ip: str) -> None:
    _FAILED_LOGINS.pop(ip, None)

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
        is_new_ip = ip not in stats
        if is_new_ip:
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
        save_ip_data(ip_data, force=is_new_ip)

# --- Endpoints ---

@security_router.post("/login")
def admin_login(req: AdminLoginRequest, request: Request):
    client_ip = get_client_ip(request)
    check_login_rate_limit(client_ip)

    perms = get_permissions()
    expected_password = perms.get("admin_password", ADMIN_PASSWORD)
    
    if req.username.strip().lower() == ADMIN_USERNAME.lower() and req.password == expected_password:
        clear_login_failures(client_ip)
        token = create_access_token(req.username, remember_me=req.remember_me)
        return {
            "status": "success",
            "token": token,
            "access_token": token,
            "username": req.username,
            "role": "admin",
            "message": "管理员登录成功"
        }
    record_login_failure(client_ip)
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
    # Bump token_version to immediately revoke all existing tokens on all other devices/browsers
    new_ver = int(time.time())
    perms["token_version"] = new_ver
    save_permissions(perms)

    # Issue a fresh token with the new version for the current admin
    new_token = create_access_token(ADMIN_USERNAME, remember_me=True)
    return {
        "status": "success",
        "message": "管理员密码修改成功，其他已登录设备与会话已全部失效，后续登录请使用新密码。",
        "token": new_token,
        "access_token": new_token
    }

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
        stored = []
    return {
        "public_notes": stored,
        "all_public": perms.get("all_public", False),
        "is_admin": is_admin
    }

@security_router.post("/public-notes")
def set_public_notes(req: PublicNotesRequest, _: bool = Depends(verify_admin)):
    perms = get_permissions()
    perms["public_notes"] = req.public_notes
    if req.all_public is not None:
        perms["all_public"] = bool(req.all_public)
    else:
        perms["all_public"] = False
    save_permissions(perms)
    return {
        "status": "success",
        "message": f"已成功更新对外文档设置（共开放 {len(req.public_notes)} 篇）",
        "public_notes": req.public_notes,
        "all_public": perms["all_public"]
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
@security_router.get("/comments/{title:path}")
def get_comments(title: str, request: Request):
    auth_header = request.headers.get("Authorization", "").replace("Bearer ", "").strip()
    is_admin = is_admin_token(auth_header)
    if not is_admin:
        perms = get_permissions()
        if not perms.get("all_public", False):
            public_list = perms.get("public_notes", [])
            if title not in public_list:
                raise HTTPException(status_code=403, detail="无权限查看此私密文档的留言。")
    comments_data = get_comments_data()
    return {"status": "success", "comments": comments_data.get(title, [])}

@security_router.post("/comments/{title:path}")
def add_comment(title: str, req: CommentCreateRequest, request: Request):
    auth_header = request.headers.get("Authorization", "").replace("Bearer ", "").strip()
    is_admin = is_admin_token(auth_header)
    if not is_admin:
        perms = get_permissions()
        if not perms.get("all_public", False):
            public_list = perms.get("public_notes", [])
            if title not in public_list:
                raise HTTPException(status_code=403, detail="无权限在此私密文档下发表留言。")

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

@security_router.delete("/comments/{title:path}/{comment_id}")
def delete_comment(title: str, comment_id: str, _: bool = Depends(verify_admin)):
    comments_data = get_comments_data()
    note_comments = comments_data.get(title, [])
    filtered = [c for c in note_comments if c.get("id") != comment_id]
    comments_data[title] = filtered
    save_comments_data(comments_data)
    return {"status": "success", "comments": filtered, "message": "评论已删除"}

# --- Annotations API (Admin Only: 管理员批注/书签模式，保存在笔记同目录下) ---
@security_router.get("/annotations/{title:path}")
def get_annotations(title: str, _: bool = Depends(verify_admin)):
    note_annotations = get_note_annotations(title)
    return {
        "status": "success",
        "annotations": note_annotations,
    }

@security_router.post("/annotations/{title:path}")
def add_annotation(title: str, req: AnnotationCreateRequest, _: bool = Depends(verify_admin)):
    quote = req.quote.strip() if req.quote else ""
    comment = req.comment.strip() if req.comment else ""

    if not quote:
        raise HTTPException(status_code=400, detail="批注必须选中一段原文内容")
    if len(quote) > 2000:
        raise HTTPException(status_code=400, detail="批注引用的原文过长，不能超过 2000 字")
    if not comment:
        raise HTTPException(status_code=400, detail="批注内容不能为空")
    if len(comment) > 2000:
        raise HTTPException(status_code=400, detail="批注内容过长，不能超过 2000 字")

    matched = check_sensitive_content(comment)
    if matched:
        raise HTTPException(status_code=400, detail="批注内容包含违规、敏感或辱骂词汇，请文明批注")

    note_annotations = list(get_note_annotations(title))

    now_iso = datetime.now().astimezone().isoformat(timespec="seconds")
    annotation_id = f"a_{int(time.time())}_{secrets.token_hex(3)}"
    new_annotation = {
        "id": annotation_id,
        "quote": quote,
        "comment": comment,
        "author_type": req.author_type or "user",
        "comment_type": req.comment_type,
        "status": req.status or "accepted",
        "createdAt": now_iso,
        "updatedAt": now_iso,
        "created_at": now_iso,
    }
    if req.author_type == "ai":
        new_annotation["generatedAt"] = now_iso
        new_annotation["model"] = req.model or "ai"

    note_annotations.append(new_annotation)
    save_note_annotations(title, note_annotations)

    return {
        "status": "success",
        "annotations": note_annotations,
        "annotation": new_annotation,
    }

@security_router.patch("/annotations/{title:path}/{annotation_id}")
def patch_annotation(title: str, annotation_id: str, req: AnnotationUpdateRequest, _: bool = Depends(verify_admin)):
    note_annotations = get_note_annotations(title)
    updated_item = None
    now_iso = datetime.now().astimezone().isoformat(timespec="seconds")
    for item in note_annotations:
        if item.get("id") == annotation_id:
            if req.status is not None:
                item["status"] = req.status
                if req.status in ("accepted", "modified_accepted", "rejected"):
                    item["resolvedAt"] = now_iso
                elif req.status == "proposed":
                    item.pop("resolvedAt", None)
            if req.comment is not None:
                comment_clean = req.comment.strip()
                matched = check_sensitive_content(comment_clean)
                if matched:
                    raise HTTPException(status_code=400, detail="修改内容包含违规、敏感或辱骂词汇")
                item["comment"] = comment_clean
            item["updatedAt"] = now_iso
            updated_item = item
            break

    if not updated_item:
        raise HTTPException(status_code=404, detail="未找到该批注")

    save_note_annotations(title, note_annotations)
    return {
        "status": "success",
        "annotations": note_annotations,
        "annotation": updated_item,
        "message": "批注状态已更新",
    }

@security_router.delete("/annotations/{title:path}/{annotation_id}")
def delete_annotation(title: str, annotation_id: str, _: bool = Depends(verify_admin)):
    note_annotations = get_note_annotations(title)
    filtered = [a for a in note_annotations if a.get("id") != annotation_id]
    save_note_annotations(title, filtered)
    return {
        "status": "success",
        "annotations": filtered,
        "message": "批注已删除",
    }

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
    save_ip_data(ip_data, force=True)
    return {"status": "success", "message": msg, "blacklist": ip_data["blacklist"]}


# --- Note Lifecycle Synchronization Handlers ---

def handle_note_renamed(old_title: str, new_title: str) -> None:
    """Synchronize annotations, summaries, and permissions when a note is renamed."""
    # 1. Update public_notes in permissions
    try:
        perms = get_permissions()
        pub_list = perms.get("public_notes")
        if pub_list is not None and old_title in pub_list:
            pub_list.remove(old_title)
            if new_title not in pub_list:
                pub_list.append(new_title)
            perms["public_notes"] = pub_list
            save_permissions(perms)
    except Exception as e:
        print(f"[Security] Rename permission update error: {e}")

    # 2. Rename per-note comments file
    try:
        old_per_note, _ = get_note_comments_paths(old_title)
        new_per_note, _ = get_note_comments_paths(new_title)
        if os.path.exists(old_per_note):
            os.makedirs(os.path.dirname(new_per_note), exist_ok=True)
            os.replace(old_per_note, new_per_note)
    except Exception as e:
        print(f"[Security] Rename comments file error: {e}")

    # 3. Rename per-note summary file
    try:
        old_summary = get_note_summary_path(old_title)
        new_summary = get_note_summary_path(new_title)
        if os.path.exists(old_summary):
            os.makedirs(os.path.dirname(new_summary), exist_ok=True)
            summary_data = load_json(old_summary, {})
            if isinstance(summary_data, dict):
                summary_data["title"] = new_title
                save_json(new_summary, summary_data)
                try:
                    os.remove(old_summary)
                except Exception:
                    pass
            else:
                os.replace(old_summary, new_summary)
    except Exception as e:
        print(f"[Security] Rename summary file error: {e}")

    # 4. Update directory-level .comments.json
    try:
        _, old_dir_comments = get_note_comments_paths(old_title)
        _, new_dir_comments = get_note_comments_paths(new_title)
        old_base = os.path.splitext(os.path.basename(old_title))[0]
        new_base = os.path.splitext(os.path.basename(new_title))[0]

        if os.path.exists(old_dir_comments):
            old_dir_data = load_json(old_dir_comments, {})
            anns = old_dir_data.pop(old_title, None) or old_dir_data.pop(old_base, None)
            if anns:
                save_json(old_dir_comments, old_dir_data)
                if old_dir_comments == new_dir_comments:
                    old_dir_data[new_title] = anns
                    old_dir_data[new_base] = anns
                    save_json(old_dir_comments, old_dir_data)
                else:
                    new_dir_data = load_json(new_dir_comments, {}) if os.path.exists(new_dir_comments) else {}
                    new_dir_data[new_title] = anns
                    new_dir_data[new_base] = anns
                    save_json(new_dir_comments, new_dir_data)
    except Exception as e:
        print(f"[Security] Rename dir comments error: {e}")

    # 5. Global legacy comments and annotations
    try:
        comments_data = get_comments_data()
        if old_title in comments_data:
            comments_data[new_title] = comments_data.pop(old_title)
            save_comments_data(comments_data)
    except Exception as e:
        print(f"[Security] Rename global comments error: {e}")

    try:
        ann_data = get_annotations_data()
        if old_title in ann_data:
            ann_data[new_title] = ann_data.pop(old_title)
            save_annotations_data(ann_data)
    except Exception as e:
        print(f"[Security] Rename global annotations error: {e}")


def handle_note_deleted(title: str) -> None:
    """Clean up comments, summaries, and permissions when a note is deleted."""
    # 1. Update public_notes in permissions
    try:
        perms = get_permissions()
        pub_list = perms.get("public_notes")
        if pub_list is not None and title in pub_list:
            pub_list.remove(title)
            perms["public_notes"] = pub_list
            save_permissions(perms)
    except Exception as e:
        print(f"[Security] Delete permission update error: {e}")

    # 2. Delete per-note comments file
    try:
        per_note, _ = get_note_comments_paths(title)
        if os.path.exists(per_note):
            os.remove(per_note)
    except Exception as e:
        print(f"[Security] Delete comments file error: {e}")

    # 3. Delete per-note summary file
    try:
        summary_file = get_note_summary_path(title)
        if os.path.exists(summary_file):
            os.remove(summary_file)
    except Exception as e:
        print(f"[Security] Delete summary file error: {e}")

    # 4. Clean directory-level .comments.json
    try:
        _, dir_comments = get_note_comments_paths(title)
        if os.path.exists(dir_comments):
            dir_data = load_json(dir_comments, {})
            base_name = os.path.splitext(os.path.basename(title))[0]
            changed = False
            if title in dir_data:
                del dir_data[title]
                changed = True
            if base_name in dir_data:
                del dir_data[base_name]
                changed = True
            if changed:
                save_json(dir_comments, dir_data)
    except Exception as e:
        print(f"[Security] Delete dir comments error: {e}")

    # 5. Clean global legacy comments and annotations
    try:
        comments_data = get_comments_data()
        if title in comments_data:
            del comments_data[title]
            save_comments_data(comments_data)
    except Exception as e:
        print(f"[Security] Delete global comments error: {e}")

    try:
        ann_data = get_annotations_data()
        if title in ann_data:
            del ann_data[title]
            save_annotations_data(ann_data)
    except Exception as e:
        print(f"[Security] Delete global annotations error: {e}")
