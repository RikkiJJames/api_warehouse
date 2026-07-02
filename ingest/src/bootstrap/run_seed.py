from src.bootstrap.api_bootstrapper import ApiBootstrapper
from src.config.api.config_loader import ConfigLoader
from src.services.api_service import ApiService, get_service


def run_seed(api_dir: str, service: ApiService | None = None):
    try:
        loader = ConfigLoader(config_dir=api_dir)
        specs = loader.load_all()

        def _seed(svc: ApiService):
            bootstrapper = ApiBootstrapper(svc)
            for spec in specs:
                print(f"Seeding API: {spec.name}")
                bootstrapper.bootstrap_api(spec)
            print("Seeding complete.")

        if service is not None:
            _seed(service)
        else:
            with get_service() as svc:
                _seed(svc)

    except Exception as e:
        raise RuntimeError(f"Error during seeding: {e}") from e


if __name__ == "__main__":
    run_seed("src/config/api/mma")
