"""Domain exceptions for FileFerry."""


class FileFerryError(Exception):
    """Base exception for all tool-specific errors."""


class ConfigurationError(FileFerryError):
    """Raised when CLI parameters or runtime config are invalid."""


class NetworkError(FileFerryError):
    """Raised for socket connection/listening errors."""


class ProtocolError(FileFerryError):
    """Raised when peer data does not match protocol expectations."""
