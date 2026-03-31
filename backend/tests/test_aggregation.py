import asyncio
import json
from backend.schemas import AggregationRequest
from backend.graph import process_query

async def main():
    print("Testing Aggregation for Query: 'what are the tensions between US and Iran currently'...")
    req = AggregationRequest(query="what are the tensions between US and Iran currently")
    
    # Run the graph
    resp = await process_query(req)
    
    # Write the JSON output to a file
    with open("test_output.json", "w", encoding="utf-8") as f:
        f.write(resp.model_dump_json(indent=2))
    print("Output written to test_output.json")
    
    # Simple validation checks
    print("\n--- Validation ---")
    print(f"Retrieved At: {resp.retrieved_at}")
    print(f"API Statuses:")
    for api, status in resp.api_status.items():
        print(f"  {api}: {status}")

if __name__ == "__main__":
    asyncio.run(main())
