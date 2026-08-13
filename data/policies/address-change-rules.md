# Acme Retail — Address Change Rules (FICTIONAL)

**Document ID:** POL-ADDR-002  
**Organization:** Acme Retail (synthetic)  
**Effective:** 2026-01-01  
**Classification:** Internal support policy — demo only

## 1. Scope

Rules for changing the delivery address on open Acme Retail demo orders.

## 2. Hard requirements

1. The requester must be the order’s customer (or a support agent acting with documented consent).
2. The order status must be `paid` or `processing` — **not** `shipped`, `out_for_delivery`, or `delivered`.
3. Destination must be within the contiguous fictional “Demo States” region.
4. Every address change requires **explicit human approval** in the product UI before ERP mutation.
5. Mutations use an idempotency key; retries must not create duplicate changes.

## 3. Allowed changes

- Street number / street name corrections before carrier handoff.
- Apartment / unit additions when the postal code is unchanged.
- City spelling corrections when ZIP remains valid.

## 4. Denied changes

- Changes after `shipped` status (create carrier intercept ticket instead — escalate).
- Cross-border / international redirects in this demo.
- Changing address to a freight-only PO Box for parcel SKUs.
- Requests that alter billing address (out of scope for this assistant).

## 5. Approval payload

The approval card must show:

- Order ID
- Previous address hash/summary
- Proposed address fields
- Policy decision (`allow` / `deny` / `escalate`)
- Evidence sources (ERP status + policy section)

## 6. Post-approval

1. Revalidate order status and authorization.
2. Call ERP address-change with `Idempotency-Key`.
3. Verify by reading the order.
4. Write an audit event and optional ticketing note.
