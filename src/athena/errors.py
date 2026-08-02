class AthenaError(RuntimeError):
    """Base error for actionable Athena failures."""


class ConfigurationError(AthenaError):
    """Configuration is invalid or incompatible."""


class WorkspaceViolation(AthenaError):
    """A path escaped the configured workspace boundary."""


class IndexCompatibilityError(AthenaError):
    """The on-disk index was created by an incompatible schema."""


class EvaluationError(AthenaError):
    """An evaluation dataset or release gate is invalid."""


class TokenBudgetError(AthenaError):
    """A serialized context result cannot fit its declared hard token budget."""
