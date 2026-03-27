from langchain.tools import tool

from app.services.product_service import ProductService


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


def _pick_result(payload, primary_key):
    payload = payload or {}
    if isinstance(payload, dict) and isinstance(payload.get(primary_key), dict):
        return payload.get(primary_key)
    if isinstance(payload, dict) and isinstance(payload.get("data"), dict):
        data = payload.get("data") or {}
        if isinstance(data.get(primary_key), dict):
            return data.get(primary_key)
        return data
    return payload if isinstance(payload, dict) else {}


def build_explain_recommendation_tool(session):
    ProductService(session)

    @tool
    async def explain_recommendation(recommendation_result=None, product_ids=None, query=None):
        """基于已有推荐结果补充推荐理由、备选关系和适合人群，不负责重新做主推荐。"""
        result = _pick_result(recommendation_result, "recommendation_result")
        items = result.get("recommended_products") or result.get("product_list") or []
        top = result.get("top_product") or (items[0] if items else {})
        resolved_ids = product_ids or result.get("compare_product_ids") or [
            item.get("id") for item in items if item.get("id") is not None
        ]
        summary = result.get("summary") or result.get("summary_text") or "推荐理由已补充"

        normalized = dict(result)
        normalized.update(
            {
                "recommended_products": items,
                "product_list": items,
                "top_product": top,
                "summary": summary,
            }
        )

        data = {
            "recommendation_result": normalized,
            "recommended_products": items,
            "product_list": items,
            "top_product": top,
            "product_ids": resolved_ids,
            "query": query or result.get("query"),
            "summary": summary,
            "explanation": summary,
        }

        return _bundle(
            f"{summary}。当前推荐理由已经补充完整，通常可以直接回复用户。",
            data,
            next_best_actions=["finish", "get_price_info", "get_product_detail"],
            should_continue=False,
            enough_for_finish=True,
        )

    return explain_recommendation


def build_summarize_comparison_tool(session):
    ProductService(session)

    @tool
    async def summarize_comparison(comparison_result=None, product_ids=None):
        """基于已有对比结果生成简洁总结，适合在 compare 模式下收束回答。"""
        result = _pick_result(comparison_result, "comparison_result")
        rows = result.get("comparison_rows") or result.get("rows") or []
        items = result.get("product_list") or result.get("products") or result.get("comparison_candidates") or []
        resolved_ids = product_ids or [item.get("id") for item in items if item.get("id") is not None]
        summary = result.get("summary") or result.get("summary_text") or "对比总结已生成"

        normalized = dict(result)
        normalized.update(
            {
                "comparison_rows": rows,
                "rows": rows,
                "product_list": items,
                "products": items,
                "summary": summary,
            }
        )

        data = {
            "comparison_result": normalized,
            "comparison_rows": rows,
            "rows": rows,
            "product_list": items,
            "products": items,
            "product_ids": resolved_ids,
            "summary": summary,
        }

        return _bundle(
            f"{summary}。当前对比总结已经完成，通常可以直接回复用户。",
            data,
            next_best_actions=["finish", "get_price_info", "get_product_detail"],
            should_continue=False,
            enough_for_finish=True,
        )

    return summarize_comparison