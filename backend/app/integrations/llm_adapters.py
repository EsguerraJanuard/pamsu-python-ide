import os
import json
from datetime import datetime, timezone
import httpx

from app.integrations.local_llm import (
    LocalLLMAdapter,
    LocalLLMAssistanceRequest,
    LocalLLMAssistanceResponse,
    LocalLLMAdapterUnavailableError,
    LocalLLMAdapterRejectedError,
    LocalLLMAdapterResponseError,
)

class OllamaLLMAdapter:
    """
    Adapter for a local Ollama instance or any OpenAI-compatible API.
    """
    def __init__(self):
        self.api_url = os.getenv("LLM_API_URL", "http://localhost:11434/api/generate")
        self.model_name = os.getenv("LLM_MODEL_NAME", "llama3")
        self.api_key = os.getenv("LLM_API_KEY", "")

    def generate_assistance(
        self,
        *,
        request: LocalLLMAssistanceRequest,
    ) -> LocalLLMAssistanceResponse:
        
        # Build prompt from context
        prompt = "You are a helpful programming tutor. Help the student understand their code or errors without giving them the direct solution.\n\n"
        
        if request.activity_title:
            prompt += f"Activity: {request.activity_title}\n"
        if request.public_instructions:
            prompt += f"Instructions: {request.public_instructions}\n"
        
        for item in request.public_review_context:
            prompt += f"Context: {item}\n"
            
        if request.source_code:
            prompt += f"\nStudent Code:\n{request.source_code}\n"
            
        if request.user_question:
            prompt += f"\nStudent Question: {request.user_question}\n"
            
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": False
        }
        
        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
            
        try:
            with httpx.Client(timeout=30.0) as client:
                # Basic Ollama integration
                response = client.post(self.api_url, json=payload, headers=headers)
                response.raise_for_status()
                data = response.json()
                
                content = data.get("response", "")
                if not content:
                    content = "The assistant provided no response."
                    
                return LocalLLMAssistanceResponse(
                    request_id=request.request_id,
                    assistance_kind=request.assistance_kind,
                    content=content,
                    model_label=self.model_name,
                    generated_at=datetime.now(timezone.utc)
                )
        except Exception as e:
            raise LocalLLMAdapterResponseError(f"Failed to generate assistance: {str(e)}")

class UnavailableLLMAdapter:
    def generate_assistance(
        self,
        *,
        request: LocalLLMAssistanceRequest,
    ) -> LocalLLMAssistanceResponse:
        raise LocalLLMAdapterUnavailableError("No local LLM adapter is configured.")

def get_local_llm_adapter() -> LocalLLMAdapter:
    if os.getenv("LLM_API_URL"):
        return OllamaLLMAdapter()
    return UnavailableLLMAdapter()