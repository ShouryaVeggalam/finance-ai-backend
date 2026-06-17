class CelestraError(Exception):
    def __init__(self, message: str, code: str = "CELESTRA_ERROR"):
        self.message = message
        self.code = code
        super().__init__(message)


class NotFoundError(CelestraError):
    def __init__(self, resource: str, identifier: str | None = None):
        msg = f"{resource} not found"
        if identifier:
            msg = f"{resource} '{identifier}' not found"
        super().__init__(msg, "NOT_FOUND")


class UnauthorizedError(CelestraError):
    def __init__(self, message: str = "Unauthorized"):
        super().__init__(message, "UNAUTHORIZED")


class ForbiddenError(CelestraError):
    def __init__(self, message: str = "Forbidden"):
        super().__init__(message, "FORBIDDEN")


class ValidationError(CelestraError):
    def __init__(self, message: str):
        super().__init__(message, "VALIDATION_ERROR")


class ConflictError(CelestraError):
    def __init__(self, message: str):
        super().__init__(message, "CONFLICT")
