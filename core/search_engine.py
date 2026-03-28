from ddgs import DDGS

def fetch_search_data(query):
    try:
        with DDGS() as ddgs:
            results = ddgs.text(query, max_results=5)
            return " ".join([r["body"] for r in results])
    except Exception as e:
        print("Search error:", e)
        return ""
