"""Stable synthetic IDs shared by API seed and mock services."""

from __future__ import annotations

from uuid import UUID


class SeedIds:
    """Fixed UUIDs for reproducible demos and tests."""

    ORG_ACME = UUID("11111111-1111-1111-1111-111111111111")
    ORG_GLOBEX = UUID("22222222-2222-2222-2222-222222222222")

    USER_CUSTOMER_ACME = UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaa0001")
    USER_AGENT_ACME = UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaa0002")
    USER_SUPERVISOR_ACME = UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaa0003")
    USER_ADMIN_ACME = UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaa0004")
    USER_CUSTOMER_GLOBEX = UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbb0001")

    CUSTOMER_ACME = UUID("cccccccc-cccc-cccc-cccc-cccccccc0001")
    CUSTOMER_GLOBEX = UUID("cccccccc-cccc-cccc-cccc-cccccccc0002")

    ORDER_ACME_DELAYED = UUID("dddddddd-dddd-dddd-dddd-dddddddd0001")
    ORDER_ACME_OK = UUID("dddddddd-dddd-dddd-dddd-dddddddd0002")
    ORDER_GLOBEX = UUID("dddddddd-dddd-dddd-dddd-dddddddd0003")

    SHIPMENT_ACME_DELAYED = UUID("eeeeeeee-eeee-eeee-eeee-eeeeeeee0001")
    SHIPMENT_ACME_OK = UUID("eeeeeeee-eeee-eeee-eeee-eeeeeeee0002")
    SHIPMENT_GLOBEX = UUID("eeeeeeee-eeee-eeee-eeee-eeeeeeee0003")

    ORDER_NUMBER_ACME_DELAYED = "ACM-10001"
    ORDER_NUMBER_ACME_OK = "ACM-10002"
    ORDER_NUMBER_GLOBEX = "GLX-20001"

    TRACKING_ACME_DELAYED = "1Z999AA10123456784"
    TRACKING_ACME_OK = "1Z999AA10123456785"
    TRACKING_GLOBEX = "1Z999BB20234567890"
