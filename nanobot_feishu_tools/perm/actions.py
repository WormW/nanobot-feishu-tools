"""Feishu permission management actions."""

from __future__ import annotations

from typing import Any

import lark_oapi as lark

from nanobot_feishu_tools._api import check_response, run_sync


async def list_members(client: lark.Client, token: str, token_type: str) -> dict:
    """List collaborators of a file/document."""
    from lark_oapi.api.drive.v1 import ListPermissionMemberRequest

    req = (
        ListPermissionMemberRequest.builder()
        .token(token)
        .type(token_type)
        .build()
    )
    resp = await run_sync(client.drive.v1.permission_member.list, req)
    check_response(resp, "drive.v1.permission_member.list")

    items = resp.data.items or [] if resp.data else []
    return {
        "members": [
            {
                "member_type": getattr(m, "member_type", None),
                "member_id": getattr(m, "member_id", None),
                "perm": getattr(m, "perm", None),
                "name": getattr(m, "name", None),
            }
            for m in items
        ],
    }


async def add_member(
    client: lark.Client,
    token: str,
    token_type: str,
    member_entity_type: str,
    member_type: str,
    member_id: str,
    perm: str,
) -> dict:
    """Add a collaborator to a file/document."""
    from lark_oapi.api.drive.v1 import (
        CreatePermissionMemberRequest,
        BaseMember,
    )

    member = (
        BaseMember.builder()
        .type(member_entity_type)
        .member_type(member_type)
        .member_id(member_id)
        .perm(perm)
        .perm_type("container")
        .build()
    )
    req = (
        CreatePermissionMemberRequest.builder()
        .token(token)
        .type(token_type)
        .need_notification(False)
        .request_body(member)
        .build()
    )
    resp = await run_sync(client.drive.v1.permission_member.create, req)
    check_response(resp, "drive.v1.permission_member.create")

    result_member = resp.data.member if resp.data else None
    return {
        "success": True,
        "member": {
            "member_type": getattr(result_member, "member_type", None),
            "member_id": getattr(result_member, "member_id", None),
            "perm": getattr(result_member, "perm", None),
            "name": getattr(result_member, "name", None),
        } if result_member else None,
    }


async def remove_member(
    client: lark.Client,
    token: str,
    token_type: str,
    member_entity_type: str,
    member_type: str,
    member_id: str,
) -> dict:
    """Remove a collaborator from a file/document."""
    from lark_oapi.api.drive.v1 import DeletePermissionMemberRequest

    req = (
        DeletePermissionMemberRequest.builder()
        .token(token)
        .member_id(member_id)
        .type(token_type)
        .member_type(member_type)
        .build()
    )
    resp = await run_sync(client.drive.v1.permission_member.delete, req)
    check_response(resp, "drive.v1.permission_member.delete")

    return {"success": True}
