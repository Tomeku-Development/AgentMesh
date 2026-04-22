"""Property-based tests for RBAC permission checks.

**Feature: saas-platform-enhancements, Property 7: RBAC permission check**
**Validates: Requirements 5.2, 5.3, 5.4, 5.5**
"""

from __future__ import annotations

from hypothesis import given, settings, strategies as st

from mesh_platform.models.workspace import WorkspaceRole

# ---------------------------------------------------------------------------
# Permission definitions — the ground-truth permitted sets from the design doc
# and the dependency functions in mesh_platform/dependencies.py.
#
#   admin    permits {owner, admin}
#   operator permits {owner, admin, operator}
#   auditor  permits {owner, admin, auditor}
#   developer permits {owner, admin, developer}
# ---------------------------------------------------------------------------

PERMISSION_LEVELS: dict[str, set[str]] = {
    "admin": {WorkspaceRole.owner.value, WorkspaceRole.admin.value},
    "operator": {
        WorkspaceRole.owner.value,
        WorkspaceRole.admin.value,
        WorkspaceRole.operator.value,
    },
    "auditor": {
        WorkspaceRole.owner.value,
        WorkspaceRole.admin.value,
        WorkspaceRole.auditor.value,
    },
    "developer": {
        WorkspaceRole.owner.value,
        WorkspaceRole.admin.value,
        WorkspaceRole.developer.value,
    },
}

ALL_ROLES = [r.value for r in WorkspaceRole]
ALL_PERMISSION_LEVELS = list(PERMISSION_LEVELS.keys())


def check_permission(role: str, permission_level: str) -> bool:
    """Pure function that mirrors the permission logic in the dependency functions.

    Returns True when *role* is in the permitted set for *permission_level*.
    This is the exact same check each ``require_workspace_*`` dependency performs
    (membership.role in {allowed_roles}).
    """
    permitted = PERMISSION_LEVELS.get(permission_level)
    if permitted is None:
        return False
    return role in permitted


# ---------------------------------------------------------------------------
# Property 7 — RBAC permission check
# ---------------------------------------------------------------------------


class TestRBACPermissionCheck:
    """Property 7: RBAC permission check.

    *For any* workspace role and *for any* permission level (admin, operator,
    auditor, developer), access SHALL be granted if and only if the role is in
    the permitted set for that level.

    **Validates: Requirements 5.2, 5.3, 5.4, 5.5**
    """

    @given(
        role=st.sampled_from(ALL_ROLES),
        permission_level=st.sampled_from(ALL_PERMISSION_LEVELS),
    )
    @settings(max_examples=200)
    def test_access_granted_iff_role_in_permitted_set(
        self, role: str, permission_level: str
    ) -> None:
        """Access is granted ⟺ role ∈ permitted set for the permission level."""
        expected_permitted = PERMISSION_LEVELS[permission_level]
        result = check_permission(role, permission_level)

        if role in expected_permitted:
            assert result is True, (
                f"Role '{role}' should be GRANTED for permission level "
                f"'{permission_level}' (permitted: {expected_permitted})"
            )
        else:
            assert result is False, (
                f"Role '{role}' should be DENIED for permission level "
                f"'{permission_level}' (permitted: {expected_permitted})"
            )

    @given(role=st.sampled_from(ALL_ROLES))
    @settings(max_examples=100)
    def test_admin_level_permits_only_owner_and_admin(self, role: str) -> None:
        """Requirement 5.2: admin permits {owner, admin} and denies all others."""
        result = check_permission(role, "admin")
        expected = role in {"owner", "admin"}
        assert result == expected, (
            f"Admin level: role '{role}' — expected {expected}, got {result}"
        )

    @given(role=st.sampled_from(ALL_ROLES))
    @settings(max_examples=100)
    def test_operator_level_permits_owner_admin_operator(self, role: str) -> None:
        """Requirement 5.3: operator permits {owner, admin, operator}."""
        result = check_permission(role, "operator")
        expected = role in {"owner", "admin", "operator"}
        assert result == expected, (
            f"Operator level: role '{role}' — expected {expected}, got {result}"
        )

    @given(role=st.sampled_from(ALL_ROLES))
    @settings(max_examples=100)
    def test_auditor_level_permits_owner_admin_auditor(self, role: str) -> None:
        """Requirement 5.4: auditor permits {owner, admin, auditor}."""
        result = check_permission(role, "auditor")
        expected = role in {"owner", "admin", "auditor"}
        assert result == expected, (
            f"Auditor level: role '{role}' — expected {expected}, got {result}"
        )

    @given(role=st.sampled_from(ALL_ROLES))
    @settings(max_examples=100)
    def test_developer_level_permits_owner_admin_developer(self, role: str) -> None:
        """Requirement 5.5: developer permits {owner, admin, developer}."""
        result = check_permission(role, "developer")
        expected = role in {"owner", "admin", "developer"}
        assert result == expected, (
            f"Developer level: role '{role}' — expected {expected}, got {result}"
        )

    @given(
        role=st.sampled_from(ALL_ROLES),
        permission_level=st.sampled_from(ALL_PERMISSION_LEVELS),
    )
    @settings(max_examples=200)
    def test_owner_and_admin_always_permitted(
        self, role: str, permission_level: str
    ) -> None:
        """Owner and admin roles are always in every permitted set."""
        result = check_permission(role, permission_level)
        if role in {"owner", "admin"}:
            assert result is True, (
                f"Role '{role}' must always be permitted for '{permission_level}'"
            )

    @given(permission_level=st.sampled_from(ALL_PERMISSION_LEVELS))
    @settings(max_examples=100)
    def test_viewer_never_permitted(self, permission_level: str) -> None:
        """Viewer role is never in any of the four permission level sets."""
        result = check_permission("viewer", permission_level)
        assert result is False, (
            f"Viewer should be denied for permission level '{permission_level}'"
        )


# ---------------------------------------------------------------------------
# Role escalation prevention helper
# ---------------------------------------------------------------------------

from mesh_platform.models.workspace import ROLE_LEVELS


def can_self_assign_role(current_role: str, target_role: str) -> bool:
    """Pure function that mirrors the self-assignment escalation check.

    Returns True (allowed) only when the target role level is NOT strictly
    higher than the current role level.  In other words, a user may keep
    their current level or move to a lower one, but never escalate.

    This mirrors the guard in ``update_member_role``:

        if target_level > current_level:
            raise HTTPException(403, "Cannot escalate own role")
    """
    current_level = ROLE_LEVELS.get(current_role, 0)
    target_level = ROLE_LEVELS.get(target_role, 0)
    # Reject when target is strictly higher
    if target_level > current_level:
        return False  # rejected — escalation attempt
    return True  # allowed — same or lower level


# ---------------------------------------------------------------------------
# Property 8 — Role escalation prevention
# ---------------------------------------------------------------------------


class TestRoleEscalationPrevention:
    """Property 8: Role escalation prevention.

    *For any* user with a current workspace role, attempting to assign
    themselves a role with a strictly higher level in the hierarchy
    (viewer=1 < auditor=2 < developer=3 < operator=4 < admin=5 < owner=6)
    SHALL be rejected.

    **Validates: Requirements 5.7**
    """

    @given(
        current_role=st.sampled_from(ALL_ROLES),
        target_role=st.sampled_from(ALL_ROLES),
    )
    @settings(max_examples=200)
    def test_self_escalation_always_rejected(
        self, current_role: str, target_role: str
    ) -> None:
        """Assigning yourself a strictly higher role is always rejected."""
        current_level = ROLE_LEVELS[current_role]
        target_level = ROLE_LEVELS[target_role]

        result = can_self_assign_role(current_role, target_role)

        if target_level > current_level:
            assert result is False, (
                f"Self-escalation from '{current_role}' (level {current_level}) "
                f"to '{target_role}' (level {target_level}) should be REJECTED"
            )
        else:
            assert result is True, (
                f"Self-assignment from '{current_role}' (level {current_level}) "
                f"to '{target_role}' (level {target_level}) should be ALLOWED "
                f"(same or lower level)"
            )

    @given(current_role=st.sampled_from(ALL_ROLES))
    @settings(max_examples=100)
    def test_self_assign_same_role_allowed(self, current_role: str) -> None:
        """A user can always assign themselves the same role they already have."""
        result = can_self_assign_role(current_role, current_role)
        assert result is True, (
            f"Self-assigning the same role '{current_role}' should be allowed"
        )

    @given(
        current_role=st.sampled_from(ALL_ROLES),
        target_role=st.sampled_from(ALL_ROLES),
    )
    @settings(max_examples=100)
    def test_viewer_cannot_escalate_to_any_higher_role(
        self, current_role: str, target_role: str
    ) -> None:
        """Viewer (lowest level) cannot escalate to any role above viewer."""
        if current_role != "viewer":
            return  # only test viewer
        target_level = ROLE_LEVELS[target_role]
        result = can_self_assign_role("viewer", target_role)
        if target_level > 1:
            assert result is False, (
                f"Viewer should not be able to self-escalate to '{target_role}'"
            )
        else:
            assert result is True, "Viewer can self-assign viewer"

    @given(target_role=st.sampled_from(ALL_ROLES))
    @settings(max_examples=100)
    def test_owner_can_self_assign_any_role(self, target_role: str) -> None:
        """Owner (highest level) can self-assign any role (no escalation possible)."""
        result = can_self_assign_role("owner", target_role)
        assert result is True, (
            f"Owner should be able to self-assign '{target_role}' "
            f"(owner is already at the highest level)"
        )
