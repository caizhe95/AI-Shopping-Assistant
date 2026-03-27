from langchain.tools import tool
from app.services.recommend_service import RecommendService


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


def build_recommend_tool(session):
    recommend_service = RecommendService(session)

    @tool
    async def recommend_products(query: str = "", candidate_ids: list[int] | None = None, limit: int = 5):
        """根据用户需求和候选商品生成推荐结果，适合产出主推荐结论。"""
        result = await recommend_service.recommend_products(
            query=query,
            candidate_ids=candidate_ids or [],
            limit=limit,
        )
        summary = str(result.get("summary") or "推荐结果已生成")

        items = (
            result.get("recommended_products")
            or result.get("product_list")
            or result.get("items")
            or []
        )

        if items:
            summary = f"{summary}。当前已经形成推荐结论，如无额外问题通常可以直接回复用户。"
            return _bundle(
                summary,
                result,
                next_best_actions=["finish", "explain_recommendation", "get_price_info", "get_product_detail"],
                should_continue=False,
                enough_for_finish=True,
            )

        summary = f"{summary}。当前推荐结果不充分，建议补充搜索、筛选或澄清需求。"
        return _bundle(
            summary,
            result,
            next_best_actions=["search_products", "filter_products", "ask_clarification"],
            should_continue=True,
            enough_for_finish=False,
        )

    return recommend_products