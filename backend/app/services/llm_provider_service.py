from typing import Dict, Any, Optional, List
from fastapi import HTTPException
from app.services.llm.factory import LLMProviderFactory

class LLMProviderService:

    async def list_models(
        self,
        provider: str,
        api_key: str,
        base_url: Optional[str] = None
    ) -> List[Dict[str, str]]:
        try:
            llm_provider = LLMProviderFactory.get_provider(provider)
            return await llm_provider.list_models(api_key=api_key, base_url=base_url)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to list models: {str(e)}")

    async def test_connection(
        self,
        provider: str,
        api_key: str,
        model: str,
        base_url: Optional[str] = None
    ) -> Dict[str, Any]:
        try:
            llm_provider = LLMProviderFactory.get_provider(provider)
            return await llm_provider.test_connection(
                api_key=api_key,
                model=model,
                base_url=base_url
            )
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Service error: {str(e)}")
