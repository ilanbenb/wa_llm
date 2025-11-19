from typing import TYPE_CHECKING

from ..models import (
    CreateGroupRequest,
    CreateGroupResponse,
    ManageParticipantRequest,
    ManageParticipantResponse,
    JoinGroupRequest,
    LeaveGroupRequest,
    GenericResponse,
)

if TYPE_CHECKING:
    from ..base_client import BaseWhatsAppClient


class GroupMixin:
    async def create_group(
        self: "BaseWhatsAppClient", request: CreateGroupRequest
    ) -> CreateGroupResponse:
        response = await self._post("/group", json=request)
        return CreateGroupResponse.model_validate_json(response.content)

    async def add_participants(
        self: "BaseWhatsAppClient", request: ManageParticipantRequest
    ) -> ManageParticipantResponse:
        response = await self._post("/group/participants", json=request)
        return ManageParticipantResponse.model_validate_json(response.content)

    async def remove_participants(
        self: "BaseWhatsAppClient", request: ManageParticipantRequest
    ) -> ManageParticipantResponse:
        response = await self._post("/group/participants/remove", json=request)
        return ManageParticipantResponse.model_validate_json(response.content)

    async def promote_participants(
        self: "BaseWhatsAppClient", request: ManageParticipantRequest
    ) -> ManageParticipantResponse:
        response = await self._post("/group/participants/promote", json=request)
        return ManageParticipantResponse.model_validate_json(response.content)

    async def demote_participants(
        self: "BaseWhatsAppClient", request: ManageParticipantRequest
    ) -> ManageParticipantResponse:
        response = await self._post("/group/participants/demote", json=request)
        return ManageParticipantResponse.model_validate_json(response.content)

    async def join_group_with_link(
        self: "BaseWhatsAppClient", link: str
    ) -> GenericResponse:
        response = await self._post(
            "/group/join-with-link", json=JoinGroupRequest(link=link)
        )
        return GenericResponse.model_validate_json(response.content)

    async def leave_group(self: "BaseWhatsAppClient", group_id: str) -> GenericResponse:
        response = await self._post(
            "/group/leave", json=LeaveGroupRequest(group_id=group_id)
        )
        return GenericResponse.model_validate_json(response.content)
