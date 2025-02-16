from typing import cast, List
import voyageai

class VoyageEmbeddingFunction:
    #     def __init__(
    #     self,
    #     base_url: str = "http://localhost:3000",
    #     username: Optional[str] = None,
    #     password: Optional[str] = None,
    #     timeout: float = 30.0,
    # ):
    def __init__(
            self,
            api_key: str,
            max_retries: int,
            model_name: str,
            batch_size: int
            ):
        self.client = voyageai.Client(
            api_key=api_key,
            max_retries=max_retries
        )
        self.model_name = model_name
        self.batch_size = batch_size

    def __call__(self, input: List[str]) -> List[List[float]]:
        embeddings = []
        total_tokens = 0

        for i in range(0, len(input), self.batch_size):
            res = self.client.embed(
                input[i : i + self.batch_size],
                model=self.model_name,
                input_type="document"
            )
            embeddings += res.embeddings
            total_tokens += res.total_tokens
        return embeddings