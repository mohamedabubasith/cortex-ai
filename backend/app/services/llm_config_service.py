"""LLM Configuration Service"""
from typing import Dict, Any, List
from app.repositories.llm_repository import LLMRepository

class LLMConfigService:
    def __init__(self, llm_repo: LLMRepository):
        self.llm_repo = llm_repo
    
    async def create_config(
        self,
        user_id: str,
        name: str,
        provider: str,
        api_key: str,
        model: str,
        base_url: str = None
    ):
        """Create LLM configuration"""
        return await self.llm_repo.create(
            user_id=user_id,
            name=name,
            provider=provider,
            api_key=api_key,
            model=model,
            base_url=base_url
        )
    
    async def get_config(self, llm_id: str, user_id: str):
        """Get LLM config by ID"""
        return await self.llm_repo.get_by_id(llm_id, user_id)
    
    async def get_all_configs(self, user_id: str):
        """Get all LLM configs for user"""
        return await self.llm_repo.get_all(user_id)
    
    async def update_config(
        self,
        llm_id: str,
        user_id: str,
        name: str = None,
        provider: str = None,
        api_key: str = None,
        model: str = None,
        base_url: str = None
    ):
        """Update LLM configuration"""
        return await self.llm_repo.update(
            llm_id=llm_id,
            user_id=user_id,
            name=name,
            provider=provider,
            api_key=api_key,
            model=model,
            base_url=base_url
        )
    
    async def delete_config(self, llm_id: str, user_id: str) -> Dict[str, Any]:
        """Delete LLM configuration"""
        deleted = await self.llm_repo.delete(llm_id, user_id)
        
        if deleted:
            return {"success": True, "message": "LLM configuration deleted"}
        else:
            return {"success": False, "message": "LLM configuration not found"}
