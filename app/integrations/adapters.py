"""External system integration adapters."""

from abc import ABC, abstractmethod
from typing import Any


class IntegrationAdapter(ABC):
    name: str = "base"

    @abstractmethod
    async def connect(self, credentials: dict[str, Any]) -> bool:
        pass

    @abstractmethod
    async def sync(self, company_id: str) -> dict[str, Any]:
        pass


class BankingIntegration(IntegrationAdapter):
    name = "banking"

    async def connect(self, credentials: dict[str, Any]) -> bool:
        return bool(credentials.get("api_key"))

    async def sync(self, company_id: str) -> dict[str, Any]:
        return {"status": "synced", "transactions": 0}


class ERPIntegration(IntegrationAdapter):
    name = "erp"

    async def connect(self, credentials: dict[str, Any]) -> bool:
        return bool(credentials.get("endpoint"))

    async def sync(self, company_id: str) -> dict[str, Any]:
        return {"status": "synced", "records": 0}


class PaymentGatewayIntegration(IntegrationAdapter):
    name = "payment_gateway"

    async def connect(self, credentials: dict[str, Any]) -> bool:
        return bool(credentials.get("merchant_id"))

    async def sync(self, company_id: str) -> dict[str, Any]:
        return {"status": "synced", "payments": 0}


INTEGRATIONS: dict[str, type[IntegrationAdapter]] = {
    "banking": BankingIntegration,
    "erp": ERPIntegration,
    "payment_gateway": PaymentGatewayIntegration,
}
