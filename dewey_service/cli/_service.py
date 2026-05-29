"""CLI service factory helpers."""

from __future__ import annotations

from dewey_service.defaults import AWS_PROFILE_REQUIRED_MESSAGE, resolve_aws_profile
from dewey_service.service import DeweyService
from dewey_service.settings import get_settings
from dewey_service.storage import S3StorageClient
from dewey_service.tapdb_backend import TapDBBackend


def build_cli_service() -> DeweyService:
    """Build a DeweyService from explicit runtime settings."""

    settings = get_settings()
    aws_profile = resolve_aws_profile(config_profile=settings.aws_profile)
    if not aws_profile:
        raise RuntimeError(AWS_PROFILE_REQUIRED_MESSAGE)
    service = DeweyService(
        TapDBBackend(app_username="dewey"),
        storage_client=S3StorageClient(
            profile=aws_profile,
            region=settings.aws_region,
        ),
        managed_storage_bucket=settings.managed_storage_bucket,
        managed_storage_prefix=settings.managed_storage_prefix,
        upload_session_ttl_seconds=settings.upload_session_ttl_seconds,
        upload_token_secret=settings.session_secret_key,
        search_export_max_rows=settings.search_export_max_rows,
        literature_allowed_domains=settings.literature_allowed_domains,
        literature_request_timeout_seconds=settings.literature_request_timeout_seconds,
        qeo_ingest_url=settings.qeo_ingest_url,
        qeo_api_token=settings.qeo_api_token,
        qeo_consumer_group=settings.qeo_consumer_group,
        qeo_timeout_seconds=settings.qeo_timeout_seconds,
        qeo_ca_bundle_path=settings.qeo_ca_bundle_path,
    )
    service.bootstrap()
    return service


__all__ = ["build_cli_service"]
