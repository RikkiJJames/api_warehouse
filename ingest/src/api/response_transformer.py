class ResponseTransformer:
    def extract(self, response, response_path=None):
        if response_path:
            for key in response_path.split("."):
                response = response.get(key, {})
        return response if isinstance(response, list) else []