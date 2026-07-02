import re
from src.api.execution_context import ExecutionContext

class Resolver:
    VAR_PATTERN = re.compile(r"{(.*?)}")

    def __init__(self, context: ExecutionContext):
        self.context = context

    def resolve(self, template: str) -> str:
        for var in self.VAR_PATTERN.findall(template):
            value = self.context.get(var)

            if value is None:
                value = self.context.find_first_field(var)

            if value is None:
                raise ValueError(f"Cannot resolve variable: {var}")

            template = template.replace(f"{{{var}}}", str(value))

        return template