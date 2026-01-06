from abc import ABC, abstractmethod
from typing import Dict, Any, Callable

class BaseTool(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @property
    @abstractmethod
    def schema(self) -> Dict[str, Any]:
        """Return the JSON schema for the tool."""
        pass

    @abstractmethod
    async def execute(self, **kwargs) -> Any:
        """Execute the tool with the given arguments."""
        pass
