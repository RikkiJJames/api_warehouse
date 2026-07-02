from pydantic import BaseModel


class Team(BaseModel):
    team_id: int | None
    team_name: str | None
    team_code: str | None
    team_country: str | None
    team_founded: int | None
    team_national: bool | None
    team_logo: str | None
    venue_id: int | None

    model_config = {"from_attributes": True}
