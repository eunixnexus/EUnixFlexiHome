"""agent.py

Agent model updated for the multi-household main_simulation.py flow.

Design goals
- Backwards compatible with the legacy constructor:
    Agent(user: str, unit_area: str, area: str)
- Compatible with the new config-driven constructor used in main_simulation.py:
    Agent({
        "agent_name": "...",
        "agent_type": "buyer"|"seller"|"battery"|...,
        "unit_area": "...",
        "household_id": "...",
        "area": {"location": "...", "bus": "..."}  # optional
        "asset_id": "..."
        "asset_category": "load"|"gen"|"storage"
        "asset_type": "demand"|"pv"|"battery"|...
    })

This file intentionally keeps the order payload schema consistent with the legacy
implementation so downstream market/matching components continue to work.
"""

from __future__ import annotations

from dataclasses import dataclass
from random import uniform
from typing import Any, Dict, Optional, Union
import uuid


def _uuid_from_name(name: str) -> str:
    """Deterministic UUID (stable across runs) for a given agent name."""
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, name))


@dataclass(frozen=True)
class AgentIdentity:
    agent_name: str
    agent_type: str
    unit_area: str
    household_id: Optional[str] = None
    area: Optional[Dict[str, Any]] = None
    asset_id: Optional[str] = None
    asset_category: Optional[str] = None
    asset_type: Optional[str] = None


class Agent:
    """Market participant agent (buyer/seller)."""

    def __init__(self, user: Union[str, Dict[str, Any]], unit_area: Optional[str] = None, area: Optional[Any] = None):
        # --- New-style dict constructor ---
        if isinstance(user, dict):
            agent_name = user.get("agent_name") or user.get("User") or user.get("user") or "agent"
            agent_type = user.get("agent_type") or user.get("Type") or user.get("type") or "buyer"
            unit_area_val = user.get("unit_area") or user.get("Unit_area") or unit_area or "DEFAULT"
            household_id = user.get("household_id") or user.get("household") or None
            area_val = user.get("area") if isinstance(user.get("area"), dict) else None

            asset_id = user.get("asset_id")
            asset_category = user.get("asset_category")
            asset_type = user.get("asset_type")

            self.identity = AgentIdentity(
                agent_name=str(agent_name),
                agent_type=str(agent_type),
                unit_area=str(unit_area_val),
                household_id=str(household_id) if household_id is not None else None,
                area=area_val,
                asset_id=str(asset_id) if asset_id is not None else None,
                asset_category=str(asset_category) if asset_category is not None else None,
                asset_type=str(asset_type) if asset_type is not None else None,
            )

            self.user = self.identity.agent_name
            self.unit_area = self.identity.unit_area
            self.area = self.identity.area if self.identity.area is not None else area
            self.userID = _uuid_from_name(self.identity.agent_name)
            return

        # --- Legacy constructor ---
        inferred_household_id = str(user).split("_", 1)[0] if "_" in str(user) else None

        self.identity = AgentIdentity(
            agent_name=str(user),
            agent_type="buyer",
            unit_area=str(unit_area) if unit_area is not None else "DEFAULT",
            household_id=inferred_household_id,
            area={"location": area} if area is not None and not isinstance(area, dict) else (area if isinstance(area, dict) else None),
            asset_id=str(user),
            asset_category=None,
            asset_type=None,
        )
        self.user = self.identity.agent_name
        self.unit_area = self.identity.unit_area
        self.area = self.identity.area
        self.userID = _uuid_from_name(self.identity.agent_name)

    # -------------------------
    # Pricing hooks
    # -------------------------
    def _default_bid_price(self) -> float:
        return round(uniform(20, 30), 2)

    def _default_offer_price(self) -> float:
        return round(uniform(5, 15), 2)

    # -------------------------
    # Order builders
    # -------------------------
    def _build_order(self, simu_row, *, is_bid: bool, price: Optional[float] = None) -> Dict[str, Any]:
        if price is None:
            price = self._default_bid_price() if is_bid else self._default_offer_price()

        row = simu_row.iloc[0] if hasattr(simu_row, "iloc") else simu_row

        dt = row["Datetime"]
        energy = row["Energy"]

        payload = {
            "User": self.user,
            "User_id": self.userID,
            "Unit_area": self.unit_area,
            "Order_id": str(uuid.uuid4()),
            "energy_qty": float(energy),
            "energy_rate": float(price),
            "bid-offer-time": dt.isoformat() if hasattr(dt, "isoformat") else str(dt),
            "delivery-time": dt.isoformat() if hasattr(dt, "isoformat") else str(dt),
            "Type": True if is_bid else False,
            "area": self.area,
        }
        
     
        if self.identity.household_id is not None:
            payload["household_id"] = self.identity.household_id

        payload["agent_name"] = self.identity.agent_name
        payload["agent_type"] = self.identity.agent_type

        if self.identity.asset_id is not None:
            payload["asset_id"] = self.identity.asset_id
        if self.identity.asset_category is not None:
            payload["asset_category"] = self.identity.asset_category
        if self.identity.asset_type is not None:
            payload["asset_type"] = self.identity.asset_type

        return payload

    def bidPrice(self, simu_row, price: Optional[float] = None) -> Dict[str, Any]:
        return self._build_order(simu_row, is_bid=True, price=price)

    def offerPrice(self, simu_row, price: Optional[float] = None) -> Dict[str, Any]:
        return self._build_order(simu_row, is_bid=False, price=price)

    def make_order(self, simu_row, *, side: str, price: Optional[float] = None) -> Dict[str, Any]:
        side_l = side.lower()
        if side_l in ("bid", "buy", "buyer"):
            return self.bidPrice(simu_row, price=price)
        if side_l in ("offer", "sell", "seller"):
            return self.offerPrice(simu_row, price=price)
        raise ValueError(f"Unknown side={side!r}. Expected bid/offer.")