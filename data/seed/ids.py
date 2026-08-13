"""Shared synthetic seed payloads for mock services."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from enterprise_domain.seed_ids import SeedIds

ADDRESS_ACME = {
    "line1": "100 Market Street",
    "line2": "Suite 4",
    "city": "San Francisco",
    "state": "CA",
    "postal_code": "94105",
    "country": "US",
}

ADDRESS_GLOBEX = {
    "line1": "500 Innovation Way",
    "city": "Austin",
    "state": "TX",
    "postal_code": "78701",
    "country": "US",
}


def customers() -> dict[str, dict[str, Any]]:
    return {
        str(SeedIds.CUSTOMER_ACME): {
            "id": str(SeedIds.CUSTOMER_ACME),
            "organization_id": str(SeedIds.ORG_ACME),
            "email": "customer@acme-demo.test",
            "full_name": "Acme Customer",
            "external_id": "crm-acme-1",
        },
        str(SeedIds.CUSTOMER_GLOBEX): {
            "id": str(SeedIds.CUSTOMER_GLOBEX),
            "organization_id": str(SeedIds.ORG_GLOBEX),
            "email": "customer@globex-demo.test",
            "full_name": "Globex Customer",
            "external_id": "crm-globex-1",
        },
    }


def orders() -> dict[str, dict[str, Any]]:
    return {
        str(SeedIds.ORDER_ACME_DELAYED): {
            "id": str(SeedIds.ORDER_ACME_DELAYED),
            "organization_id": str(SeedIds.ORG_ACME),
            "customer_id": str(SeedIds.CUSTOMER_ACME),
            "order_number": SeedIds.ORDER_NUMBER_ACME_DELAYED,
            "status": "delayed",
            "shipping_address": deepcopy(ADDRESS_ACME),
            "tracking_number": SeedIds.TRACKING_ACME_DELAYED,
            "version": 1,
            "etag": "1",
        },
        str(SeedIds.ORDER_ACME_OK): {
            "id": str(SeedIds.ORDER_ACME_OK),
            "organization_id": str(SeedIds.ORG_ACME),
            "customer_id": str(SeedIds.CUSTOMER_ACME),
            "order_number": SeedIds.ORDER_NUMBER_ACME_OK,
            "status": "shipped",
            "shipping_address": deepcopy(ADDRESS_ACME),
            "tracking_number": SeedIds.TRACKING_ACME_OK,
            "version": 1,
            "etag": "1",
        },
        str(SeedIds.ORDER_GLOBEX): {
            "id": str(SeedIds.ORDER_GLOBEX),
            "organization_id": str(SeedIds.ORG_GLOBEX),
            "customer_id": str(SeedIds.CUSTOMER_GLOBEX),
            "order_number": SeedIds.ORDER_NUMBER_GLOBEX,
            "status": "shipped",
            "shipping_address": deepcopy(ADDRESS_GLOBEX),
            "tracking_number": SeedIds.TRACKING_GLOBEX,
            "version": 1,
            "etag": "1",
        },
    }


def tracking() -> dict[str, dict[str, Any]]:
    return {
        SeedIds.TRACKING_ACME_DELAYED: {
            "tracking_number": SeedIds.TRACKING_ACME_DELAYED,
            "status": "delayed",
            "status_detail": "Hub exception — package held for scan",
            "delay_reason": "Weather-related hub backlog at OAK",
            "carrier": "mock-carrier",
        },
        SeedIds.TRACKING_ACME_OK: {
            "tracking_number": SeedIds.TRACKING_ACME_OK,
            "status": "in_transit",
            "status_detail": "On time",
            "carrier": "mock-carrier",
        },
        SeedIds.TRACKING_GLOBEX: {
            "tracking_number": SeedIds.TRACKING_GLOBEX,
            "status": "in_transit",
            "status_detail": "On time",
            "carrier": "mock-carrier",
        },
    }
