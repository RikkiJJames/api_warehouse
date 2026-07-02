from pydantic import BaseModel


class Fighter(BaseModel):
    fighter_id: int | None
    name: str | None
    nickname: str | None
    gender: str | None
    birth_date: str | None
    age: int | None
    height: str | None
    weight: str | None
    reach: str | None
    stance: str | None
    category: str | None
    team_name: str | None

    model_config = {"from_attributes": True}
