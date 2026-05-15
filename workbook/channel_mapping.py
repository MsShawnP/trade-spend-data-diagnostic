"""Retailer-to-channel mapping — single source of truth."""

CHANNEL_RATE_COLS: dict[str, str] = {
    "Walmart": "trade_spend_pct_walmart",
    "Costco": "trade_spend_pct_costco",
    "Whole Foods": "trade_spend_pct_whole_foods",
    "UNFI": "trade_spend_pct_unfi",
    "DTC": "trade_spend_pct_dtc",
    "Regional": "trade_spend_pct_regional",
}

RETAILER_TO_CHANNEL: dict[str, str] = {
    "Walmart": "Walmart",
    "Costco": "Costco",
    "Whole Foods": "Whole Foods",
    "UNFI": "UNFI",
    "DTC": "DTC",
    "Green Basket Market": "Regional",
    "Southside Grocers": "Regional",
    "Prairie Provisions": "Regional",
    "Mountain Pantry Co": "Regional",
    "Harbor Fresh": "Regional",
    "KeHE": "Distributor",
}

REGIONAL_RETAILERS: list[str] = [
    r for r, ch in RETAILER_TO_CHANNEL.items() if ch == "Regional"
]

CHANNEL_DISPLAY_ORDER: list[str] = [
    "Walmart", "Costco", "Whole Foods", "UNFI", "Regional", "DTC", "Distributor",
]
