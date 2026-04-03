from pydantic import BaseModel, ConfigDict


class HeartbeatResult(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "is_alive": True,
                }
            ]
        }
    )

    is_alive: bool
