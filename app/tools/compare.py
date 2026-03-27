from langchain.tools import tool

from app.services.compare_service import CompareService
from app.services.memory_service import MemoryService

def _bundle(summary, data, *, next_best_actions=None, should_continue=None, enough_for_finish=None):
    return {
        "ok": True,
        "summary": summary,
        "data": data,
        "success": True,
        "summary_text": summary,
        "payload": data,
        "next_best_actions": next_best_actions or [],
        "should_continue": should_continue,
        "enough_for_finish": enough_for_finish,
    }

def _text(value):
    return str(value or "").strip()

def _normalize_compare_value(value):
    text = _text(value)
    if not text:
        return text
    text = text.replace(" is stronger in ", "在")
    text = text.replace("performance", "性能")
    text = text.replace("camera", "拍照")
    text = text.replace("battery", "续航")
    text = text.replace("screen", "屏幕")
    text = text.replace("portability", "便携性")
    text = text.replace("price", "价格")
    if text.endswith("相当"):
        return text
    if "在性能" in text or "在拍照" in text or "在续航" in text or "在屏幕" in text or "在便携性" in text or "在价格" in text:
        if "方面更强" not in text and "价格更低" not in text and "价格更高" not in text:
            text = text + "方面更强"
    return text

def _normalize_compare_rows(rows):
    normalized = []
    for row in rows or []:
        item = dict(row or {})
        normalized.append({
            "left_product": item.get("left_product"),
            "right_product": item.get("right_product"),
            "性能": _normalize_compare_value(item.get("性能") or item.get("performance")),
            "拍照": _normalize_compare_value(item.get("拍照") or item.get("camera")),
            "续航": _normalize_compare_value(item.get("续航") or item.get("battery")),
            "屏幕": _normalize_compare_value(item.get("屏幕") or item.get("screen")),
            "便携性": _normalize_compare_value(item.get("便携性") or item.get("portability")),
            "价格": _normalize_compare_value(item.get("价格") or item.get("price")),
        })
    return normalized

def _normalize_compare_summary(summary):
    text = _text(summary)
    if not text:
        return "对比结果已生成"
    text = text.replace("comparison finished", "对比完成")
    text = text.replace("price is close", "价格接近")
    text = text.replace("not enough products to compare", "商品数量不足，无法对比")
    text = text.replace("performance", "性能")
    text = text.replace("camera", "拍照")
    text = text.replace("battery", "续航")
    text = text.replace("screen", "屏幕")
    text = text.replace("portability", "便携性")
    return text

def _normalize_compare_payload(data):
    payload = dict(data or {})
    rows = _normalize_compare_rows(payload.get("rows") or payload.get("comparison_rows") or [])
    payload["rows"] = rows
    payload["comparison_rows"] = rows
    payload["summary"] = _normalize_compare_summary(payload.get("summary"))
    return payload

def build_compare_tool(session):
    compare_service = CompareService(session)
    memory_service = MemoryService(session)

    @tool
    async def compare_products(product_ids: list[int]):
        """对多个商品做结构化对比，适合生成核心差异、优劣势和适用人群判断。"""
        if not product_ids or len(product_ids) == 1:
            return _bundle(
                "对比至少需要 2 个商品，当前不足以生成对比结论。",
                {"product_ids": product_ids or []},
                next_best_actions=["ask_clarification", "search_products"],
                should_continue=True,
                enough_for_finish=False,
            )
        cache_key = ",".join(str(pid) for pid in sorted(product_ids))
        cached = await memory_service.get_cached_compare_result(cache_key)
        if cached:
            cached = _normalize_compare_payload(cached)
            summary = _normalize_compare_summary(cached.get("summary") or "已命中缓存的对比结果")
            return _bundle(
                summary + "。当前已经形成对比结论，通常可以直接回复用户。",
                cached,
                next_best_actions=["finish", "summarize_comparison", "get_price_info", "get_product_detail"],
                should_continue=False,
                enough_for_finish=True,
            )
        result = _normalize_compare_payload(await compare_service.compare_products(product_ids))
        await memory_service.cache_compare_result(cache_key, result)
        summary = _normalize_compare_summary(result.get("summary") or "对比结果已生成")
        items = result.get("products") or result.get("product_list") or []
        has_result = bool(items) and not len(items) == 1
        return _bundle(
            summary + ("。当前已经形成对比结论。" if has_result else "。当前结果还不足以直接收束。"),
            result,
            next_best_actions=(["finish", "summarize_comparison", "get_price_info", "get_product_detail"] if has_result else ["search_products", "ask_clarification"]),
            should_continue=not has_result,
            enough_for_finish=has_result,
        )

    return compare_products
