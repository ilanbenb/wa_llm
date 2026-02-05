from __future__ import annotations

from typing import Optional

from ..models import (
    ApiResponse,
    CreateGroupRequest,
    CreateGroupResponse,
    GenericResponse,
    GroupDescriptionRequest,
    GroupNameRequest,
    GroupResponse,
    GroupTopicRequest,
    JoinGroupRequest,
    LeaveGroupRequest,
    ManageParticipantRequest,
    ManageParticipantResponse,
)
from ..protocols import GoWaClientProtocol


class GroupMixin(GoWaClientProtocol):
    async def get_group_info(
        self, group_id: str, *, device_id: Optional[str] = None
    ) -> ApiResponse[dict]:
        response = await self._get(
            "/group/info", params={"group_id": group_id}, device_id=device_id
        )
        return ApiResponse[dict].model_validate_json(response.content)

    async def create_group(
        self, request: CreateGroupRequest, *, device_id: Optional[str] = None
    ) -> CreateGroupResponse:
        response = await self._post("/group", json=request, device_id=device_id)
        return CreateGroupResponse.model_validate_json(response.content)

    async def get_group_participants(
        self, group_id: str, *, device_id: Optional[str] = None
    ) -> GroupResponse:
        response = await self._get(
            "/group/participants", params={"group_id": group_id}, device_id=device_id
        )
        return GroupResponse.model_validate_json(response.content)

    async def export_group_participants(
        self, group_id: str, *, device_id: Optional[str] = None
    ) -> ApiResponse[dict]:
        response = await self._get(
            "/group/participants/export",
            params={"group_id": group_id},
            device_id=device_id,
        )
        return ApiResponse[dict].model_validate_json(response.content)

    async def add_participants(
        self, request: ManageParticipantRequest, *, device_id: Optional[str] = None
    ) -> ManageParticipantResponse:
        response = await self._post(
            "/group/participants", json=request, device_id=device_id
        )
        return ManageParticipantResponse.model_validate_json(response.content)

    async def remove_participants(
        self, request: ManageParticipantRequest, *, device_id: Optional[str] = None
    ) -> ManageParticipantResponse:
        response = await self._post(
            "/group/participants/remove", json=request, device_id=device_id
        )
        return ManageParticipantResponse.model_validate_json(response.content)

    async def promote_participants(
        self, request: ManageParticipantRequest, *, device_id: Optional[str] = None
    ) -> ManageParticipantResponse:
        response = await self._post(
            "/group/participants/promote", json=request, device_id=device_id
        )
        return ManageParticipantResponse.model_validate_json(response.content)

    async def demote_participants(
        self, request: ManageParticipantRequest, *, device_id: Optional[str] = None
    ) -> ManageParticipantResponse:
        response = await self._post(
            "/group/participants/demote", json=request, device_id=device_id
        )
        return ManageParticipantResponse.model_validate_json(response.content)

    async def join_group_with_link(
        self, link: str, *, device_id: Optional[str] = None
    ) -> GenericResponse:
        response = await self._post(
            "/group/join-with-link",
            json=JoinGroupRequest(link=link),
            device_id=device_id,
        )
        return GenericResponse.model_validate_json(response.content)

    async def get_group_info_from_link(
        self, link: str, *, device_id: Optional[str] = None
    ) -> ApiResponse[dict]:
        response = await self._get(
            "/group/info-from-link", params={"link": link}, device_id=device_id
        )
        return ApiResponse[dict].model_validate_json(response.content)

    async def get_group_participant_requests(
        self, group_id: str, *, device_id: Optional[str] = None
    ) -> ApiResponse[dict]:
        response = await self._get(
            "/group/participant-requests",
            params={"group_id": group_id},
            device_id=device_id,
        )
        return ApiResponse[dict].model_validate_json(response.content)

    async def approve_group_participant_requests(
        self, group_id: str, participants: list[str], *, device_id: Optional[str] = None
    ) -> ApiResponse[dict]:
        response = await self._post(
            "/group/participant-requests/approve",
            json={"group_id": group_id, "participants": participants},
            device_id=device_id,
        )
        return ApiResponse[dict].model_validate_json(response.content)

    async def reject_group_participant_requests(
        self, group_id: str, participants: list[str], *, device_id: Optional[str] = None
    ) -> ApiResponse[dict]:
        response = await self._post(
            "/group/participant-requests/reject",
            json={"group_id": group_id, "participants": participants},
            device_id=device_id,
        )
        return ApiResponse[dict].model_validate_json(response.content)

    async def leave_group(
        self, group_id: str, *, device_id: Optional[str] = None
    ) -> GenericResponse:
        response = await self._post(
            "/group/leave",
            json=LeaveGroupRequest(group_id=group_id),
            device_id=device_id,
        )
        return GenericResponse.model_validate_json(response.content)

    async def set_group_photo(
        self,
        group_id: str,
        image: bytes,
        *,
        filename: str = "group.jpg",
        device_id: Optional[str] = None,
    ) -> ApiResponse[dict]:
        response = await self._post(
            "/group/photo",
            data={"group_id": group_id},
            files={"image": (filename, image)},
            device_id=device_id,
        )
        return ApiResponse[dict].model_validate_json(response.content)

    async def set_group_name(
        self, request: GroupNameRequest, *, device_id: Optional[str] = None
    ) -> ApiResponse[dict]:
        response = await self._post("/group/name", json=request, device_id=device_id)
        return ApiResponse[dict].model_validate_json(response.content)

    async def set_group_topic(
        self, request: GroupTopicRequest, *, device_id: Optional[str] = None
    ) -> ApiResponse[dict]:
        response = await self._post("/group/topic", json=request, device_id=device_id)
        return ApiResponse[dict].model_validate_json(response.content)

    async def set_group_description(
        self, request: GroupDescriptionRequest, *, device_id: Optional[str] = None
    ) -> ApiResponse[dict]:
        response = await self._post(
            "/group/description", json=request, device_id=device_id
        )
        return ApiResponse[dict].model_validate_json(response.content)
