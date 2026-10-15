import json
import os
import re
import secrets
import sys

from pydantic import BaseModel

from logger import logger


def camel_case(snake_case_str: str) -> str:
    """Return the declared snake_case string in camelCase."""
    parts = [part for part in snake_case_str.split("_") if part != ""]
    return parts[0] + "".join(part.title() for part in parts[1:])


def is_valid_filename(value):
    """Validate note title / filename. Strictly rejects absolute paths, null bytes, traversal, and invalid chars."""
    if not value or not isinstance(value, str):
        raise ValueError("title/filename cannot be empty")
    clean = value.strip()
    if not clean:
        raise ValueError("title/filename cannot be empty")
    if "\x00" in clean:
        raise ValueError("title/filename cannot contain null bytes")
    if os.path.isabs(clean) or clean.startswith("/") or clean.startswith("\\"):
        raise ValueError("title/filename cannot be an absolute path or start with '/' or '\\'")
    if ".." in clean.replace("\\", "/").split("/"):
        raise ValueError("title/filename cannot contain '..' path traversal")
    if ".." in clean:
        raise ValueError("title/filename cannot contain '..'")
    invalid_chars = r'<>:"|?*'
    if any(invalid_char in clean for invalid_char in invalid_chars):
        raise ValueError(
            "title/filename cannot include any of the following characters: "
            + invalid_chars
        )
    return clean


def strip_whitespace(value):
    """Return the declared string with leading and trailing whitespace
    removed."""
    return value.strip()


def atomic_save_json(filepath: str, data, mode: int = None) -> None:
    """Atomically write JSON data to file to prevent corruption on crash or concurrency."""
    dir_name = os.path.dirname(filepath)
    if dir_name:
        os.makedirs(dir_name, exist_ok=True)
    temp_file = f"{filepath}.tmp.{os.getpid()}.{secrets.token_hex(4)}"
    try:
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.flush()
            os.fsync(f.fileno())
        if mode is not None:
            try:
                os.chmod(temp_file, mode)
            except Exception:
                pass
        os.replace(temp_file, filepath)
    except Exception as e:
        if os.path.exists(temp_file):
            try:
                os.remove(temp_file)
            except Exception:
                pass
        raise e


def get_env(
    key, fallback_keys=None, mandatory=False, default=None, cast_int=False, cast_bool=False
):
    """Get an environment variable. Supports checking fallback keys."""
    value = os.environ.get(key)
    if not value and fallback_keys:
        if isinstance(fallback_keys, str):
            fallback_keys = [fallback_keys]
        for fk in fallback_keys:
            v = os.environ.get(fk)
            if v:
                value = v
                break
    if mandatory and not value:
        logger.error(f"Environment variable {key} must be set.")
        sys.exit(1)
    if not mandatory and not value:
        return default
    if cast_int:
        try:
            value = int(value)
        except (TypeError, ValueError):
            logger.error(f"Invalid value '{value}' for {key}.")
            sys.exit(1)
    if cast_bool:
        if isinstance(value, bool):
            return value
        value_str = str(value).lower()
        if value_str == "true":
            value = True
        elif value_str == "false":
            value = False
        else:
            logger.error(f"Invalid value '{value}' for {key}.")
            sys.exit(1)
    return value


def replace_base_href(html_file, path_prefix):
    """Replace the href value for the base element in an HTML file."""
    base_path = path_prefix + "/"
    logger.info(
        f"Replacing href value for base element in '{html_file}' "
        + f"with '{base_path}'."
    )
    with open(html_file, "r", encoding="utf-8") as f:
        html = f.read()
    pattern = r'(<base\s+href=")[^"]*(")'
    replacement = r"\1" + base_path + r"\2"
    updated_html = re.sub(pattern, replacement, html, flags=re.IGNORECASE)
    with open(html_file, "w", encoding="utf-8") as f:
        f.write(updated_html)


class CustomBaseModel(BaseModel):
    class Config:
        alias_generator = camel_case
        populate_by_name = True
        from_attributes = True
