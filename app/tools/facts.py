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



CATEGORY_ALIASES = {
    'laptop': {'laptop', '笔记本', '笔记本电脑', '轻薄本', '轻薄笔记本', '办公本'},
    'smartphone': {'smartphone', '手机'},
    'tablet': {'tablet', '平板', '平板电脑'},
    'earbuds': {'earbuds', '耳机', '蓝牙耳机'},
    'watch': {'watch', '手表', '智能手表'},
}

def _category_tokens(value):
    text = str(value or '').strip().lower()
    if not text:
        return set()
    tokens = {text}
    for base, aliases in CATEGORY_ALIASES.items():
        lowered = {item.lower() for item in aliases}
        if text in lowered or text == base:
            tokens.update(lowered)
            tokens.add(base)
    return tokens

def _category_match(expected, actual):
    if not expected:
        return True
    return bool(_category_tokens(expected) & _category_tokens(actual))

def build_filter_tool(session):
    service = ProductService(session)

    @tool
    async def filter_products(
        query=None,
        brand=None,
        series=None,
        category=None,
        sub_category=None,
        is_own_brand=None,
        is_featured=None,
        min_price=None,
        max_price=None,
        limit=10,
    ):
        """按品牌、品类、价格和标签条件筛选商品候选，适合做初筛和精细过滤。"""
        items = await service.search_products(query=query, limit=max(limit * 3, 20))
        filtered = [
            item for item in items
            if (not brand or brand.lower() in str(item.get("brand")).lower())
            and (not series or series.lower() in str(item.get("series")).lower())
            and _category_match(category, item.get("category"))
            and (not sub_category or sub_category.lower() in str(item.get("sub_category")).lower())
            and (is_own_brand is None or bool(item.get("is_own_brand")) == bool(is_own_brand))
            and (is_featured is None or bool(item.get("is_featured")) == bool(is_featured))
            and (min_price is None or float(item.get("guide_price") or 0) >= float(min_price))
            and (max_price is None or float(item.get("guide_price") or 0) <= float(max_price))
        ][:limit]

        product_ids = [item.get("id") for item in filtered if item.get("id") is not None]
        summary = service.build_search_summary(filtered, query=query)
        summary = f"{summary}。当前结果更适合作为过滤后的候选池，通常还需要继续推荐、对比或补充详情。"

        data = {
            "query": query,
            "filters": {
                "brand": brand,
                "series": series,
                "category": category,
                "sub_category": sub_category,
                "is_own_brand": is_own_brand,
                "is_featured": is_featured,
                "min_price": min_price,
                "max_price": max_price,
            },
            "retrieved_products": items,
            "filtered_products": filtered,
            "product_list": filtered,
            "candidate_product_ids": product_ids,
            "candidate_count": len(filtered),
        }

        if not filtered:
            return _bundle(
                summary,
                data,
                next_best_actions=["ask_clarification"],
                should_continue=False,
                enough_for_finish=False,
            )

        if len(filtered) == 1:
            next_actions = ["get_product_detail", "get_price_info", "recommend_products"]
        else:
            next_actions = ["recommend_products", "compare_products", "get_product_detail"]

        return _bundle(
            summary,
            data,
            next_best_actions=next_actions,
            should_continue=True,
            enough_for_finish=False,
        )

    return filter_products


def build_detail_tool(session):
    service = ProductService(session)

    @tool
    async def get_product_detail(product_id: int):
        """获取单个商品的完整详情、价格区间和价格快照，适合补充事实信息。"""
        result = await service.get_product_detail(product_id)
        if not result:
            return _bundle(
                "未找到该商品详情。",
                {
                    "product_id": product_id,
                    "detail_result": {},
                    "price_context": {},
                    "price_snapshots": [],
                    "product_detail": {},
                },
                next_best_actions=["search_products", "ask_clarification"],
                should_continue=True,
                enough_for_finish=False,
            )

        summary = (result or {}).get("name") or "商品详情已获取"
        summary = f"{summary}，当前已经拿到关键详情，通常可以直接回答，或继续补价格/相似款。"

        data = {
            "detail_result": result or {},
            "price_context": (result or {}).get("price_context") or {},
            "price_snapshots": (result or {}).get("price_snapshots") or [],
            "product_detail": result or {},
        }

        return _bundle(
            summary,
            data,
            next_best_actions=["finish", "get_price_info", "find_similar_products", "compare_products"],
            should_continue=False,
            enough_for_finish=True,
        )

    return get_product_detail


def build_price_tool(session):
    service = ProductService(session)

    @tool
    async def get_price_info(product_id: int):
        """获取商品当前导购价、价格区间和价格快照信息，适合单独问价格时使用。"""
        result = await service.get_price_info(product_id)
        if not result:
            return _bundle(
                "未找到该商品价格信息。",
                {
                    "product_id": product_id,
                    "price_context": {},
                    "price_snapshots": [],
                    "price_result": {},
                },
                next_best_actions=["get_product_detail", "search_products", "ask_clarification"],
                should_continue=True,
                enough_for_finish=False,
            )

        summary = (result or {}).get("summary") or "价格信息已获取"
        summary = f"{summary}。当前已经拿到价格结论，通常可以直接回复用户。"

        data = {
            "price_context": result or {},
            "price_snapshots": (result or {}).get("price_snapshots") or [],
            "price_result": result or {},
        }

        return _bundle(
            summary,
            data,
            next_best_actions=["finish", "get_product_detail", "compare_products"],
            should_continue=False,
            enough_for_finish=True,
        )

    return get_price_info


def build_similar_tool(session):
    service = ProductService(session)

    @tool
    async def find_similar_products(product_id: int, limit=5):
        """基于目标商品查找相似候选，适合扩展备选和对比对象。"""
        seed = await service.get_product_detail(product_id)
        if not seed:
            return _bundle(
                "未找到对应商品，无法扩展相似候选。",
                {
                    "product_id": product_id,
                    "similar_products": [],
                    "comparison_candidates": [],
                    "product_list": [],
                    "candidate_product_ids": [],
                },
                next_best_actions=["search_products", "ask_clarification"],
                should_continue=True,
                enough_for_finish=False,
            )

        pool = await service.search_products(query=seed.get("name"), limit=max(limit * 4, 20))
        scored = sorted(
            (
                (_score_similar(seed, item), item)
                for item in pool
                if item.get("id") != product_id
            ),
            key=lambda pair: (
                -pair[0],
                not pair[1].get("is_featured"),
                not pair[1].get("is_own_brand"),
                pair[1].get("guide_price") or 0,
            ),
        )
        similar = [item for _, item in scored[:limit]]
        candidate_ids = [item.get("id") for item in similar if item.get("id") is not None]

        summary = "已找到相似商品，当前结果更适合作为备选池，通常还应继续推荐、对比或补充详情。"
        return _bundle(
            summary,
            {
                "product_id": product_id,
                "seed_product": seed,
                "similar_products": similar,
                "comparison_candidates": similar,
                "product_list": similar,
                "candidate_product_ids": candidate_ids,
                "candidate_count": len(similar),
            },
            next_best_actions=["compare_products", "recommend_products", "get_product_detail"],
            should_continue=bool(similar),
            enough_for_finish=False,
        )

    return find_similar_products


def _score_similar(seed, item):
    score = 0.0
    score += 0.5 if item.get("category") == seed.get("category") else 0.0
    score += 0.4 if item.get("sub_category") == seed.get("sub_category") else 0.0
    score += 0.3 if item.get("brand") == seed.get("brand") else 0.0
    score += 0.12 * len(set(item.get("features") or []).intersection(set(seed.get("features") or [])))
    score += 0.10 * len(set(item.get("usage_scenarios") or []).intersection(set(seed.get("usage_scenarios") or [])))
    score += 0.08 * len(set(item.get("target_users") or []).intersection(set(seed.get("target_users") or [])))
    score += 0.10 if bool(item.get("is_featured")) else 0.0
    score += 0.05 if bool(item.get("is_own_brand")) else 0.0
    return score
