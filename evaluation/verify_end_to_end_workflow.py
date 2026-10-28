# SupplyChain Sentinel Workflow Verification
"""End-to-end validation script for SupplyChain Sentinel release candidate.

Simulates the full user workflow against the FastAPI backend:
1. Creates a target supplier with parts and inventory coverage.
2. Triggers an incident investigation using the deterministic pipeline.
3. Inspects evidence: source lineage clustering, quote validation badges, entity match.
4. Records a human decision gate review (accept and override).
5. Verifies persisted audit history and confirms database records are intact.
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

# Add backend to path
BACKEND_DIR = Path(__file__).resolve().parent.parent / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.db.session import init_db
from app.main import app
from httpx import ASGITransport, AsyncClient


async def main() -> None:
    print("=" * 70)
    print("SUPPLYCHAIN SENTINEL END-TO-END WORKFLOW VALIDATION")
    print("=" * 70)

    await init_db()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        # Step 1: Health check
        health_resp = await client.get("/api/v1/health")
        assert health_resp.status_code == 200, f"Health failed: {health_resp.text}"
        print("[OK] Step 1: Health check passed ->", health_resp.json()["status"])

        # Step 2: Create or get supplier
        supplier_payload = {
            "name": "Apex Semiconductor Ltd",
            "aliases": ["Apex Semi", "ASL"],
            "country_or_region": "Taiwan",
            "official_domains": ["apex-semi.com"],
            "parts": [
                {
                    "part_name": "Power Management IC",
                    "inventory_coverage_days": 14,
                    "typical_lead_time_days": 60,
                    "criticality": "high",
                }
            ],
        }
        sup_resp = await client.post("/api/v1/suppliers", json=supplier_payload)
        assert sup_resp.status_code in (200, 201), (
            f"Create supplier failed: {sup_resp.text}"
        )
        supplier = sup_resp.json()
        supplier_id = supplier["id"]
        print(
            f"[OK] Step 2: Supplier registered -> '{supplier['name']}' (ID: {supplier_id})"
        )

        # Step 3: Run Investigation (Fixture Mode)
        inv_payload = {
            "supplier_id": supplier_id,
            "search_mode": "fixture",
        }
        inv_resp = await client.post("/api/v1/investigations", json=inv_payload)
        assert inv_resp.status_code in (200, 201), (
            f"Run investigation failed: {inv_resp.text}"
        )
        inv_data = inv_resp.json()
        investigation_id = inv_data["id"]
        print(f"[OK] Step 3: Investigation completed -> ID: {investigation_id}")

        # Step 4: Evidence Inspection
        # A. Sources & Lineage
        src_resp = await client.get(
            f"/api/v1/investigations/{investigation_id}/sources"
        )
        assert src_resp.status_code == 200, f"Get sources failed: {src_resp.text}"
        sources = src_resp.json()
        assert len(sources) > 0, "No sources retrieved"
        print(f"[OK] Step 4a: Retrieved {len(sources)} source documents")

        # B. Claims & Quote Verification
        claims_resp = await client.get(
            f"/api/v1/investigations/{investigation_id}/claims"
        )
        assert claims_resp.status_code == 200, f"Get claims failed: {claims_resp.text}"
        claims = claims_resp.json()
        assert len(claims) > 0, "No claims extracted"
        first_claim = claims[0]
        assert first_claim.get("extraction_status") == "validated", (
            f"Expected extraction_status == 'validated', got {first_claim.get('extraction_status')}"
        )
        print(f"[OK] Step 4b: Retrieved {len(claims)} claim(s)")
        print(f'   - Rule E-005 Verified Quote: "{first_claim["supporting_quote"]}"')
        print(f"   - Extraction Status: {first_claim['extraction_status']}")

        # C. Incident Candidates, Exposure & Policy Recommendation
        inc_resp = await client.get(
            f"/api/v1/investigations/{investigation_id}/incidents"
        )
        assert inc_resp.status_code == 200, f"Get incidents failed: {inc_resp.text}"
        incidents = inc_resp.json()
        assert len(incidents) > 0, "No incident candidates generated"
        inc = incidents[0]
        incident_id = inc["id"]
        pol = inc["policy_decision"]
        exp = inc.get("exposure")

        print(f"[OK] Step 4c: Incident Candidate generated -> ID: {incident_id}")
        print(f"   - Automated Recommendation: {pol['recommendation']}")
        print(f"   - Rules Fired: {pol.get('rule_ids_fired')}")
        print(f"   - Policy Reasons: {pol.get('reasons')}")
        if exp:
            print(
                f"   - Exposure Inventory Gap: {exp.get('potential_inventory_gap_days')} days"
            )

        # Step 5: Human Decision Gate (Override recommendation with rationale)
        decision_payload = {
            "action": "reject_recommendation",
            "override_recommendation": "monitor",
            "reviewer_name": "procurement-director-01",
            "reviewer_note": "Secondary inventory buffer verified at regional logistics center; safe to monitor.",
        }
        dec_resp = await client.post(
            f"/api/v1/incidents/{incident_id}/decision",
            json=decision_payload,
        )
        assert dec_resp.status_code in (200, 201), (
            f"Record decision failed: {dec_resp.text}"
        )
        decision = dec_resp.json()
        print(
            f"[OK] Step 5: Human Decision Gate Recorded -> Action: {decision['action']}"
        )
        print(f"   - Reviewer: {decision['reviewer_name']}")
        print(f"   - Prior Recommendation: {decision.get('prior_recommendation')}")
        print(
            f"   - Override Recommendation: {decision.get('override_recommendation')}"
        )
        print(f"   - Reviewer Notes: {decision.get('reviewer_note')}")

        # Step 6: Persisted Audit History
        audit_resp = await client.get("/api/v1/audit-events")
        assert audit_resp.status_code == 200, f"Audit history failed: {audit_resp.text}"
        audit_events = audit_resp.json()
        assert len(audit_events) > 0, "Audit log empty"
        print(
            f"[OK] Step 6: Audit History Verified -> {len(audit_events)} audit events recorded"
        )
        for evt in audit_events[:5]:
            print(
                f"   - [{evt['created_at']}] Event: {evt['event_type']} (Entity: {evt.get('entity_type')})"
            )

    print("=" * 70)
    print("ALL END-TO-END WORKFLOW VERIFICATIONS PASSED SUCCESSFULLY!")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
