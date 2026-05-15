"""Deduction taxonomy — bucket, addressability, and defense per deduction type."""

DEDUCTION_TAXONOMY: dict[str, dict] = {
    "short_ship": {
        "bucket": "Probable Waste",
        "addressable": True,
        "defense": "Verify against BOL and shipping records — many are rebuttable",
    },
    "label_fine": {
        "bucket": "Probable Waste",
        "addressable": True,
        "defense": "Labeling compliance failures — fixable with updated processes",
    },
    "late_delivery": {
        "bucket": "Probable Waste",
        "addressable": True,
        "defense": "Track against carrier SLAs — some are carrier fault, not manufacturer",
    },
    "spoilage": {
        "bucket": "Probable Waste",
        "addressable": True,
        "defense": "Audit against shelf-life data and retailer handling procedures",
    },
    "damaged": {
        "bucket": "Probable Waste",
        "addressable": True,
        "defense": "Audit damage claims against packaging specs and carrier handling",
    },
    "pallet_fine": {
        "bucket": "Probable Waste",
        "addressable": True,
        "defense": "Compliance failure — fixable with warehouse process changes",
    },
    "vague": {
        "bucket": "Unknown",
        "addressable": True,
        "defense": "No clear basis — highest priority for investigation and dispute",
    },
    "slotting": {
        "bucket": "Contractual",
        "addressable": False,
        "defense": "Negotiated shelf-access fee — verify against contract terms",
    },
    "promo_billback": {
        "bucket": "Contractual",
        "addressable": False,
        "defense": "Authorized promotional activity — verify against promo calendar",
    },
}

BUCKET_DISPLAY_ORDER = ["Probable Waste", "Unknown", "Contractual"]


def get_taxonomy(deduction_type: str) -> dict:
    return DEDUCTION_TAXONOMY.get(deduction_type, {
        "bucket": "Unknown",
        "addressable": True,
        "defense": "Unmapped deduction type — investigate",
    })
