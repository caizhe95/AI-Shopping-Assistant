# Smart Shopping Agent

## Recommend API

`POST /api/v1/recommend`

Request:

```json
{
  "session_id": "s1",
  "user_query": "Need a light office laptop under 4000",
  "candidate_ids": [1, 3, 5],
  "user_id": "u1"
}
```

Response:

```json
{
  "session_id": "s1",
  "reply": "Recommend Product A. It fits the budget, is suitable for office work, and looks like the best overall match. If you want, I can also compare it with Product B and Product C.",
  "recommendation": {
    "query": "Need a light office laptop under 4000",
    "budget": 4000,
    "compare_needed": true,
    "compare_product_ids": [1, 3, 5],
    "summary": "best match: Product A; budget 4000; compare suggested",
    "recommendations": [
      {
        "id": 1,
        "brand": "BrandX",
        "name": "Product A",
        "guide_price": 3899,
        "score": 0.91,
        "reasons": ["query matched: office, laptop", "within budget at 3899", "featured model", "lightweight, long battery life"]
      },
      {
        "id": 3,
        "brand": "BrandY",
        "name": "Product B",
        "guide_price": 3799,
        "score": 0.85,
        "reasons": ["query matched: office", "within budget at 3799", "good value"]
      },
      {
        "id": 5,
        "brand": "BrandZ",
        "name": "Product C",
        "guide_price": 4099,
        "score": 0.77,
        "reasons": ["above budget at 4099", "strong performance"]
      }
    ]
  }
}
```
  
## Docker  
  
Run the full stack with:  
docker compose up --build  
  
Services:  
- API: http://localhost:8000  
- Health: http://localhost:8000/health  
- MySQL: localhost:3306  
- Redis: localhost:6379 
