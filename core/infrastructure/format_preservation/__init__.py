"""Format-preserving artifact generation for de-identification outputs."""

from .artifact_writer import DeidentifiedArtifact, build_deidentified_artifact

__all__ = ["DeidentifiedArtifact", "build_deidentified_artifact"]
