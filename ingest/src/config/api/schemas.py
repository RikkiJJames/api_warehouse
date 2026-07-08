from pydantic import BaseModel


class ApiConfigSpec(BaseModel):
    parameter_name: str
    parameter_value: str | None = None


class EndpointParamSpec(BaseModel):
    param_name: str
    required: bool = False
    default_value: str | None = None
    value_type: str = "string"
    source_table: str | None = None
    source_column: str | None = None
    is_distinct: bool = False


class EndpointConfigSpec(BaseModel):
    logical_name: str
    path_template: str
    exec_order: int
    is_active: bool
    db_target: str | None = None
    db_target_column: str | None = None
    db_source_field: str | None = None
    response_path: str | None = None  # dot-notation path into the response body, e.g. "recenttracks.track"
    method: str = "GET"
    query: str | None = None  # raw GraphQL query text, used when method == "POST"
    params: list[EndpointParamSpec] = []


class ApiSpec(BaseModel):
    name: str
    description: str
    base_url: str
    api_config: list[ApiConfigSpec]
    endpoints: list[EndpointConfigSpec]
