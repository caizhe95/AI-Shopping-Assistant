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


def build_search_tool(session):
    product_service = ProductService(session)

    @tool
    async def search_products(query: str = "", limit: int = 10):
        """按用户关键词搜索商品候选，适合导购初筛、泛搜索和召回候选商品。"""
        products = await product_service.search_products(query=query, limit=limit)
        product_ids = [p.get("id") for p in products if isinstance(p, dict) and p.get("id") is not None]

        if not products:
            summary = f"没有找到与“{query}”相关的商品，当前信息不足以直接给出结论，建议澄清品牌、预算或用途。"
            return _bundle(
                summary,
                {
                    "query": query,
                    "limit": limit,
                    "retrieved_products": [],
                    "filtered_products": [],
                    "product_list": [],
                    "candidate_product_ids": [],
                    "candidate_count": 0,
                },
                next_best_actions=["ask_clarification"],
                should_continue=False,
                enough_for_finish=False,
            )

        summary = product_service.build_search_summary(products, query=query)
        summary = f"{summary}。当前结果更适合作为候选池，通常还应继续做推荐、对比、详情或价格查询。"

        next_actions = (
            ["get_product_detail", "get_price_info", "recommend_products"]
            if len(products) == 1
            else ["recommend_products", "filter_products", "compare_products", "get_product_detail"]
        )

        return _bundle(
            summary,
            {
                "query": query,
                "limit": limit,
                "retrieved_products": products,
                "filtered_products": products,
                "product_list": products,
                "candidate_product_ids": product_ids,
                "candidate_count": len(products),
            },
            next_best_actions=next_actions,
            should_continue=True,
            enough_for_finish=False,
        )

    return search_products