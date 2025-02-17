from voyageai.client_async import AsyncClient


from typing import List


async def voyage_embed_text(embedding_client: AsyncClient, input: List[str]) -> List[List[float]]:
    model_name = 'voyage-3'
    batch_size = 128
    embeddings = []
    total_tokens = 0

    for i in range(0, len(input), batch_size):
        res = await embedding_client.embed(
            input[i : i + batch_size],
            model=model_name,
            input_type="document"
        )
        embeddings += res.embeddings
        total_tokens += res.total_tokens
    return embeddings