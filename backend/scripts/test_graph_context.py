from backend.graph_engine_connector import db
import asyncio

async def test():
    print("Testing Graph Context Retrieval...")
    context = db.get_contextual_graph_data(["India", "Russia", "USA"])
    print(context)

if __name__ == "__main__":
    asyncio.run(test())
