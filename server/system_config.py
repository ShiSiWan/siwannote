import json
import os
import shutil
from typing import List, Optional
from pydantic import BaseModel
from fastapi import APIRouter, HTTPException, Request

try:
    import security
except ImportError:
    from server import security

system_router = APIRouter(prefix="/api/system", tags=["system"])

APP_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SERVER_CONFIG_FILE = os.path.join(APP_ROOT, ".siwan_server_config.json")
DEFAULT_DATA_DIR = os.path.join(APP_ROOT, "data")

def load_server_config() -> dict:
    if os.path.exists(SERVER_CONFIG_FILE):
        try:
            with open(SERVER_CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def save_server_config(cfg: dict) -> None:
    os.makedirs(APP_ROOT, exist_ok=True)
    with open(SERVER_CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)

def get_current_storage_path() -> str:
    cfg = load_server_config()
    p = cfg.get("storage_path")
    if p and os.path.isdir(p):
        return p
    return os.environ.get("SIWAN_PATH", os.environ.get("FLATNOTES_PATH", DEFAULT_DATA_DIR))

def save_storage_path(new_path: str) -> None:
    cfg = load_server_config()
    cfg["storage_path"] = new_path
    save_server_config(cfg)

def get_notes_count_in_dir(path: str) -> int:
    if not os.path.isdir(path):
        return 0
    count = 0
    skip_dirs = {".siwan_index", ".flatnotes", "attachments", ".git", "__pycache__", ".well-known"}
    for root, dirs, files in os.walk(path):
        dirs[:] = [d for d in dirs if d not in skip_dirs and not d.startswith(".")]
        for f in files:
            if f.endswith(".md") and not f.startswith("."):
                count += 1
    return count

def sync_storage_contents(src_dir: str, dst_dir: str) -> dict:
    """Copy all markdown files, attachments, and configuration files from src_dir to dst_dir."""
    if not os.path.exists(src_dir) or not os.path.isdir(src_dir):
        return {"copied_notes": 0, "copied_attachments": 0}

    os.makedirs(dst_dir, exist_ok=True)
    copied_notes = 0
    copied_attachments = 0

    # 1. Copy all markdown files (including subdirectories)
    skip_dirs = {".siwan_index", ".flatnotes", "attachments", ".git", "__pycache__", ".well-known"}
    for root, dirs, files in os.walk(src_dir):
        dirs[:] = [d for d in dirs if d not in skip_dirs and not d.startswith(".")]
        for f in files:
            if f.endswith(".md") and not f.startswith("."):
                rel_path = os.path.relpath(os.path.join(root, f), src_dir)
                target_file = os.path.join(dst_dir, rel_path)
                os.makedirs(os.path.dirname(target_file), exist_ok=True)
                if not os.path.exists(target_file):
                    shutil.copy2(os.path.join(root, f), target_file)
                    copied_notes += 1

    # 2. Copy attachments
    src_att = os.path.join(src_dir, "attachments")
    dst_att = os.path.join(dst_dir, "attachments")
    if os.path.exists(src_att) and os.path.isdir(src_att):
        os.makedirs(dst_att, exist_ok=True)
        for f in os.listdir(src_att):
            src_f = os.path.join(src_att, f)
            dst_f = os.path.join(dst_att, f)
            if os.path.isfile(src_f) and not os.path.exists(dst_f):
                shutil.copy2(src_f, dst_f)
                copied_attachments += 1

    # 3. Copy permissions / comments / ai_config
    for cfg_name in [".siwan_permissions.json", ".siwan_comments.json", ".siwan_ai_config.json"]:
        src_cfg = os.path.join(src_dir, cfg_name)
        dst_cfg = os.path.join(dst_dir, cfg_name)
        if os.path.exists(src_cfg) and not os.path.exists(dst_cfg):
            try:
                shutil.copy2(src_cfg, dst_cfg)
            except Exception:
                pass

    return {"copied_notes": copied_notes, "copied_attachments": copied_attachments}

def update_runtime_storage(target_path: str) -> None:
    """Hot-reload note_storage and attachment_storage in running FastAPI application."""
    import sys
    os.environ["SIWAN_PATH"] = target_path
    os.environ["FLATNOTES_PATH"] = target_path
    for mod_name in ["main", "server.main"]:
        if mod_name in sys.modules:
            mod = sys.modules[mod_name]
            if hasattr(mod, "global_config"):
                mod.global_config.storage_path = target_path
            if hasattr(mod, "_current_storage_path"):
                mod._current_storage_path = None
            if hasattr(mod, "_current_storage_instance"):
                mod._current_storage_instance = None
            if hasattr(mod, "_current_attachment_path"):
                mod._current_attachment_path = None
            if hasattr(mod, "_current_attachment_instance"):
                mod._current_attachment_instance = None
            if hasattr(mod, "get_note_storage"):
                try:
                    storage = mod.get_note_storage()
                    storage._sync_index_with_retry(clean=True, optimize=True)
                except Exception as e:
                    print(f"[SystemConfig] Error reloading note_storage on {mod_name}: {e}")

def check_admin(request: Request):
    auth_header = request.headers.get("Authorization", "").replace("Bearer ", "").strip()
    if not security.is_admin_token(auth_header):
        raise HTTPException(
            status_code=403,
            detail="无权限操作：仅管理员可切换数据库目录或浏览系统路径。"
        )

class SetStoragePathRequest(BaseModel):
    new_path: str
    create_if_missing: bool = True
    copy_existing_notes: bool = False

class SiteConfigPayload(BaseModel):
    site_title: str
    site_subtitle: Optional[str] = "SLAM & KNOWLEDGE LAB"

@system_router.get("/site-config")
def get_site_config():
    """Get public website title and branding configuration."""
    cfg = load_server_config()
    return {
        "site_title": cfg.get("site_title", "siwannote"),
        "site_subtitle": cfg.get("site_subtitle", "SLAM & KNOWLEDGE LAB")
    }

@system_router.post("/site-config")
def update_site_config(payload: SiteConfigPayload, request: Request):
    """Update website title and branding (Admin Only)."""
    check_admin(request)
    title = payload.site_title.strip()
    if not title:
        raise HTTPException(status_code=400, detail="网站名称不能为空")
    
    cfg = load_server_config()
    cfg["site_title"] = title
    cfg["site_subtitle"] = (payload.site_subtitle or "").strip()
    save_server_config(cfg)
    return {
        "status": "success",
        "message": "网页名称与副标题已成功更新",
        "site_title": cfg["site_title"],
        "site_subtitle": cfg["site_subtitle"]
    }

@system_router.get("/storage")
def get_storage_info(request: Request):
    """Get current active storage directory details."""
    check_admin(request)
    current = get_current_storage_path()
    exists = os.path.exists(current)
    notes_count = get_notes_count_in_dir(current) if exists else 0

    return {
        "current_path": current,
        "exists": exists,
        "default_path": DEFAULT_DATA_DIR,
        "notes_count": notes_count,
        "app_root": APP_ROOT
    }

@system_router.post("/storage")
def set_storage_info(payload: SetStoragePathRequest, request: Request):
    """Set new storage directory on the device, optionally migrating/copying files."""
    check_admin(request)
    raw_path = payload.new_path.strip()
    if not raw_path:
        raise HTTPException(status_code=400, detail="文件夹路径不能为空")

    target_path = os.path.abspath(os.path.expanduser(raw_path))

    if not os.path.exists(target_path):
        if payload.create_if_missing:
            try:
                os.makedirs(target_path, exist_ok=True)
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"无法创建目标文件夹: {e}")
        else:
            raise HTTPException(status_code=404, detail="目标文件夹不存在")

    if not os.path.isdir(target_path):
        raise HTTPException(status_code=400, detail="指定的路径不是有效文件夹")

    # Check write permission
    if not os.access(target_path, os.W_OK):
        raise HTTPException(status_code=403, detail="对该文件夹没有写入权限，请检查系统目录权限")

    old_path = get_current_storage_path()

    # Optional sync / copy from current directory
    sync_stats = None
    if payload.copy_existing_notes and old_path and os.path.isdir(old_path) and old_path != target_path:
        sync_stats = sync_storage_contents(old_path, target_path)

    # Save to server config
    save_storage_path(target_path)
    os.environ["SIWAN_PATH"] = target_path
    os.environ["FLATNOTES_PATH"] = target_path

    # Reload runtime storage
    try:
        update_runtime_storage(target_path)
        notes_count = get_notes_count_in_dir(target_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"加载新数据库失败: {e}")

    # Build response message
    msg = f"数据库目录已成功切换至: {target_path} (共 {notes_count} 篇文档)"
    if sync_stats and sync_stats.get("copied_notes", 0) > 0:
        msg += f"，并已自动同步迁移 {sync_stats['copied_notes']} 篇笔记及附件"

    return {
        "status": "success",
        "message": msg,
        "current_path": target_path,
        "notes_count": notes_count,
        "sync_stats": sync_stats
    }

@system_router.post("/sync")
def sync_storage_index(request: Request):
    """Force resync and rebuild the index for the active database directory."""
    check_admin(request)
    current_path = get_current_storage_path()

    # Force rebuild index
    import sys
    for mod_name in ["main", "server.main"]:
        if mod_name in sys.modules:
            mod = sys.modules[mod_name]
            if hasattr(mod, "_current_storage_path"):
                mod._current_storage_path = None
            if hasattr(mod, "_current_storage_instance"):
                mod._current_storage_instance = None
            if hasattr(mod, "get_note_storage"):
                try:
                    storage = mod.get_note_storage()
                    storage._sync_index_with_retry(clean=True, optimize=True)
                except Exception as e:
                    print(f"[SystemConfig] Error syncing index on {mod_name}: {e}")

    notes_count = get_notes_count_in_dir(current_path)

    return {
        "status": "success",
        "message": f"数据库索引已全面重新同步与重建！当前共检索到 {notes_count} 篇文档。",
        "current_path": current_path,
        "notes_count": notes_count
    }

@system_router.get("/browse")
def browse_directory(request: Request, path: Optional[str] = None):
    """Browse directories on the device/server."""
    check_admin(request)
    
    if not path or not path.strip():
        curr = get_current_storage_path()
        target = os.path.dirname(curr) if os.path.exists(curr) else os.path.expanduser("~")
    else:
        target = os.path.abspath(os.path.expanduser(path.strip()))

    if not os.path.exists(target) or not os.path.isdir(target):
        target = os.path.expanduser("~")

    parent = os.path.dirname(target)
    subdirs = []
    
    try:
        entries = sorted(os.listdir(target))
        for item in entries:
            # Skip hidden files
            if item.startswith("."):
                continue
            item_path = os.path.join(target, item)
            try:
                if os.path.isdir(item_path):
                    subdirs.append({
                        "name": item,
                        "path": item_path,
                        "writable": os.access(item_path, os.W_OK)
                    })
            except (PermissionError, OSError):
                continue
    except PermissionError:
        raise HTTPException(status_code=403, detail="无权读取该系统目录")

    return {
        "current": target,
        "parent": parent if parent != target else None,
        "subdirs": subdirs,
        "writable": os.access(target, os.W_OK)
    }
