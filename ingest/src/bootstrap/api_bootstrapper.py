from src.config.api.schemas import ApiSpec
from src.services.api_service import ApiService


class ApiBootstrapper:
    def __init__(self, service: ApiService):
        self.service = service

    def bootstrap_api(self, spec: ApiSpec):
        api = self.service.repository.get_or_create_api(
            name=spec.name,
            description=spec.description,
            base_url=spec.base_url,
        )

        for ep in spec.endpoints:
            endpoint = self.service.repository.upsert_endpoint(
                api_id=api.id,
                logical_name=ep.logical_name,
                path_template=ep.path_template,
                exec_order=ep.exec_order,
                is_active=ep.is_active,
                db_target=ep.db_target,
                db_target_column=ep.db_target_column,
                db_source_field=ep.db_source_field,
                response_path=ep.response_path,
            )

            for param in ep.params:
                self.service.repository.upsert_endpoint_param(
                    endpoint_id=endpoint.id,
                    param_name=param.param_name,
                    required=param.required,
                    default_value=param.default_value,
                    value_type=param.value_type,
                    source_table=param.source_table,
                    source_column=param.source_column,
                    is_distinct=param.is_distinct,
                )

        for cfg in spec.api_config:
            self.service.repository.add_config(
                api_id=api.id,
                parameter_name=cfg.parameter_name,
                parameter_value=cfg.parameter_value,
            )
