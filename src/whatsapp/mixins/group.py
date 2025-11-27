from ..protocols import WhatsAppClientProtocol

from ..models import (
    CreateGroupRequest,
    CreateGroupResponse,
    ManageParticipantRequest,
    ManageParticipantResponse,
    JoinGroupRequest,
    LeaveGroupRequest,
    GenericResponse,
)


class GroupMixin(WhatsAppClientProtocol):
    async def create_group(self, request: CreateGroupRequest) -> CreateGroupResponse:
        response = await self._post("/group", json=request)
        return CreateGroupResponse.model_validate_json(response.content)

    async def add_participants(
        self, request: ManageParticipantRequest
    ) -> ManageParticipantResponse:
        response = await self._post("/group/participants", json=request)
        return ManageParticipantResponse.model_validate_json(response.content)

    async def remove_participants(
        self, request: ManageParticipantRequest
    ) -> ManageParticipantResponse:
        response = await self._post("/group/participants/remove", json=request)
        return ManageParticipantResponse.model_validate_json(response.content)

    async def promote_participants(
        self, request: ManageParticipantRequest
    ) -> ManageParticipantResponse:
        response = await self._post("/group/participants/promote", json=request)
        return ManageParticipantResponse.model_validate_json(response.content)

    async def demote_participants(
        self, request: ManageParticipantRequest
    ) -> ManageParticipantResponse:
        response = await self._post("/group/participants/demote", json=request)
        return ManageParticipantResponse.model_validate_json(response.content)

    async def join_group_with_link(self, link: str) -> GenericResponse:
        response = await self._post(
            "/group/join-with-link", json=JoinGroupRequest(link=link)
        )
        return GenericResponse.model_validate_json(response.content)

    async def leave_group(self, group_id: str) -> GenericResponse:
        response = await self._post(
            "/group/leave", json=LeaveGroupRequest(group_id=group_id)
        )
        return GenericResponse.model_validate_json(response.content)
