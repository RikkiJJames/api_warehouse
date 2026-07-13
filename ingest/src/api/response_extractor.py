class ResponseExtractor:
    def extract(self, response: dict | list, response_path: str | None) -> list:
        """
        Normalises API responses into a list of records.
        """
        if isinstance(response, list):
            return response

        if not isinstance(response, dict):
            return []
        if response_path:
            for key in response_path.split("."):
                if not isinstance(response, dict):
                    return []
                response = response.get(key)
            if isinstance(response, list):
                return response
            if isinstance(response, dict):
                return [response]
            return []
        # common API conventions
        for key in ("response", "items", "data", "results"):
            if isinstance(response, dict) and key in response:
                response = response[key]

        if isinstance(response, list):
            return response
        # A bare single-resource object (e.g. Trakt's GET /movies/{id}) isn't
        # wrapped in any of the keys above — treat it as one record rather
        # than silently dropping it.
        if isinstance(response, dict):
            return [response]
        return []