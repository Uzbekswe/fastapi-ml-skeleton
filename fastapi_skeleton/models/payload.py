from pydantic import BaseModel, ConfigDict, Field


class HousePredictionPayload(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "median_income_in_block": 8.3252,
                    "median_house_age_in_block": 41,
                    "average_rooms": 6.98,
                    "average_bedrooms": 1.02,
                    "population_per_block": 322,
                    "average_house_occupancy": 2.56,
                    "block_latitude": 37.88,
                    "block_longitude": -122.23,
                }
            ]
        }
    )

    median_income_in_block: float = Field(
        gt=0, description="Median income for households in the block (tens of thousands USD)"
    )
    median_house_age_in_block: int = Field(
        gt=0, description="Median age of houses in the block (years)"
    )
    average_rooms: float = Field(
        gt=0, description="Average number of rooms per household"
    )
    average_bedrooms: float = Field(
        gt=0, description="Average number of bedrooms per household"
    )
    population_per_block: int = Field(
        gt=0, description="Total population in the block"
    )
    average_house_occupancy: float = Field(
        gt=0, description="Average number of occupants per household"
    )
    block_latitude: float = Field(
        ge=-90, le=90, description="Latitude of the block centroid"
    )
    block_longitude: float = Field(
        ge=-180, le=180, description="Longitude of the block centroid"
    )

    def to_list(self) -> list[float]:
        return list(self.model_dump().values())
