"""UPS-style size tiers, volumetric weight, and tariff hints."""
from __future__ import annotations

from dataclasses import dataclass

from app.models import SizeCategory, ContentCategory

# Domestic express divisor (cm³ → kg), aligned with IATA / UPS volumetric rules.
VOLUMETRIC_DIVISOR = 5000

# ETB base rates by size tier (chargeable kg bands) — override via admin config later.
_TIER_BASE: dict[SizeCategory, float] = {
    SizeCategory.SMALL: 120.0,
    SizeCategory.MEDIUM: 180.0,
    SizeCategory.LARGE: 280.0,
    SizeCategory.OVERSIZED: 450.0,
}
_PER_KG: dict[SizeCategory, float] = {
    SizeCategory.SMALL: 8.0,
    SizeCategory.MEDIUM: 12.0,
    SizeCategory.LARGE: 18.0,
    SizeCategory.OVERSIZED: 25.0,
}
_FRAGILE_SURCHARGE = 1.15
_ELECTRONICS_SURCHARGE = 1.10


@dataclass(frozen=True)
class ClassificationResult:
    size_category: SizeCategory
    volumetric_weight_kg: float
    chargeable_weight_kg: float
    suggested_price: float


def volumetric_weight_kg(length_cm: float, width_cm: float, height_cm: float) -> float:
    if length_cm <= 0 or width_cm <= 0 or height_cm <= 0:
        return 0.0
    return round((length_cm * width_cm * height_cm) / VOLUMETRIC_DIVISOR, 2)


def classify_size(
    length_cm: float | None,
    width_cm: float | None,
    height_cm: float | None,
    weight_kg: float | None = None,
) -> SizeCategory:
    """Tier from longest side + girth (L + 2W + 2H), UPS small-package style."""
    if not length_cm or not width_cm or not height_cm:
        w = weight_kg or 1.0
        if w <= 2:
            return SizeCategory.SMALL
        if w <= 10:
            return SizeCategory.MEDIUM
        if w <= 25:
            return SizeCategory.LARGE
        return SizeCategory.OVERSIZED

    dims = sorted([length_cm, width_cm, height_cm], reverse=True)
    longest, mid, shortest = dims
    girth = longest + 2 * mid + 2 * shortest

    if longest <= 45 and girth <= 100:
        return SizeCategory.SMALL
    if longest <= 60 and girth <= 150:
        return SizeCategory.MEDIUM
    if longest <= 100 and girth <= 250:
        return SizeCategory.LARGE
    return SizeCategory.OVERSIZED


def chargeable_weight(actual_kg: float | None, volumetric_kg: float) -> float:
    actual = max(0.1, float(actual_kg or 0.1))
    return round(max(actual, volumetric_kg), 2)


def suggest_price(
    size_category: SizeCategory,
    chargeable_kg: float,
    content_category: ContentCategory | None = None,
) -> float:
    base = _TIER_BASE[size_category]
    per_kg = max(0, chargeable_kg - 1) * _PER_KG[size_category]
    total = base + per_kg
    if content_category == ContentCategory.FRAGILE:
        total *= _FRAGILE_SURCHARGE
    elif content_category == ContentCategory.ELECTRONICS:
        total *= _ELECTRONICS_SURCHARGE
    return round(total, 2)


def classify_parcel(
    *,
    weight_kg: float | None,
    length_cm: float | None,
    width_cm: float | None,
    height_cm: float | None,
    content_category: ContentCategory | None = None,
) -> ClassificationResult:
    vol = volumetric_weight_kg(length_cm or 0, width_cm or 0, height_cm or 0)
    size = classify_size(length_cm, width_cm, height_cm, weight_kg)
    billable = chargeable_weight(weight_kg, vol)
    price = suggest_price(size, billable, content_category)
    return ClassificationResult(
        size_category=size,
        volumetric_weight_kg=vol,
        chargeable_weight_kg=billable,
        suggested_price=price,
    )
