import json

import pytest

from backend.app.ai_skills.okx_market_reading import (
    compile_okx_market_reading_context,
    okx_market_reading_metadata,
    validate_okx_market_reading_profile,
)


def test_okx_market_reading_profile_is_stable_and_public_read_only():
    first = okx_market_reading_metadata()
    second = okx_market_reading_metadata()
    context = compile_okx_market_reading_context()

    assert first == second
    assert first["id"] == "okx-market-reading"
    assert first["dataPolicy"] == "public-read-only"
    assert first["upstream"]["commit"] == "9c180cc1e9911a1ca44c0df5cc7509dba5bb7697"
    assert "okx_cli_execution" in context["prohibitedCapabilities"]
    assert "orders" in context["prohibitedCapabilities"]
    assert "fixed_trends_15m_1H_1D" in context["allowedEvidence"]
    assert all("okx market" not in rule.lower() for rule in context["rules"])
    assert json.dumps(context, ensure_ascii=False)


def test_okx_market_reading_profile_rejects_missing_read_only_protection():
    profile = {
        "id": "okx-market-reading",
        "profileVersion": 1,
        "upstream": {"repository": "okx/agent-skills", "path": "skills/okx-cex-market/SKILL.md", "version": "1.4.8", "commit": "abc", "license": "MIT"},
        "dataPolicy": "public-read-only",
        "allowedEvidence": ["ticker"],
        "prohibitedCapabilities": ["orders"],
        "instructions": ["只读"],
    }

    with pytest.raises(ValueError, match="只读保护"):
        validate_okx_market_reading_profile(profile)
