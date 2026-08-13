# Acme Retail — Shipping Delay Policy (FICTIONAL)

**Document ID:** POL-SHIP-001  
**Organization:** Acme Retail (synthetic)  
**Effective:** 2026-01-01  
**Classification:** Internal support policy — demo only

## 1. Purpose

This fictional policy explains how support agents and the AI assistant should explain delayed shipments for Acme Retail demo orders.

## 2. Definitions

- **Carrier scan gap:** No scan for more than 48 hours after the last facility scan.
- **Weather hold:** Carrier-reported weather exception code `WX-HOLD`.
- **Merchant delay:** Order not handed to carrier within promised ship-by date.

## 3. Customer-facing explanation rules

1. Always cite the specific delay reason code from the carrier tool when available.
2. If multiple reasons exist, prefer the most recent carrier exception.
3. Do not invent compensation; only reference section 5 when a documented credit applies.
4. If carrier and ERP disagree, escalate — do not pick a narrative.

## 4. Standard delay messages

### 4.1 Weather hold

Inform the customer that delivery is paused due to a weather exception, quote the ETA range from the carrier tool, and avoid promising a calendar day unless the carrier provides one.

### 4.2 Scan gap

Explain that the package has not received a new scan within 48 hours, that investigation is open, and that a ticket should be created if the gap exceeds 72 hours.

### 4.3 Merchant delay

Explain that the order missed the merchant ship-by date and provide the revised ship date from ERP when present.

## 5. Credits (fictional)

Credits are **not** auto-issued by the assistant. Supervisors may approve a goodwill credit of up to **$15** for delays exceeding **5 business days** after the original ETA. The assistant must escalate rather than promise credits.

## 6. Prohibited statements

- Guaranteeing delivery by a specific hour without carrier ETA.
- Blaming a named employee.
- Disclosing another customer’s shipment details.
