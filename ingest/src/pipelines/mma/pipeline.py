from src.pipelines.api_pipeline import ApiPipeline


class MmaPipeline(ApiPipeline):

    def __init__(self):
        super().__init__("mma")

    def get_api_key(self):
        return self.meta.config["api_key"]

    def get_auth_header(self):
        return "x-apisports-key"
