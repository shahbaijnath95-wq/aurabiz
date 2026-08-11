"""Custom exception classes for the application."""

from fastapi import HTTPException, status


# ── Base ──

class AppException(HTTPException):
    """Base exception for the application."""
    def __init__(self, detail: str, status_code: int = 400):
        super().__init__(status_code=status_code, detail=detail)


# ── Auth ──

class UnauthorizedException(AppException):
    def __init__(self, detail: str = "Authentication required"):
        super().__init__(detail=detail, status_code=status.HTTP_401_UNAUTHORIZED)


class ForbiddenException(AppException):
    def __init__(self, detail: str = "Access denied"):
        super().__init__(detail=detail, status_code=status.HTTP_403_FORBIDDEN)


# ── Not Found ──

class NotFoundException(AppException):
    def __init__(self, resource: str = "Resource"):
        super().__init__(detail=f"{resource} nahi mila", status_code=status.HTTP_404_NOT_FOUND)


class BusinessNotFoundException(NotFoundException):
    def __init__(self):
        super().__init__(resource="Business")


class CustomerNotFoundException(NotFoundException):
    def __init__(self):
        super().__init__(resource="Customer")


class OrderNotFoundException(NotFoundException):
    def __init__(self):
        super().__init__(resource="Order")


class ProductNotFoundException(NotFoundException):
    def __init__(self):
        super().__init__(resource="Product")


# ── Validation ──

class ValidationException(AppException):
    def __init__(self, detail: str):
        super().__init__(detail=detail, status_code=status.HTTP_422_UNPROCESSABLE_ENTITY)


class DuplicateException(AppException):
    def __init__(self, detail: str):
        super().__init__(detail=detail, status_code=status.HTTP_409_CONFLICT)


# ── Business Logic ──

class InsufficientStockException(AppException):
    def __init__(self, product_name: str, available: int, requested: int):
        super().__init__(
            detail=f"'{product_name}' mein sirf {available} stock hai, {requested} nahi mangwaya ja sakta",
            status_code=status.HTTP_400_BAD_REQUEST,
        )


class PaymentFailedException(AppException):
    def __init__(self, detail: str = "Payment process fail ho gaya"):
        super().__init__(detail=detail, status_code=status.HTTP_402_PAYMENT_REQUIRED)


class WhatsAppNotConnectedException(AppException):
    def __init__(self):
        super().__init__(detail="WhatsApp connected nahi hai", status_code=status.HTTP_503_SERVICE_UNAVAILABLE)


class AIProviderException(AppException):
    def __init__(self, provider: str, detail: str = "AI service temporarily unavailable"):
        super().__init__(
            detail=f"{provider}: {detail}",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        )


class RateLimitException(AppException):
    def __init__(self, detail: str = "Bahut zyada requests ho rahi hain. Thodi der baad try karein."):
        super().__init__(detail=detail, status_code=status.HTTP_429_TOO_MANY_REQUESTS)
