import json
import os
from typing import List, Literal, Optional

from fastapi import APIRouter, Depends, FastAPI, HTTPException, Request, Response, UploadFile
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

import api_messages
from attachments.base import BaseAttachments
from attachments.models import AttachmentCreateResponse
from auth.base import BaseAuth
from auth.models import Login, Token
from global_config import AuthType, GlobalConfig, GlobalConfigResponseModel
from helpers import replace_base_href
from notes.base import BaseNotes
from notes.models import Note, NoteCreate, NoteUpdate, SearchResult
import ai
import security
import system_config

# If a custom database folder was configured, apply it before loading storage
custom_storage = system_config.get_current_storage_path()
if custom_storage and os.path.isdir(custom_storage):
    os.environ["SIWAN_PATH"] = custom_storage
    os.environ["FLATNOTES_PATH"] = custom_storage
    security.DATA_DIR = custom_storage
    security.PERM_FILE = os.path.join(custom_storage, ".siwan_permissions.json")
    security.COMMENTS_FILE = os.path.join(custom_storage, ".siwan_comments.json")
    security.IP_STATS_FILE = os.path.join(custom_storage, ".siwan_ip_stats.json")

global_config = GlobalConfig()
global_config.storage_path = custom_storage
auth: BaseAuth = global_config.load_auth()
# Dynamic Storage Resolvers
_current_storage_instance: Optional[BaseNotes] = None
_current_storage_path: Optional[str] = None
_current_attachment_instance: Optional[BaseAttachments] = None
_current_attachment_path: Optional[str] = None

def get_note_storage() -> BaseNotes:
    global _current_storage_instance, _current_storage_path
    active_path = system_config.get_current_storage_path()
    if _current_storage_instance is None or _current_storage_path != active_path:
        _current_storage_path = active_path
        os.environ["SIWAN_PATH"] = active_path
        os.environ["FLATNOTES_PATH"] = active_path
        global_config.storage_path = active_path
        from notes.file_system import FileSystemNotes
        _current_storage_instance = FileSystemNotes(active_path)
        _current_storage_instance._sync_index_with_retry(clean=True, optimize=True)
    return _current_storage_instance

def get_attachment_storage() -> BaseAttachments:
    global _current_attachment_instance, _current_attachment_path
    active_path = system_config.get_current_storage_path()
    if _current_attachment_instance is None or _current_attachment_path != active_path:
        _current_attachment_path = active_path
        from attachments.file_system import FileSystemAttachments
        _current_attachment_instance = FileSystemAttachments(active_path)
    return _current_attachment_instance

class NoteStorageProxy:
    def __getattr__(self, name):
        return getattr(get_note_storage(), name)

note_storage = NoteStorageProxy()

class AttachmentStorageProxy:
    def __getattr__(self, name):
        return getattr(get_attachment_storage(), name)

attachment_storage = AttachmentStorageProxy()

auth_deps = [Depends(auth.authenticate)] if auth else []
router = APIRouter()
app = FastAPI(
    docs_url=global_config.path_prefix + "/docs",
    openapi_url=global_config.path_prefix + "/openapi.json",
)
replace_base_href("client/dist/index.html", global_config.path_prefix)

# IP Tracking & Blacklist Middleware
@app.middleware("http")
async def ip_security_middleware(request: Request, call_next):
    try:
        security.check_ip_and_track(request)
    except HTTPException as e:
        return Response(
            content=json.dumps({"detail": e.detail}),
            status_code=e.status_code,
            media_type="application/json"
        )
    return await call_next(request)


# region UI
@router.get("/", include_in_schema=False)
@router.get("/login", include_in_schema=False)
@router.get("/search", include_in_schema=False)
@router.get("/new", include_in_schema=False)
@router.get("/note/{title:path}", include_in_schema=False)
def root(title: str = ""):
    with open("client/dist/index.html", "r", encoding="utf-8") as f:
        html = f.read()
    return HTMLResponse(content=html)


# endregion


# region Auth
if global_config.auth_type not in [AuthType.NONE, AuthType.READ_ONLY]:

    @router.post("/api/token", response_model=Token)
    def token(data: Login):
        try:
            return auth.login(data)
        except ValueError:
            raise HTTPException(
                status_code=401, detail=api_messages.login_failed
            )


@router.get("/api/auth-check", dependencies=auth_deps)
def auth_check() -> str:
    return "OK"


# endregion


# region Notes
# Get Note
@router.get(
    "/api/notes/{title:path}",
    dependencies=auth_deps,
    response_model=Note,
)
def get_note(title: str, request: Request):
    """Get a specific note from the active database."""
    auth_header = request.headers.get("Authorization", "").replace("Bearer ", "").strip()
    is_admin = security.is_admin_token(auth_header)
    if not is_admin:
        perms = security.get_permissions()
        if not perms.get("all_public", True):
            public_list = perms.get("public_notes", [])
            if title not in public_list:
                raise HTTPException(
                    status_code=403,
                    detail="该文档未对外开放，仅管理员登录后可见。"
                )

    try:
        return get_note_storage().get(title)
    except ValueError:
        raise HTTPException(
            status_code=400, detail=api_messages.invalid_note_title
        )
    except FileNotFoundError:
        raise HTTPException(404, api_messages.note_not_found)


# Create Note (Admin Only)
@router.post(
    "/api/notes",
    dependencies=auth_deps,
    response_model=Note,
)
def post_note(note: NoteCreate, request: Request):
    """Create a new note."""
    auth_header = request.headers.get("Authorization", "").replace("Bearer ", "").strip()
    if not security.is_admin_token(auth_header):
        raise HTTPException(status_code=403, detail="访客模式无权限创建笔记，请登录管理员账号。")

    try:
        created = get_note_storage().create(note)
        perms = security.get_permissions()
        if perms.get("public_notes") is not None and note.title not in perms["public_notes"]:
            perms["public_notes"].append(note.title)
            security.save_permissions(perms)
        return created
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=api_messages.invalid_note_title,
        )
    except FileExistsError:
        raise HTTPException(
            status_code=409, detail=api_messages.note_exists
        )


# Update Note (Admin Only)
@router.patch(
    "/api/notes/{title:path}",
    dependencies=auth_deps,
    response_model=Note,
)
def patch_note(title: str, data: NoteUpdate, request: Request):
    auth_header = request.headers.get("Authorization", "").replace("Bearer ", "").strip()
    if not security.is_admin_token(auth_header):
        raise HTTPException(status_code=403, detail="访客模式无权限修改笔记，请登录管理员账号。")

    try:
        updated = get_note_storage().update(title, data)
        if data.new_title and data.new_title != title:
            perms = security.get_permissions()
            pub_list = perms.get("public_notes")
            if pub_list is not None and title in pub_list:
                pub_list.remove(title)
                pub_list.append(data.new_title)
                perms["public_notes"] = pub_list
                security.save_permissions(perms)
        return updated
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=api_messages.invalid_note_title,
        )
    except FileExistsError:
        raise HTTPException(
            status_code=409, detail=api_messages.note_exists
        )
    except FileNotFoundError:
        raise HTTPException(404, api_messages.note_not_found)


# Delete Note (Admin Only)
@router.delete(
    "/api/notes/{title:path}",
    dependencies=auth_deps,
    response_model=None,
)
def delete_note(title: str, request: Request):
    auth_header = request.headers.get("Authorization", "").replace("Bearer ", "").strip()
    if not security.is_admin_token(auth_header):
        raise HTTPException(status_code=403, detail="访客模式无权限删除笔记，请登录管理员账号。")

    try:
        get_note_storage().delete(title)
        perms = security.get_permissions()
        pub_list = perms.get("public_notes")
        if pub_list is not None and title in pub_list:
            pub_list.remove(title)
            perms["public_notes"] = pub_list
            security.save_permissions(perms)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=api_messages.invalid_note_title,
        )
    except FileNotFoundError:
        raise HTTPException(404, api_messages.note_not_found)


# endregion


# region Search
@router.get(
    "/api/search",
    dependencies=auth_deps,
    response_model=List[SearchResult],
)
def search(
    request: Request,
    term: str,
    sort: Literal["score", "title", "lastModified", "last_modified"] = "score",
    order: Literal["asc", "desc"] = "desc",
    limit: int = None,
):
    """Perform a full text search on notes."""
    if sort == "lastModified":
        sort = "last_modified"
    results = get_note_storage().search(term, sort=sort, order=order, limit=limit)

    auth_header = request.headers.get("Authorization", "").replace("Bearer ", "").strip()
    is_admin = security.is_admin_token(auth_header)
    if not is_admin:
        perms = security.get_permissions()
        if not perms.get("all_public", True):
            public_list = perms.get("public_notes", [])
            public_set = set(public_list)
            results = [r for r in results if r.title in public_set]

    return results


@router.get(
    "/api/tags",
    dependencies=auth_deps,
    response_model=List[str],
)
def get_tags():
    return get_note_storage().get_tags()


# endregion


# region Config
@router.get("/api/config", response_model=GlobalConfigResponseModel)
def get_config():
    return GlobalConfigResponseModel(
        auth_type=global_config.auth_type,
        quick_access_hide=global_config.quick_access_hide,
        quick_access_title=global_config.quick_access_title,
        quick_access_term=global_config.quick_access_term,
        quick_access_sort=global_config.quick_access_sort,
        quick_access_limit=global_config.quick_access_limit,
    )


# endregion


# region Attachments
@router.get(
    "/api/attachments/{filename:path}",
    dependencies=auth_deps,
    response_class=HTMLResponse,
)
def get_attachment(filename: str):
    try:
        return get_attachment_storage().get(filename)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=api_messages.invalid_attachment_filename,
        )
    except FileNotFoundError:
        raise HTTPException(404, api_messages.attachment_not_found)


@router.post(
    "/api/attachments",
    dependencies=auth_deps,
    response_model=AttachmentCreateResponse,
)
def post_attachment(file: UploadFile):
    try:
        return get_attachment_storage().create(file)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=api_messages.invalid_attachment_filename,
        )
    except FileExistsError:
        raise HTTPException(409, api_messages.attachment_exists)


# endregion


# region Favicon
@router.get("/favicon.ico", include_in_schema=False)
def favicon():
    for p in [
        "client/dist/favicon.ico",
        "client/public/favicon.ico",
        "client/assets/favicon.ico",
    ]:
        if os.path.exists(p):
            return FileResponse(p, media_type="image/x-icon")
    raise HTTPException(status_code=404)


# endregion


# region Healthcheck
@router.get("/health")
def healthcheck() -> str:
    return "OK"


# endregion

app.include_router(router, prefix=global_config.path_prefix)
app.include_router(ai.router, prefix=global_config.path_prefix)
app.include_router(security.security_router, prefix=global_config.path_prefix)
app.include_router(system_config.system_router, prefix=global_config.path_prefix)
app.mount(
    global_config.path_prefix,
    StaticFiles(directory="client/dist"),
    name="dist",
)
