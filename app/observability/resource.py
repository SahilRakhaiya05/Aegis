from opentelemetry.sdk.resources import Resource

from app.settings import settings


def build_resource() -> Resource:
    return Resource.create(
        {
            "service.name": settings.OTEL_SERVICE_NAME,
            "service.version": settings.SERVICE_VERSION,
            "deployment.environment": settings.deployment_environment,
            "telemetry.sdk.language": "python",
            "aegis.product": settings.PRODUCT_TITLE,
        }
    )
