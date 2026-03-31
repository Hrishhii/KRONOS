import asyncio, json, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from backend.schemas import AggregationRequest
from backend.graph import process_query

async def run_test(label, query):
    print(f"\n{'='*60}")
    print(f"TEST: {label}")
    print(f"QUERY: {query}")
    print('='*60)
    resp = await process_query(AggregationRequest(query=query))
    print(f"API STATUS: {json.dumps(resp.api_status)}")
    print(f"\n--- INSIGHT ---\n")
    print(resp.insight)
    print(f"\n--- END ---\n")
    
    # Automated checks
    checks = {
        "no_raw_function_tags": "<function=" not in resp.insight,
        "has_exec_summary": "Executive Summary" in resp.insight,
        "no_key_takeaways": "Key Takeaways" not in resp.insight,
    }
    print("CHECKS:", json.dumps(checks, indent=2))
    return all(checks.values())

async def main():
    r1 = await run_test("Germany Weather (capital city + dated NASA rows)", "What is the current weather in Germany?")
    r2 = await run_test("India-Pakistan tensions (no raw tags)", "Geopolitical situation India Pakistan currently")
    
    print("\n\n====== FINAL VERDICT ======")
    print("All checks passed!" if (r1 and r2) else "SOME CHECKS FAILED. Review output above.")

asyncio.run(main())
