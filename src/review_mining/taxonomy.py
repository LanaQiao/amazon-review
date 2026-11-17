"""Closed taxonomy and JSON schema for negative-review attribution."""

CAUSES = [
    "quality_durability",
    "performance_functionality",
    "size_fit_design",
    "description_expectation_gap",
    "value_for_money",
    "delivery_packaging",
    "customer_service_return",
    "safety_health",
    "usability_setup",
    "wrong_item_counterfeit",
    "other",
    "unclear",
]

CAUSE_DESCRIPTIONS = {
    "quality_durability": "damaged, poor build/material, wears out or breaks",
    "performance_functionality": "does not work, poor performance, compatibility failure",
    "size_fit_design": "size, fit, comfort, ergonomics or design issue",
    "description_expectation_gap": "does not match listing, photo, claim or expectation",
    "value_for_money": "price, value or perceived worth",
    "delivery_packaging": "shipping, missing parts, package damage or delivery",
    "customer_service_return": "support, warranty, return or refund experience",
    "safety_health": "safety, irritation, allergy or health concern",
    "usability_setup": "installation, instructions or ease of use",
    "wrong_item_counterfeit": "wrong item, suspected counterfeit or used item",
    "other": "a clear negative cause outside this taxonomy",
    "unclear": "insufficient evidence in the review",
}

LABEL_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["items"],
    "properties": {
        "items": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": [
                    "review_id", "primary_cause", "secondary_causes", "is_product_related",
                    "severity", "confidence", "evidence", "rationale",
                ],
                "properties": {
                    "review_id": {"type": "string"},
                    "primary_cause": {"type": "string", "enum": CAUSES},
                    "secondary_causes": {
                        "type": "array", "items": {"type": "string", "enum": CAUSES},
                        "maxItems": 2,
                    },
                    "is_product_related": {"type": "boolean"},
                    "severity": {"type": "integer", "minimum": 1, "maximum": 5},
                    "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                    "evidence": {
                        "type": "array", "items": {"type": "string"}, "maxItems": 2,
                    },
                    "rationale": {"type": "string", "maxLength": 180},
                },
            },
        }
    },
}
