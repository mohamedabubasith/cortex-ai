from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from pydantic import BaseModel

from app.core.database import get_db
from app.models import models
from app.schemas import schemas
from app.repositories.llm_repository import LLMRepository
from app.services.llm_config_service import LLMConfigService
from app.services.auth_service import get_current_active_user

router = APIRouter()

def get_llm_service(db: AsyncSession = Depends(get_db)) -> LLMConfigService:
    """Dependency injection for LLM service"""
    return LLMConfigService(LLMRepository(db))

@router.post("/", response_model=schemas.LLMConfiguration)
async def create_llm_config(
    config: schemas.LLMConfigurationCreate,
    current_user: models.User = Depends(get_current_active_user),
    llm_service: LLMConfigService = Depends(get_llm_service)
):
    """Create LLM configuration"""
    return await llm_service.create_config(
        user_id=current_user.id,
        name=config.name,
        api_key=config.api_key,
        model=config.model,
        base_url=config.base_url
    )

@router.get("/", response_model=List[schemas.LLMConfiguration])
async def get_llm_configs(
    current_user: models.User = Depends(get_current_active_user),
    llm_service: LLMConfigService = Depends(get_llm_service)
):
    """Get all LLM configurations"""
    return await llm_service.get_all_configs(current_user.id)

@router.get("/{llm_id}", response_model=schemas.LLMConfiguration)
async def get_llm_config(
    llm_id: str,
    current_user: models.User = Depends(get_current_active_user),
    llm_service: LLMConfigService = Depends(get_llm_service)
):
    """Get LLM configuration by ID"""
    config = await llm_service.get_config(llm_id, current_user.id)
    
    if not config:
        raise HTTPException(status_code=404, detail="LLM configuration not found")
    
    return config

@router.put("/{llm_id}", response_model=schemas.LLMConfiguration)
async def update_llm_config(
    llm_id: str,
    config: schemas.LLMConfigurationUpdate,
    current_user: models.User = Depends(get_current_active_user),
    llm_service: LLMConfigService = Depends(get_llm_service)
):
    """Update LLM configuration"""
    updated = await llm_service.update_config(
        llm_id=llm_id,
        user_id=current_user.id,
        name=config.name,
        api_key=config.api_key,
        model=config.model,
        base_url=config.base_url
    )
    
    if not updated:
        raise HTTPException(status_code=404, detail="LLM configuration not found")
    
    return updated

@router.delete("/{llm_id}")
async def delete_llm_config(
    llm_id: str,
    current_user: models.User = Depends(get_current_active_user),
    llm_service: LLMConfigService = Depends(get_llm_service)
):
    """Delete LLM configuration"""
    result = await llm_service.delete_config(llm_id, current_user.id)
    
    if not result["success"]:
        raise HTTPException(status_code=404, detail=result["message"])
    
    return result

class LLMTestRequest(BaseModel):
    api_key: str
    base_url: str = None
    model: str

@router.post("/test")
async def test_llm_connection(
    request: LLMTestRequest,
    current_user: models.User = Depends(get_current_active_user)
):
    """Test LLM connection with actual chat completion"""
    try:
        from openai import AsyncOpenAI
        
        client_kwargs = {"api_key": request.api_key}
        if request.base_url:
            client_kwargs["base_url"] = request.base_url
        
        client = AsyncOpenAI(**client_kwargs)
        
        # IMPORTANT: Test with actual chat completion, not just models.list()
        # This validates API key, base URL, AND model access
        response = await client.chat.completions.create(
            model=request.model,
            messages=[{"role": "user", "content": "test"}],
            max_tokens=5
        )
        
        return {
            "status": "success", 
            "message": f"Connection successful! Model '{request.model}' is accessible.",
            "test_response": response.choices[0].message.content if response.choices else None
        }
    except Exception as e:
        error_msg = str(e)
        status_code = 400
        
        # Provide specific error messages
        if "401" in error_msg or "Unauthorized" in error_msg:
            detail = "API key is invalid or expired"
            status_code = 401
        elif "403" in error_msg or "Forbidden" in error_msg:
            detail = f"API key doesn't have access to model '{request.model}'"
            status_code = 403
        elif "404" in error_msg:
            detail = f"Model '{request.model}' not found"
            status_code = 404
        else:
            detail = f"Connection failed: {error_msg}"
        
        raise HTTPException(status_code=status_code, detail=detail)

