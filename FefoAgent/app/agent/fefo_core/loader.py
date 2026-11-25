"""Single entry point for reading data files.

``load_tables(data_dir)`` is the ONLY place in ``fefo_core`` that opens data
files. A DynamoDB source can later be added here (same ``RawTables`` result)
without touching validate, features, forecast or risk.

Layout under ``data_dir``: ``raw/{products,dealers,dealer_rules,shipments,
inventory_snapshot,inbound_plan,calendar}.csv`` and ``config/params.json``.
``inbound_plan.csv`` is optional; every other file is required.

Row numbers used in error messages and by ``validate`` are file line numbers
(header = 1, first data row = 2); ``RawTables`` lists are 0-based, so list
index ``i`` is file row ``i + 2``.
"""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any, Callable

Row = dict[str, Any]


class LoadError(ValueError):
    """A data file is missing a column or holds a value that cannot be parsed."""


@dataclass
class RawTables:
    products: list[Row] = field(default_factory=list)
    dealers: list[Row] = field(default_factory=list)
    dealer_rules: list[Row] = field(default_factory=list)
    shipments: list[Row] = field(default_factory=list)
    inventory_snapshot: list[Row] = field(default_factory=list)
    inbound_plan: list[Row] = field(default_factory=list)
    calendar: list[Row] = field(default_factory=list)
    params: dict[str, Any] = field(default_factory=dict)


def _str(v: str) -> str:
    return v.strip()


def _int(v: str) -> int:
    return int(v.strip())


def _float(v: str) -> float:
    return float(v.strip())


def _date(v: str) -> date:
    return date.fromisoformat(v.strip())


def _bool(v: str) -> bool:
    s = v.strip().lower()
    if s in ("true", "1", "yes"):
        return True
    if s in ("false", "0", "no", ""):
        return False
    raise ValueError(f"not a boolean: {v!r}")


def _id_list(v: str) -> list[str]:
    return [p.strip() for p in v.split(";") if p.strip()]


# file -> {column: parser}. Column names follow TEAM_PLAN section 3 / data-gen.
_SCHEMAS: dict[str, dict[str, Callable[[str], Any]]] = {
    "products": {
        "sku_id": _str, "sku_name": _str, "category": _str,
        "shelf_life_days": _int, "unit_cost_try": _float,
        "unit_price_try": _float, "unit_weight_kg": _float,
        "supplier_id": _str, "supplier_return_allowed": _bool,
    },
    "dealers": {
        "dealer_id": _str, "dealer_name": _str, "region": _str,
        "dealer_type": _str,
    },
    "dealer_rules": {
        "dealer_id": _str, "category": _str, "shelf_pull_days": _int,
        "min_days_on_receipt": _int,
    },
    "shipments": {
        "date": _date, "dealer_id": _str, "sku_id": _str, "lot_id": _str,
        "qty_units": _int,
    },
    "inventory_snapshot": {
        "sku_id": _str, "lot_id": _str, "qty_units": _int,
        "expiry_date": _date, "received_date": _date, "location_bin": _str,
    },
    "inbound_plan": {
        "expected_date": _date, "sku_id": _str, "lot_id": _str,
        "qty_units": _int, "expiry_date": _date,
    },
    "calendar": {
        "date": _date, "is_campaign_day": _bool,
        "campaign_sku_ids": _id_list, "stockout_sku_ids": _id_list,
    },
}

_OPTIONAL = {"inbound_plan"}


def _read_csv(path: Path, name: str) -> list[Row]:
    schema = _SCHEMAS[name]
    rows: list[Row] = []
    with path.open("r", encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        missing = [c for c in schema if c not in (reader.fieldnames or [])]
        if missing:
            raise LoadError(f"{path.name}: missing columns {missing}")
        for line_no, raw in enumerate(reader, start=2):
            row: Row = {}
            for col, parse in schema.items():
                try:
                    row[col] = parse(raw[col] if raw[col] is not None else "")
                except (ValueError, TypeError) as exc:
                    raise LoadError(
                        f"{path.name} row {line_no} column {col}: {exc}"
                    ) from exc
            rows.append(row)
    return rows


def load_tables(data_dir: str | Path) -> RawTables:
    """Read every data file under ``data_dir`` into a ``RawTables``."""
    base = Path(data_dir)
    tables = RawTables()
    for name in _SCHEMAS:
        path = base / "raw" / f"{name}.csv"
        if not path.is_file():
            if name in _OPTIONAL:
                continue
            raise FileNotFoundError(f"required data file not found: {path}")
        setattr(tables, name, _read_csv(path, name))
    params_path = base / "config" / "params.json"
    if not params_path.is_file():
        raise FileNotFoundError(f"required data file not found: {params_path}")
    with params_path.open("r", encoding="utf-8") as fh:
        try:
            tables.params = json.load(fh)
        except json.JSONDecodeError as exc:
            raise LoadError(f"params.json: {exc}") from exc
    return tables
