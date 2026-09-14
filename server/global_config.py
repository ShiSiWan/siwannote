import sys
from enum import Enum

from helpers import CustomBaseModel, get_env
from logger import logger


class GlobalConfig:
    def __init__(self) -> None:
        logger.debug("Loading global config...")
        self.auth_type: AuthType = self._load_auth_type()
        self.quick_access_hide: bool = self._quick_access_hide()
        self.quick_access_title: str = self._quick_access_title()
        self.quick_access_term: str = self._quick_access_term()
        self.quick_access_sort: str = self._quick_access_sort()
        self.quick_access_limit: int = self._quick_access_limit()
        self.path_prefix: str = self._load_path_prefix()
        self.storage_path: str = None

    def load_auth(self):
        if self.auth_type in (AuthType.NONE, AuthType.READ_ONLY):
            return None
        elif self.auth_type in (AuthType.PASSWORD, AuthType.TOTP):
            from auth.local import LocalAuth

            return LocalAuth()

    def load_note_storage(self, storage_path: str = None):
        from notes.file_system import FileSystemNotes

        path = storage_path or self.storage_path
        return FileSystemNotes(path)

    def load_attachment_storage(self, storage_path: str = None):
        from attachments.file_system import FileSystemAttachments

        path = storage_path or self.storage_path
        return FileSystemAttachments(path)

    def _load_auth_type(self):
        key = "SIWAN_AUTH_TYPE"
        auth_type = get_env(
            key, fallback_keys=["FLATNOTES_AUTH_TYPE"], mandatory=False, default=AuthType.NONE.value
        )
        try:
            auth_type = AuthType(auth_type.lower())
        except ValueError:
            logger.error(
                f"Invalid value '{auth_type}' for {key}. "
                + "Must be one of: "
                + ", ".join([auth_type.value for auth_type in AuthType])
                + "."
            )
            sys.exit(1)
        return auth_type

    def _quick_access_hide(self):
        key = "SIWAN_QUICK_ACCESS_HIDE"
        value = get_env(key, fallback_keys=["FLATNOTES_QUICK_ACCESS_HIDE"], mandatory=False, default=False, cast_bool=True)
        return value

    def _quick_access_title(self):
        key = "SIWAN_QUICK_ACCESS_TITLE"
        return get_env(key, fallback_keys=["FLATNOTES_QUICK_ACCESS_TITLE"], mandatory=False, default="全部文档 (按名称排序)")

    def _quick_access_term(self):
        key = "SIWAN_QUICK_ACCESS_TERM"
        return get_env(key, fallback_keys=["FLATNOTES_QUICK_ACCESS_TERM"], mandatory=False, default="*")

    def _quick_access_sort(self):
        key = "SIWAN_QUICK_ACCESS_SORT"
        value = get_env(key, fallback_keys=["FLATNOTES_QUICK_ACCESS_SORT"], mandatory=False, default="title")
        valid_values = ["score", "title", "lastModified"]
        if value not in valid_values:
            logger.error(
                f"Invalid value '{value}' for {key}. "
                + "Must be one of: "
                + ", ".join(valid_values)
            )
            sys.exit(1)
        return value

    def _quick_access_limit(self):
        key = "SIWAN_QUICK_ACCESS_LIMIT"
        return get_env(key, fallback_keys=["FLATNOTES_QUICK_ACCESS_LIMIT"], mandatory=False, default=100, cast_int=True)

    def _load_path_prefix(self):
        key = "SIWAN_PATH_PREFIX"
        value = get_env(key, fallback_keys=["FLATNOTES_PATH_PREFIX"], mandatory=False, default="")
        if value and (not value.startswith("/") or value.endswith("/")):
            logger.error(
                f"Invalid value '{value}' for {key}. "
                + "Must start with '/' and not end with '/'."
            )
            sys.exit(1)
        return value


class AuthType(str, Enum):
    NONE = "none"
    READ_ONLY = "read_only"
    PASSWORD = "password"
    TOTP = "totp"


class GlobalConfigResponseModel(CustomBaseModel):
    auth_type: AuthType
    quick_access_hide: bool
    quick_access_title: str
    quick_access_term: str
    quick_access_sort: str
    quick_access_limit: int
