from __future__ import annotations

import io
import zipfile

import pytest

from dewey_service.service import DeweyNotFoundError, DeweyService
from tests.support.service_fakes import _FakeStorageClient


def test_register_artifact_replay_and_identity_reuse(service: DeweyService) -> None:
    service.bootstrap()

    status_code, created = service.register_artifact(
        artifact_type="FASTQ",
        storage_backend="s3",
        bucket="bucket-1",
        key="reads/r1.fastq.gz",
        version_id=None,
        size=123,
        checksums={"sha256": "abc"},
        content_type="application/gzip",
        original_filename="r1.fastq.gz",
        producer_system="atlas",
        producer_object_euid="OBJ-1",
        storage_class="standard",
        availability_status="ready",
        metadata={"lane": 1},
        idempotency_key="idem-1",
    )

    replay_code, replay = service.register_artifact(
        artifact_type="fastq",
        storage_backend="s3",
        bucket="bucket-1",
        key="reads/r1.fastq.gz",
        version_id=None,
        size=123,
        checksums={"sha256": "abc"},
        content_type="application/gzip",
        original_filename="r1.fastq.gz",
        producer_system="atlas",
        producer_object_euid="OBJ-1",
        storage_class="standard",
        availability_status="ready",
        metadata={"lane": 1},
        idempotency_key="idem-1",
    )

    reused_code, reused = service.register_artifact(
        artifact_type="fastq",
        storage_backend="s3",
        bucket="bucket-1",
        key="reads/r1.fastq.gz",
        version_id=None,
        size=123,
        checksums={"sha256": "abc"},
        content_type="application/gzip",
        original_filename="r1.fastq.gz",
        producer_system="atlas",
        producer_object_euid="OBJ-1",
        storage_class="standard",
        availability_status="ready",
        metadata={"lane": 1},
        idempotency_key="idem-2",
    )

    assert status_code == 201
    assert replay_code == 201
    assert replay["artifact_euid"] == created["artifact_euid"]
    assert reused_code == 200
    assert reused["artifact_euid"] == created["artifact_euid"]
    assert (
        service.get_artifact(created["artifact_euid"])["storage_uri"]
        == "s3://bucket-1/reads/r1.fastq.gz"
    )
    assert service.list_artifacts(artifact_type="fastq", producer_system="atlas") == [created]


def test_bootstrap_seeds_and_reads_local_anomalies(service: DeweyService) -> None:
    service.bootstrap()

    anomalies = service.list_anomalies()
    assert len(anomalies) == 3
    assert anomalies[0]["anomaly_id"].startswith("ANM-")
    assert anomalies[0]["source_view_url"].startswith("/ui/anomalies/")

    anomaly = service.get_anomaly(anomalies[0]["anomaly_id"])
    assert anomaly["anomaly_id"] == anomalies[0]["anomaly_id"]
    assert anomaly["severity"] in {"high", "medium", "low"}

    with pytest.raises(DeweyNotFoundError):
        service.get_anomaly("ANM-999999")


def test_import_artifact_and_validation_errors(
    service: DeweyService,
    storage: _FakeStorageClient,
) -> None:
    with pytest.raises(ValueError, match="s3://"):
        service.import_artifact_from_uri(
            artifact_type="fastq",
            source_uri="gs://bucket/object",
            metadata={},
            idempotency_key="idem-import-bad",
        )

    with pytest.raises(ValueError, match="bucket is required"):
        service.register_artifact(
            artifact_type="fastq",
            storage_backend="s3",
            bucket="",
            key="reads/r2.fastq.gz",
            version_id=None,
            size=None,
            checksums=None,
            content_type=None,
            original_filename=None,
            producer_system=None,
            producer_object_euid=None,
            storage_class=None,
            availability_status=None,
            metadata=None,
            idempotency_key="idem-invalid",
        )

    storage.seed_object(
        bucket="bucket-2",
        key="reads/r2.fastq.gz",
        size=256,
        content_type="application/gzip",
    )
    status_code, imported = service.import_artifact_from_uri(
        artifact_type="fastq",
        source_uri="s3://bucket-2/reads/r2.fastq.gz",
        import_mode="reference",
        metadata={"content_type": "application/gzip", "producer_system": "ursa"},
        idempotency_key="idem-import-good",
    )

    assert status_code == 201
    assert imported["bucket"] == "bucket-2"
    assert imported["producer_system"] == "ursa"
    assert imported["storage_status"] == "verified"

    copy_code, copied = service.import_artifact_from_uri(
        artifact_type="fastq",
        source_uri="s3://bucket-2/reads/r2.fastq.gz",
        import_mode="copy",
        lock_after_import=True,
        metadata={"content_type": "application/gzip"},
        idempotency_key="idem-import-copy",
    )

    assert copy_code == 201
    assert copied["bucket"] == "managed-bucket"
    assert copied["import_mode"] == "copy"
    assert copied["retention_mode"] == "GOVERNANCE"


def test_expand_s3_sources_and_build_download_archive(
    service: DeweyService,
    storage: _FakeStorageClient,
) -> None:
    storage.seed_object(
        bucket="bucket-6",
        key="runs/batch/file-1.txt",
        size=4,
        content_type="text/plain",
    )
    storage.seed_object(
        bucket="bucket-6",
        key="runs/batch/file-2.txt",
        size=4,
        content_type="text/plain",
    )

    expanded = service.expand_s3_sources("s3://bucket-6/runs/batch/")
    assert expanded == [
        "s3://bucket-6/runs/batch/file-1.txt",
        "s3://bucket-6/runs/batch/file-2.txt",
    ]

    _, first = service.register_artifact(
        artifact_type="report",
        storage_backend="s3",
        bucket="bucket-6",
        key="runs/batch/file-1.txt",
        version_id=None,
        size=4,
        checksums=None,
        content_type="text/plain",
        original_filename="file-1.txt",
        producer_system=None,
        producer_object_euid=None,
        storage_class=None,
        availability_status=None,
        metadata={"study_id": "ST-6"},
        idempotency_key="idem-archive-artifact-1",
    )
    _, second = service.register_artifact(
        artifact_type="report",
        storage_backend="s3",
        bucket="bucket-6",
        key="runs/batch/file-2.txt",
        version_id=None,
        size=4,
        checksums=None,
        content_type="text/plain",
        original_filename="file-2.txt",
        producer_system=None,
        producer_object_euid=None,
        storage_class=None,
        availability_status=None,
        metadata={"study_id": "ST-6"},
        idempotency_key="idem-archive-artifact-2",
    )

    archive_name, archive_bytes = service.build_artifact_download_archive(
        artifact_euids=[first["artifact_euid"], second["artifact_euid"]],
        naming_mode="dewey",
        include_metadata=True,
    )
    assert archive_name.startswith("dewey-artifacts-")

    with zipfile.ZipFile(io.BytesIO(archive_bytes)) as archive:
        names = set(archive.namelist())
    assert f"{first['artifact_euid']}.txt" in names
    assert f"{first['artifact_euid']}.txt.dewey.yaml" in names
    assert f"{second['artifact_euid']}.txt" in names


def test_service_infers_artifact_type_from_filename_and_allows_na(
    service: DeweyService,
    storage: _FakeStorageClient,
) -> None:
    session_code, upload_session = service.create_upload_session(
        artifact_type="n/a",
        original_filename="variants.vcf.gz",
        content_type="application/gzip",
        producer_system=None,
        producer_object_euid=None,
        metadata={},
        lock_after_import=False,
        idempotency_key="idem-upload-infer",
    )
    assert session_code == 201

    storage.seed_object(
        bucket=upload_session["bucket"],
        key=upload_session["key"],
        size=1024,
        content_type="application/gzip",
    )
    complete_code, artifact = service.complete_upload_session(
        upload_token=upload_session["upload_token"],
        checksums={},
        metadata={},
        idempotency_key="idem-upload-infer-complete",
    )
    assert complete_code == 201
    assert artifact["artifact_type"] == "vcf"
