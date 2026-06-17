import uuid
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import PurchaseRequest, Vendor, VendorContract
from app.repositories.domain_repository import VendorRepository


class ProcurementEngine:
    """Vendor analysis, contract tracking, spend optimization, purchase monitoring."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.vendor_repo = VendorRepository(session)

    async def analyze_vendor_spend(self, company_id: uuid.UUID) -> list[dict]:
        vendors = await self.vendor_repo.list_by_company(company_id, limit=100)
        return [
            {
                "vendor_id": str(v.id),
                "name": v.name,
                "total_spend": float(v.total_spend),
                "risk_score": float(v.risk_score) if v.risk_score else None,
                "category": v.category,
            }
            for v in sorted(vendors, key=lambda x: x.total_spend, reverse=True)
        ]

    async def detect_savings_opportunities(self, company_id: uuid.UUID) -> list[dict]:
        vendors = await self.analyze_vendor_spend(company_id)
        opportunities = []
        for v in vendors:
            if v["total_spend"] > 10000 and (v["risk_score"] is None or v["risk_score"] < 30):
                opportunities.append(
                    {
                        "vendor_id": v["vendor_id"],
                        "vendor_name": v["name"],
                        "potential_savings_pct": 10,
                        "estimated_savings": v["total_spend"] * 0.1,
                        "recommendation": "Renegotiate contract or consolidate spend",
                    }
                )
        return opportunities

    async def vendor_risk_alerts(self, company_id: uuid.UUID) -> list[dict]:
        result = await self.session.execute(
            select(Vendor).where(
                Vendor.company_id == company_id,
                Vendor.risk_score.isnot(None),
                Vendor.risk_score >= Decimal("70"),
            )
        )
        return [
            {
                "vendor_id": str(v.id),
                "name": v.name,
                "risk_score": float(v.risk_score),
                "alert": "High vendor risk detected",
            }
            for v in result.scalars().all()
        ]

    async def expiring_contracts(self, company_id: uuid.UUID, days: int = 90) -> list[dict]:
        from datetime import date, timedelta

        cutoff = date.today() + timedelta(days=days)
        result = await self.session.execute(
            select(VendorContract).where(
                VendorContract.company_id == company_id,
                VendorContract.end_date <= cutoff,
                VendorContract.status == "active",
            )
        )
        return [
            {
                "contract_id": str(c.id),
                "contract_number": c.contract_number,
                "end_date": c.end_date.isoformat(),
                "total_value": float(c.total_value),
            }
            for c in result.scalars().all()
        ]

    async def procurement_health_score(self, company_id: uuid.UUID) -> Decimal:
        pending = await self.session.execute(
            select(func.count()).select_from(PurchaseRequest).where(
                PurchaseRequest.company_id == company_id,
                PurchaseRequest.status == "pending",
            )
        )
        pending_count = pending.scalar_one()
        high_risk = len(await self.vendor_risk_alerts(company_id))
        score = Decimal("100") - Decimal(str(pending_count * 2)) - Decimal(str(high_risk * 10))
        return max(Decimal("0"), score).quantize(Decimal("0.01"))
