from typing import Union, Optional
from pydantic_ai.models import Model
from config import Settings
from services.local_model import LocalModel

_local_model_instance: Optional[LocalModel] = None

def get_model(settings: Settings) -> Union[str, Model]:
    global _local_model_instance
    print(f"get_model called. use_local_model={settings.use_local_model}, instance={_local_model_instance}")
    
    if settings.use_local_model:
        if _local_model_instance is None:
            _local_model_instance = LocalModel(settings.local_model_path)
        return _local_model_instance
    else:
        return settings.model_name
