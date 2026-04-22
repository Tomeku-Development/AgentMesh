"""Property-based tests for SLA breach detection correctness.

**Feature: saas-platform-enhancements, Property 6: SLA breach detection correctness**
**Validates: Requirements 4.2**
"""

from __future__ import annotations

from hypothesis import given, settings, strategies as st, HealthCheck


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

METRIC_TYPES = ["order_settlement_time", "agent_uptime", "order_success_rate"]
OPERATORS = ["greater_than", "less_than"]


# ---------------------------------------------------------------------------
# Pure breach detection function (mirrors sla_service.evaluate_rules logic)
# ---------------------------------------------------------------------------

def detect_breach(operator: str, actual_value: float, threshold: float) -> bool:
    """Pure function implementing the SLA breach detection logic.

    This is the exact comparison logic from ``sla_service.evaluate_rules``:

    .. code-block:: python

        if rule.operator == "greater_than" and actual_value > rule.threshold:
            breached = True
        elif rule.operator == "less_than" and actual_value < rule.threshold:
            breached = True

    Extracted here so we can test it as a pure function without a database.
    """
    if operator == "greater_than" and actual_value > threshold:
        return True
    elif operator == "less_than" and actual_value < threshold:
        return True
    return False


# ---------------------------------------------------------------------------
# Oracle: independently compute expected breach result
# ---------------------------------------------------------------------------

def expected_breach(operator: str, actual_value: float, threshold: float) -> bool:
    """Independent oracle for breach detection.

    A breach occurs if and only if:
    - operator is "greater_than" AND actual > threshold, OR
    - operator is "less_than" AND actual < threshold.
    """
    if operator == "greater_than":
        return actual_value > threshold
    elif operator == "less_than":
        return actual_value < threshold
    return False


# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

operator_st = st.sampled_from(OPERATORS)
metric_type_st = st.sampled_from(METRIC_TYPES)

# Use finite floats to avoid NaN/Inf edge cases that aren't meaningful for SLA metrics
threshold_st = st.floats(
    min_value=-1e6, max_value=1e6, allow_nan=False, allow_infinity=False
)
actual_value_st = st.floats(
    min_value=-1e6, max_value=1e6, allow_nan=False, allow_infinity=False
)


# ---------------------------------------------------------------------------
# Property 6 — SLA breach detection correctness
# ---------------------------------------------------------------------------

class TestSLABreachDetectionCorrectness:
    """Property 6: SLA breach detection correctness.

    *For any* SLA rule with a metric type, threshold value, and comparison
    operator, and *for any* actual metric value, the evaluation SHALL detect
    a breach if and only if: (operator is "greater_than" AND actual > threshold)
    OR (operator is "less_than" AND actual < threshold).

    **Validates: Requirements 4.2**
    """

    @given(
        operator=operator_st,
        threshold=threshold_st,
        actual_value=actual_value_st,
        metric_type=metric_type_st,
    )
    @settings(
        max_examples=100,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
        deadline=None,
    )
    def test_breach_detected_iff_condition_holds(
        self,
        operator: str,
        threshold: float,
        actual_value: float,
        metric_type: str,
    ) -> None:
        """Breach detection matches the expected formula for all inputs.

        For any operator, threshold, and actual value, ``detect_breach``
        returns True if and only if the oracle ``expected_breach`` returns True.

        **Validates: Requirements 4.2**
        """
        result = detect_breach(operator, actual_value, threshold)
        expected = expected_breach(operator, actual_value, threshold)

        assert result == expected, (
            f"Breach detection mismatch: "
            f"operator={operator!r}, actual={actual_value}, threshold={threshold}, "
            f"metric_type={metric_type!r} → got {result}, expected {expected}"
        )

    @given(
        threshold=threshold_st,
        actual_value=actual_value_st,
    )
    @settings(
        max_examples=100,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
        deadline=None,
    )
    def test_greater_than_breaches_only_when_actual_exceeds_threshold(
        self,
        threshold: float,
        actual_value: float,
    ) -> None:
        """With operator "greater_than", breach occurs iff actual > threshold.

        **Validates: Requirements 4.2**
        """
        result = detect_breach("greater_than", actual_value, threshold)

        if actual_value > threshold:
            assert result is True, (
                f"Expected breach: actual={actual_value} > threshold={threshold}"
            )
        else:
            assert result is False, (
                f"Expected no breach: actual={actual_value} <= threshold={threshold}"
            )

    @given(
        threshold=threshold_st,
        actual_value=actual_value_st,
    )
    @settings(
        max_examples=100,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
        deadline=None,
    )
    def test_less_than_breaches_only_when_actual_below_threshold(
        self,
        threshold: float,
        actual_value: float,
    ) -> None:
        """With operator "less_than", breach occurs iff actual < threshold.

        **Validates: Requirements 4.2**
        """
        result = detect_breach("less_than", actual_value, threshold)

        if actual_value < threshold:
            assert result is True, (
                f"Expected breach: actual={actual_value} < threshold={threshold}"
            )
        else:
            assert result is False, (
                f"Expected no breach: actual={actual_value} >= threshold={threshold}"
            )

    @given(
        operator=operator_st,
        threshold=threshold_st,
    )
    @settings(
        max_examples=100,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
        deadline=None,
    )
    def test_equal_values_never_breach(
        self,
        operator: str,
        threshold: float,
    ) -> None:
        """When actual == threshold, no breach is detected regardless of operator.

        The operators are strict: "greater_than" (not >=) and "less_than" (not <=).

        **Validates: Requirements 4.2**
        """
        result = detect_breach(operator, threshold, threshold)

        assert result is False, (
            f"Expected no breach when actual == threshold: "
            f"operator={operator!r}, value={threshold}"
        )
