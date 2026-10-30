"""Errors raised by capture, replay, and the regression suite."""


class UndoomError(Exception):
    """Base class for expected Undoom failures."""


class SchemaVersionError(UndoomError):
    """A stored document was written by a different schema generation."""


class ReplayError(UndoomError):
    """A replay could not be prepared or the model provider failed."""


class PromoteError(UndoomError):
    """A replay cannot become a regression case."""


class TraceImportError(UndoomError):
    """An OpenTelemetry document cannot become a cassette-ready run."""
