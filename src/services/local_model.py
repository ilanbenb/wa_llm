import asyncio
from typing import Optional, List
from pydantic_ai.models import Model, ModelRequest, ModelResponse
from pydantic_ai.messages import (
    ModelMessage,
    ModelRequest,
    ModelResponse,
    TextPart,
    UserPromptPart,
    SystemPromptPart,
)
from pydantic_ai.settings import ModelSettings
# import torch
# from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline, BitsAndBytesConfig

import logging

logger = logging.getLogger(__name__)

class LocalModel(Model):
    def __init__(self, model_name: str):
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline, BitsAndBytesConfig

        self._model_name = model_name
        logger.info(f"Loading local model: {model_name}...")
        print(f"Loading local model: {model_name}...", flush=True)
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        
        try:
            logger.info(f"Attempting to load local model: {model_name} on GPU...")
            print(f"Attempting to load local model: {model_name} on GPU...", flush=True)
            quantization_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_compute_dtype=torch.float16
            )
            
            self.model = AutoModelForCausalLM.from_pretrained(
                model_name,
                device_map="auto",
                quantization_config=quantization_config,
                trust_remote_code=True
            )
        except Exception as e:
            logger.warning(f"Failed to load model on GPU: {e}. Falling back to CPU.")
            print(f"Failed to load model on GPU: {e}. Falling back to CPU.", flush=True)
            self.model = AutoModelForCausalLM.from_pretrained(
                model_name,
                device_map="cpu",
                trust_remote_code=True,
                torch_dtype=torch.float32
            )

        self.pipe = pipeline(
            "text-generation",
            model=self.model,
            tokenizer=self.tokenizer,
        )
        logger.info("Local model loaded.")
        print("Local model loaded.", flush=True)

    @property
    def model_name(self) -> str:
        return self._model_name

    @property
    def system(self) -> str:
        return ""

    async def request(
        self,
        messages: list[ModelMessage],
        settings: Optional[ModelSettings] = None,
        model_request_parameters: Optional[dict] = None,
    ) -> ModelResponse:
        # Convert messages to prompt
        # This is a very basic prompt construction. 
        # You might want to use the tokenizer's chat template if available.
        prompt = ""
        for msg in messages:
            if isinstance(msg, ModelRequest):
                for part in msg.parts:
                    if isinstance(part, SystemPromptPart):
                        prompt += f"System: {part.content}\n"
                    elif isinstance(part, UserPromptPart):
                        prompt += f"User: {part.content}\n"
            elif isinstance(msg, ModelResponse):
                 for part in msg.parts:
                    if isinstance(part, TextPart):
                        prompt += f"Assistant: {part.content}\n"

        prompt += "Assistant: "

        # Run generation in a separate thread to avoid blocking the event loop
        loop = asyncio.get_running_loop()
        generated_text = await loop.run_in_executor(
            None, self._generate, prompt
        )

        return ModelResponse(
            parts=[TextPart(content=generated_text)],
        )

    def _generate(self, prompt: str) -> str:
        outputs = self.pipe(
            prompt,
            max_new_tokens=512,
            do_sample=True,
            temperature=0.7,
            top_p=0.9,
            return_full_text=False
        )
        return outputs[0]["generated_text"]

    def name(self) -> str:
        return f"local:{self.model_name}"
