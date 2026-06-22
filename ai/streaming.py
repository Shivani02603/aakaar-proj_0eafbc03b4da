import os
from fastapi import FastAPI, Query
from fastapi.responses import StreamingResponse
from ai.embeddings import get_embedding
from ai.vector_store import vector_store
from ai.llm import gemini_flash

app = FastAPI()

async def stream_answer(query: str, session_id: str, user_id: str):
    # Step 1: Embed query using get_embedding()
    embedding_model_key = os.getenv("OPENAI_API_KEY")
    if not embedding_model_key:
        raise ValueError("OPENAI_API_KEY environment variable not set.")
    query_embedding = get_embedding(query, model="text-embedding-3-small", api_key=embedding_model_key)

    # Step 2: Retrieve top-5 chunks from vector store via vector_store.search()
    top_chunks = vector_store.search(
        embedding=query_embedding,
        top_k=5,
        session_id=session_id,
        user_id=user_id
    )

    # Step 3: Build prompt with retrieved context
    context = "\n".join([chunk["content"] for chunk in top_chunks])
    prompt = f"Context:\n{context}\n\nQuestion:\n{query}\n\nAnswer:"

    # Step 4: Call gemini-2.0-flash with stream=True
    gemini_api_key = os.getenv("GOOGLE_API_KEY")
    if not gemini_api_key:
        raise ValueError("GOOGLE_API_KEY environment variable not set.")
    llm_response = gemini_flash.generate(
        prompt=prompt,
        stream=True,
        api_key=gemini_api_key
    )

    # Step 5: Yield each token as: 'data: {"token": "<tok>"}\n'
    citations = [chunk["source"] for chunk in top_chunks]
    async for token in llm_response:
        yield f'data: {{"token": "{token}"}}\n'

    # Step 6: After final token, yield: 'data: {"done": true, "citations": [<source list>]}\n'
    yield f'data: {{"done": true, "citations": {citations}}}\n'

@app.get("/stream")
async def stream(query: str = Query(...), session_id: str = Query(...), user_id: str = Query(...)):
    return StreamingResponse(stream_answer(query, session_id, user_id), media_type="text/event-stream")