"""Custom exceptions for Looker provisioning."""


class ProvisioningError(Exception):
    """Raised when Looker provisioning operations fail."""


class ValidationError(Exception):
    """Raised when input validation fails."""
