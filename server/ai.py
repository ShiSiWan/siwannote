import json
import os
import re
import time
import secrets
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel
import httpx
from fastapi import APIRouter, Depends, HTTPException
try:
    import security
    verify_admin = security.verify_admin
except ImportError:
    from server import security
    verify_admin = security.verify_admin

router = APIRouter(prefix="/api/ai", tags=["ai"])

DEFAULT_SUMMARY_TEMPLATE = (
    "请严格按以下格式输出，内容紧凑、重点突出，包含：\n"
    "📌 核心主旨与背景（1~2 句话概括定位）\n\n"
    "⚙️ 核心技术架构与算法机制（提炼 2-3 条要点）\n\n"
    "📊 关键实验指标与对标结论（若文档包含实验实测数据，重点提炼）\n\n"
    "💡 关键价值与后续启发（1~2 条）"
)

# AI Configuration Data Model
class AiConfig(BaseModel):
    api_base: str = "https://api.openai.com/v1"
    api_key: str = ""
    model: str = "gpt-4o-mini"
    proxy_url: Optional[str] = ""
    auto_summarize: bool = True
    system_prompt: str = "你是一个严谨高效的科研与技术专家助手。请针对用户提供的学术文献、工程技术或学习笔记，生成结构化、专业精准的深度中文总结。"
    summary_template: str = DEFAULT_SUMMARY_TEMPLATE
    temperature: float = 0.3

class AiSummarizeRequest(BaseModel):
    title: str
    content: str
    custom_prompt: Optional[str] = None

class ChatMessage(BaseModel):
    role: str
    content: str

class AiChatRequest(BaseModel):
    doc_title: Optional[str] = ""
    doc_context: Optional[str] = ""
    messages: List[ChatMessage]

def get_ai_config_file() -> str:
    try:
        from server.system_config import get_current_storage_path
        storage = get_current_storage_path()
    except Exception:
        storage = os.environ.get("SIWAN_PATH", os.environ.get("FLATNOTES_PATH", "/data"))
    return os.path.join(storage, ".siwan_ai_config.json")

def load_ai_config() -> AiConfig:
    cfg_file = get_ai_config_file()
    if os.path.exists(cfg_file):
        try:
            with open(cfg_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                return AiConfig(**data)
        except Exception as e:
            print(f"[SiWan_notes AI] Failed to load config: {e}")
    return AiConfig()

def save_ai_config(config: AiConfig) -> None:
    cfg_file = get_ai_config_file()
    os.makedirs(os.path.dirname(cfg_file), exist_ok=True)
    with open(cfg_file, "w", encoding="utf-8") as f:
        json.dump(config.dict(), f, ensure_ascii=False, indent=2)

def get_http_client(cfg: AiConfig, timeout: float = 60.0) -> httpx.AsyncClient:
    proxy = (cfg.proxy_url or "").strip()
    if proxy and proxy.lower() not in ("none", "direct", "off", "false", "0"):
        # Normalize socks:// to socks5:// for httpx socksio
        if proxy.startswith("socks://"):
            proxy = "socks5://" + proxy[len("socks://"):]
        return httpx.AsyncClient(proxy=proxy, timeout=timeout, trust_env=False)
    else:
        return httpx.AsyncClient(timeout=timeout, trust_env=False)

def mask_key(key: str) -> str:
    if not key:
        return ""
    if len(key) > 8:
        return key[:4] + "*" * (len(key) - 8) + key[-4:]
    return "********"

@router.get("/config")
def get_config():
    cfg = load_ai_config()
    return {
        "api_base": cfg.api_base,
        "model": cfg.model,
        "proxy_url": cfg.proxy_url,
        "auto_summarize": cfg.auto_summarize,
        "system_prompt": cfg.system_prompt,
        "summary_template": cfg.summary_template or DEFAULT_SUMMARY_TEMPLATE,
        "temperature": cfg.temperature,
        "has_key": bool(cfg.api_key.strip()),
        "masked_key": mask_key(cfg.api_key)
    }

@router.post("/config", dependencies=[Depends(verify_admin)])
def update_config(data: Dict[str, Any]):
    cfg = load_ai_config()
    # Support ccSwitch / OpenAI / custom format conversions
    api_base = data.get("api_base") or data.get("baseURL") or data.get("baseUrl")
    if api_base:
        cfg.api_base = str(api_base).strip().rstrip("/")
    
    api_key = data.get("api_key") or data.get("apiKey")
    if api_key is not None:
        new_key = str(api_key).strip()
        if new_key and not new_key.startswith("****") and "*" not in new_key:
            cfg.api_key = new_key
            
    model = data.get("model")
    if not model and "models" in data:
        if isinstance(data["models"], dict) and data["models"]:
            model = list(data["models"].keys())[0]
        elif isinstance(data["models"], list) and data["models"]:
            model = data["models"][0]
    if model:
        cfg.model = str(model).strip()
        
    if "proxy_url" in data:
        cfg.proxy_url = str(data["proxy_url"]).strip() if data["proxy_url"] else ""
        
    if "auto_summarize" in data:
        cfg.auto_summarize = bool(data["auto_summarize"])
        
    if "system_prompt" in data and data["system_prompt"]:
        cfg.system_prompt = str(data["system_prompt"]).strip()

    if "summary_template" in data and data["summary_template"]:
        cfg.summary_template = str(data["summary_template"]).strip()
        
    if "temperature" in data:
        try:
            cfg.temperature = float(data["temperature"])
        except (ValueError, TypeError):
            pass

    save_ai_config(cfg)
    return {"status": "success", "message": "AI configuration saved successfully"}

@router.get("/raw-json")
def get_raw_json():
    cfg = load_ai_config()
    data = cfg.dict()
    # Return raw json but provide masked key if not specifically requested
    masked_data = dict(data)
    if masked_data.get("api_key"):
        masked_data["api_key"] = mask_key(masked_data["api_key"])
    return {
        "raw_json": json.dumps(masked_data, ensure_ascii=False, indent=2),
        "has_key": bool(cfg.api_key.strip())
    }

@router.post("/raw-json")
def update_raw_json(payload: Dict[str, Any]):
    json_str = payload.get("json_str", "")
    try:
        data = json.loads(json_str) if isinstance(json_str, str) else json_str
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"JSON 解析错误: {str(e)}")

    # Support parsing ccSwitch provider config object
    if "options" in data and isinstance(data["options"], dict):
        opts = data["options"]
        if "baseURL" in opts:
            data["api_base"] = opts["baseURL"]
        if "apiKey" in opts:
            data["api_key"] = opts["apiKey"]

    return update_config(data)

def extract_reply(result: dict) -> str:
    choices = result.get("choices", [])
    if not choices:
        return ""
    msg = choices[0].get("message", {})
    content = msg.get("content")
    if not content:
        content = msg.get("reasoning_content") or ""
    return str(content).strip()

@router.post("/test")
async def test_ai_connection():
    cfg = load_ai_config()
    if not cfg.api_key.strip():
        raise HTTPException(status_code=400, detail="未配置 API Key，请先填写密钥。")

    url = f"{cfg.api_base}/chat/completions"
    headers = {
        "Authorization": f"Bearer {cfg.api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": cfg.model,
        "messages": [
            {"role": "user", "content": "Hello! Reply with 'OK' only."}
        ],
        "max_tokens": 10
    }

    try:
        async with get_http_client(cfg, timeout=15.0) as client:
            resp = await client.post(url, headers=headers, json=payload)
            if resp.status_code == 200:
                res_data = resp.json()
                reply = extract_reply(res_data)
                return {"status": "success", "message": f"连接成功！模型响应: {reply or 'OK'}"}
            else:
                raise HTTPException(
                    status_code=resp.status_code,
                    detail=f"API 响应错误 ({resp.status_code}): {resp.text[:200]}"
                )
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="请求超时（15s），请检查网络或代理地址。")
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f"网络连接失败: {str(e)}")

@router.post("/summarize")
async def summarize_doc(req: AiSummarizeRequest):
    cfg = load_ai_config()
    if not cfg.api_key.strip():
        raise HTTPException(
            status_code=400,
            detail="AI API Key 未配置，请在右上角「设置」中心打开 AI 配置填入您的密钥。"
        )

    # Prepare summary prompt
    doc_text = req.content[:30000]
    template = (req.custom_prompt or cfg.summary_template or DEFAULT_SUMMARY_TEMPLATE).strip()
    summary_prompt = (
        f"【任务】：请为以下文档《{req.title}》生成专业结构化的深度中文摘要总结。\n\n"
        f"【文档全文内容】：\n"
        f"{doc_text}\n\n"
        f"【输出规范与结构要求】：\n"
        f"{template}\n"
    )

    url = f"{cfg.api_base}/chat/completions"
    headers = {
        "Authorization": f"Bearer {cfg.api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": cfg.model,
        "messages": [
            {"role": "system", "content": cfg.system_prompt},
            {"role": "user", "content": summary_prompt}
        ],
        "temperature": cfg.temperature
    }

    try:
        async with get_http_client(cfg, timeout=75.0) as client:
            resp = await client.post(url, headers=headers, json=payload)
            if resp.status_code != 200:
                raise HTTPException(
                    status_code=resp.status_code,
                    detail=f"AI 服务端调用返回错误 ({resp.status_code}): {resp.text}"
                )
            result = resp.json()
            reply = extract_reply(result)
            return {
                "title": req.title,
                "summary": reply,
                "model": cfg.model
            }
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="AI 服务请求超时，请检查网络或更换更轻量的模型。")
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f"AI 总结生成失败: {str(e)}")

@router.post("/chat")
async def chat_with_ai(req: AiChatRequest):
    cfg = load_ai_config()
    if not cfg.api_key.strip():
        raise HTTPException(
            status_code=400,
            detail="AI API Key 未配置，请在右上角「设置」中心填入您的密钥。"
        )

    system_content = cfg.system_prompt
    if req.doc_title and req.doc_context:
        system_content += (
            f"\n\n用户当前正在查看/编辑笔记《{req.doc_title}》。"
            f"以下为该文档全文上下文，请优先结合该文档内容准确回答用户问题：\n"
            f"--- 文档开始 ---\n{req.doc_context[:25000]}\n--- 文档结束 ---"
        )

    messages = [{"role": "system", "content": system_content}]
    for msg in req.messages:
        messages.append({"role": msg.role, "content": msg.content})

    url = f"{cfg.api_base}/chat/completions"
    headers = {
        "Authorization": f"Bearer {cfg.api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": cfg.model,
        "messages": messages,
        "temperature": cfg.temperature
    }

    try:
        async with get_http_client(cfg, timeout=75.0) as client:
            resp = await client.post(url, headers=headers, json=payload)
            if resp.status_code != 200:
                raise HTTPException(
                    status_code=resp.status_code,
                    detail=f"AI 服务端调用返回错误 ({resp.status_code}): {resp.text}"
                )
            result = resp.json()
            reply = extract_reply(result)
            return {"reply": reply, "model": cfg.model}
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f"AI 对话请求失败: {str(e)}")

class AiReviewRequest(BaseModel):
    title: str
    content: str

class AiScanRequest(BaseModel):
    title: str
    content: str
    custom_prompt: Optional[str] = None

def get_notes_storage():
    try:
        import main
        return main.get_note_storage()
    except Exception:
        from notes.file_system import FileSystemNotes
        return FileSystemNotes()

AI_UNIFIED_SCAN_PROMPT = """你是一个严谨客观的科研与技术专家第二读者助手（AI Reviewer & Summarizer）。
请针对用户提供的文档《{title}》【同时完成以下两项任务】，并严格按指定的 JSON 结构返回：

【任务一：文档结构化深度总结】
提炼核心内容，格式紧凑、重点突出，使用 markdown 包含以下维度：
📌 核心主旨与背景（1~2 句话概括定位）
⚙️ 核心技术架构与算法机制（提炼 2-3 条要点）
📊 关键实验指标与对标结论（若文档包含实验实测数据，重点提炼）
💡 关键价值与后续启发（1~2 条）

【任务二：第二读者批注草稿审查】
审阅待审查正文，找出具体存在的问题，并提出简短中肯的修改建议。
【审查类型严格限定为以下 5 种之一，严禁使用其他类型】：
1. 事实存疑
2. 逻辑跳跃
3. 建议补充
4. 术语不一致
5. 表达冗余

批注审查要求：
1. 原文连续片段（quote）必须一字不差地在正文中真实存在（长度 5~40 字），严禁凭空捏造！
2. 简要说明问题和修改建议，最终拼接为“类型：问题；建议：...”，总字数严格不超过 40 个字！
3. 最多提出 5 条批注草稿；若文档无明显问题，返回空数组 []。

【输出规范】：
请仅输出合法的 JSON 对象，严禁包含任何前缀、解释、说明文字或 markdown 代码块标记。
JSON 格式严格定义如下：
{{
  "summary": "这里是完整的 Markdown 结构化摘要总结",
  "annotations": [
    {{
      "quote": "正文中真实存在的连续片段",
      "type": "事实存疑|逻辑跳跃|建议补充|术语不一致|表达冗余",
      "problem": "具体问题简述（10字以内）",
      "suggestion": "具体修改建议（15字以内）"
    }}
  ]
}}
"""

async def execute_unified_scan(title: str, content: str, custom_prompt: Optional[str] = None) -> Dict[str, Any]:
    cfg = load_ai_config()
    existing_annotations = security.get_note_annotations(title)
    now_iso = datetime.now().astimezone().isoformat(timespec="seconds")

    if not cfg.api_key.strip():
        return {
            "status": "skipped",
            "message": "AI API Key 未配置，跳过自动扫描",
            "title": title,
            "summary": "",
            "annotations": existing_annotations,
            "new_annotations_count": 0,
            "model": cfg.model,
            "generatedAt": now_iso
        }

    content_snippet = content[:25000]
    prompt = AI_UNIFIED_SCAN_PROMPT.format(title=title) + f"\n\n【待审查与总结的文档全文内容】：\n{content_snippet}"

    url = f"{cfg.api_base}/chat/completions"
    headers = {
        "Authorization": f"Bearer {cfg.api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": cfg.model,
        "messages": [
            {"role": "system", "content": "你是一个严格返回合法 JSON 对象的分析引擎，不包含任何外部 markdown 代码块标记。"},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.2
    }

    try:
        async with get_http_client(cfg, timeout=75.0) as client:
            resp = await client.post(url, headers=headers, json=payload)
            if resp.status_code != 200:
                return {
                    "status": "error",
                    "message": f"AI 服务响应错误 ({resp.status_code}): {resp.text[:200]}",
                    "title": title,
                    "summary": "",
                    "annotations": existing_annotations,
                    "new_annotations_count": 0,
                    "model": cfg.model,
                    "generatedAt": now_iso
                }
            result = resp.json()
            choices = result.get("choices", [])
            msg = choices[0].get("message", {}) if choices else {}
            content_str = str(msg.get("content") or "").strip()
            reasoning_str = str(msg.get("reasoning_content") or "").strip()

            # Check if reasoning is embedded in <think>...</think> within content
            think_match = re.search(r"<think>([\s\S]*?)</think>", content_str, flags=re.IGNORECASE)
            if think_match:
                if not reasoning_str:
                    reasoning_str = think_match.group(1).strip()
                clean_json = re.sub(r"<think>[\s\S]*?</think>", "", content_str, flags=re.IGNORECASE).strip()
            else:
                clean_json = content_str

            code_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", clean_json)
            if code_match:
                clean_json = code_match.group(1).strip()

            data = {}
            try:
                data = json.loads(clean_json)
            except Exception:
                m = re.search(r"\{[\s\S]*\}", clean_json)
                if m:
                    try:
                        data = json.loads(m.group(0))
                    except Exception as err:
                        print(f"[SiWan_notes AI JSON fallback parse error]: {err}\nSnippet: {clean_json[:300]}")
                else:
                    print(f"[SiWan_notes AI No JSON block found]: {clean_json[:300]}")
                    if clean_json:
                        data = {"summary": clean_json, "annotations": []}

            summary = str(data.get("summary", "")).strip()
            if not summary and clean_json and "summary" not in data:
                summary = clean_json

            # Preserve thinking process for frontend thinking accordion UI
            if reasoning_str:
                if "<think>" not in summary:
                    summary = f"<think>\n{reasoning_str}\n</think>\n\n{summary}"

            raw_annotations = data.get("annotations", [])
            if not isinstance(raw_annotations, list):
                raw_annotations = []

            ALLOWED_TYPES = {"事实存疑", "逻辑跳跃", "建议补充", "术语不一致", "表达冗余"}
            new_annotations = []
            existing_quotes = {a.get("quote", "").strip() for a in existing_annotations if a.get("quote")}

            for item in raw_annotations[:5]:
                if not isinstance(item, dict):
                    continue
                quote = str(item.get("quote", "")).strip()
                c_type = str(item.get("type", "")).strip()
                problem = str(item.get("problem", "")).strip()
                suggestion = str(item.get("suggestion", "")).strip()

                if not quote or quote not in content:
                    continue
                if quote in existing_quotes:
                    continue
                if c_type not in ALLOWED_TYPES:
                    c_type = "建议补充"

                # Standardized format: 类型：问题；建议：... (<= 40 chars)
                formatted_comment = f"{c_type}：{problem}；建议：{suggestion}"
                if len(formatted_comment) > 40:
                    formatted_comment = formatted_comment[:39] + "…"

                ann_id = f"ai_{int(time.time())}_{secrets.token_hex(3)}"
                ai_ann = {
                    "id": ann_id,
                    "quote": quote,
                    "comment": formatted_comment,
                    "author_type": "ai",
                    "comment_type": c_type,
                    "status": "proposed",
                    "createdAt": now_iso,
                    "updatedAt": now_iso,
                    "generatedAt": now_iso,
                    "model": cfg.model,
                    "created_at": now_iso
                }
                new_annotations.append(ai_ann)
                existing_quotes.add(quote)

            merged_annotations = list(existing_annotations)
            if new_annotations:
                merged_annotations.extend(new_annotations)
                security.save_note_annotations(title, merged_annotations)

            # Persist generated summary to disk
            try:
                security.save_note_summary(title, {
                    "title": title,
                    "summary": summary,
                    "thinking": reasoning_str,
                    "model": cfg.model,
                    "generatedAt": now_iso
                })
            except Exception as ex:
                print(f"[SiWan_notes AI] Save note summary error: {ex}")

            # Update reviewed timestamp in note YAML front matter
            try:
                get_notes_storage().update_reviewed(title, now_iso)
            except Exception as ex:
                print(f"[SiWan_notes AI] Note front matter reviewed update error: {ex}")

            return {
                "status": "success",
                "title": title,
                "summary": summary,
                "thinking": reasoning_str,
                "annotations": merged_annotations,
                "new_annotations_count": len(new_annotations),
                "model": cfg.model,
                "generatedAt": now_iso,
                "reviewed": now_iso
            }

    except Exception as e:
        print(f"[SiWan_notes AI Unified Scan Error]: {e}")
        return {
            "status": "error",
            "message": str(e),
            "title": title,
            "summary": "",
            "annotations": existing_annotations,
            "new_annotations_count": 0,
            "model": cfg.model,
            "generatedAt": now_iso
        }

@router.get("/summary/{title:path}")
def get_summary(title: str):
    """Get previously saved AI summary for a note from disk (0 API calls)."""
    data = security.get_note_summary(title)
    return {
        "title": title,
        "summary": data.get("summary", ""),
        "thinking": data.get("thinking", ""),
        "model": data.get("model", ""),
        "generatedAt": data.get("generatedAt", "")
    }

@router.post("/scan")
async def scan_doc(req: AiScanRequest):
    """Single-call background AI scan generating both structured summary and second-reader annotations."""
    return await execute_unified_scan(req.title, req.content, req.custom_prompt)

@router.post("/review")
async def review_doc(req: AiReviewRequest):
    """Review doc endpoint (leverages unified single-call execution)."""
    res = await execute_unified_scan(req.title, req.content)
    return {
        "status": res["status"],
        "message": res.get("message", ""),
        "annotations": res.get("annotations", []),
        "new_count": res.get("new_annotations_count", 0),
        "summary": res.get("summary", ""),
        "model": res.get("model", ""),
        "generatedAt": res.get("generatedAt", "")
    }
