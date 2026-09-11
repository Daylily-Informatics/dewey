"""Explicit owner manifest; identifiers refer only to persisted Dewey artifacts."""

from pathlib import PurePosixPath
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class PackageFile(BaseModel):
    model_config = ConfigDict(extra="forbid")
    artifact_euid: str = Field(min_length=1)
    role: Literal["report", "data", "archive"]
    relative_path: str = Field(min_length=1)
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    size_bytes: int = Field(ge=0, strict=True)

    @model_validator(mode="after")
    def safe_path(self):
        path = PurePosixPath(self.relative_path)
        if (
            path.is_absolute()
            or "\\" in self.relative_path
            or any(p in {"", ".", ".."} for p in self.relative_path.split("/"))
            or any(ord(c) < 32 for c in self.relative_path)
        ):
            raise ValueError("relative_path must be a safe, exact package member path")
        return self


class PackageRegistration(BaseModel):
    model_config = ConfigDict(extra="forbid")
    contract: Literal["dewey.multiqc-package/v1"]
    complete_data_package: Literal[True]
    label: str = Field(min_length=1)
    files: list[PackageFile] = Field(min_length=2, max_length=10000)

    @model_validator(mode="after")
    def complete_shape(self):
        roles = [f.role for f in self.files]
        if roles.count("report") != 1:
            raise ValueError("Exactly one report is required")
        if not (
            (roles.count("archive") == 1 and roles.count("data") == 0)
            or (roles.count("archive") == 0 and roles.count("data") >= 1)
        ):
            raise ValueError("Supply one complete ZIP archive OR all data files")
        if len({f.artifact_euid for f in self.files}) != len(self.files):
            raise ValueError("Duplicate artifact membership")
        if len({f.relative_path.casefold() for f in self.files}) != len(self.files):
            raise ValueError("Duplicate package paths")
        return self


class ResolveMultiqcRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    kind: Literal["artifact", "artifact_set"]
    euid: str = Field(min_length=1)
