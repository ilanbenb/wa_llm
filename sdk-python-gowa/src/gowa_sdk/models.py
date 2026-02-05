from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Generic, List, Optional, TypeVar

from pydantic import AliasChoices, BaseModel, ConfigDict, Field

T = TypeVar("T")


class BaseModelConfig(BaseModel):
    model_config = ConfigDict(extra="allow", populate_by_name=True)


class ApiResponse(BaseModelConfig, Generic[T]):
    status: Optional[int] = None
    code: Optional[str] = None
    message: Optional[str] = None
    results: Optional[T] = None


class ErrorResponse(BaseModelConfig):
    code: Optional[str] = None
    message: Optional[str] = None
    results: Optional[Dict[str, Any]] = None


class MessageSendResult(BaseModelConfig):
    message_id: Optional[str] = Field(
        default=None, validation_alias=AliasChoices("message_id", "id")
    )
    status: Optional[str] = None


class LoginResult(BaseModelConfig):
    qr_duration: Optional[int] = None
    qr_link: Optional[str] = None


class LoginWithCodeResult(BaseModelConfig):
    pair_code: Optional[str] = None


class CreateGroupResult(BaseModelConfig):
    group_id: Optional[str] = None


class ManageParticipantResult(BaseModelConfig):
    participant: Optional[str] = None
    status: Optional[str] = None
    message: Optional[str] = None


class DeviceResult(BaseModelConfig):
    name: Optional[str] = None
    device: Optional[str] = None


class DeviceInfo(BaseModelConfig):
    id: Optional[str] = None
    device_id: Optional[str] = None
    phone: Optional[str] = None
    jid: Optional[str] = None
    pushname: Optional[str] = None
    status: Optional[str] = None
    last_seen: Optional[str] = None


class DeviceStatus(BaseModelConfig):
    status: Optional[str] = None
    message: Optional[str] = None


class UserAvatar(BaseModelConfig):
    url: Optional[str] = None
    id: Optional[str] = None
    type: Optional[str] = None


class UserPrivacy(BaseModelConfig):
    group_add: Optional[str] = None
    last_seen: Optional[str] = None
    status: Optional[str] = None
    profile: Optional[str] = None
    read_receipts: Optional[str] = None


class Device(BaseModelConfig):
    user: Optional[str] = Field(default=None, alias="User")
    agent: Optional[int] = Field(default=None, alias="Agent")
    device: Optional[str] = Field(default=None, alias="Device")
    server: Optional[str] = Field(default=None, alias="Server")
    ad: Optional[bool] = Field(default=None, alias="AD")


class UserInfo(BaseModelConfig):
    verified_name: Optional[str] = None
    status: Optional[str] = None
    picture_id: Optional[str] = None
    devices: Optional[List[Device]] = None


class Participant(BaseModelConfig):
    jid: Optional[str] = Field(default=None, alias="JID")
    lid: Optional[str] = Field(default=None, alias="LID")
    is_admin: Optional[bool] = Field(default=None, alias="IsAdmin")
    is_super_admin: Optional[bool] = Field(default=None, alias="IsSuperAdmin")
    display_name: Optional[str] = Field(default=None, alias="DisplayName")
    error: Optional[int] = Field(default=None, alias="Error")
    add_request: Optional[str] = Field(default=None, alias="AddRequest")


class Group(BaseModelConfig):
    jid: Optional[str] = Field(default=None, alias="JID")
    owner_jid: Optional[str] = Field(default=None, alias="OwnerJID")
    owner_pn: Optional[str] = Field(default=None, alias="OwnerPN")
    name: Optional[str] = Field(default=None, alias="Name")
    name_set_at: Optional[datetime] = Field(default=None, alias="NameSetAt")
    name_set_by: Optional[str] = Field(default=None, alias="NameSetBy")
    topic: Optional[str] = Field(default=None, alias="Topic")
    topic_id: Optional[str] = Field(default=None, alias="TopicID")
    topic_set_at: Optional[datetime] = Field(default=None, alias="TopicSetAt")
    topic_set_by: Optional[str] = Field(default=None, alias="TopicSetBy")
    topic_deleted: Optional[bool] = Field(default=None, alias="TopicDeleted")
    is_locked: Optional[bool] = Field(default=None, alias="IsLocked")
    is_announce: Optional[bool] = Field(default=None, alias="IsAnnounce")
    announce_version_id: Optional[str] = Field(default=None, alias="AnnounceVersionID")
    is_ephemeral: Optional[bool] = Field(default=None, alias="IsEphemeral")
    disappearing_timer: Optional[int] = Field(default=None, alias="DisappearingTimer")
    is_incognito: Optional[bool] = Field(default=None, alias="IsIncognito")
    is_parent: Optional[bool] = Field(default=None, alias="IsParent")
    default_membership_approval_mode: Optional[str] = Field(
        default=None, alias="DefaultMembershipApprovalMode"
    )
    linked_parent_jid: Optional[str] = Field(default=None, alias="LinkedParentJID")
    is_default_sub_group: Optional[bool] = Field(
        default=None, alias="IsDefaultSubGroup"
    )
    is_join_approval_required: Optional[bool] = Field(
        default=None, alias="IsJoinApprovalRequired"
    )
    group_created: Optional[datetime] = Field(default=None, alias="GroupCreated")
    participant_version_id: Optional[str] = Field(
        default=None, alias="ParticipantVersionID"
    )
    participants: Optional[List[Participant]] = Field(
        default=None, alias="Participants"
    )
    member_add_mode: Optional[str] = Field(default=None, alias="MemberAddMode")


class NewsletterPicture(BaseModelConfig):
    url: Optional[str] = None
    id: Optional[str] = None
    type: Optional[str] = None
    direct_path: Optional[str] = None


class NewsletterName(BaseModelConfig):
    text: Optional[str] = None
    id: Optional[str] = None
    update_time: Optional[str] = None


class NewsletterDescription(BaseModelConfig):
    text: Optional[str] = None
    id: Optional[str] = None
    update_time: Optional[str] = None


class NewsletterSettings(BaseModelConfig):
    reaction_codes: Optional[Dict[str, str]] = None


class NewsletterThreadMetadata(BaseModelConfig):
    creation_time: Optional[str] = None
    invite: Optional[str] = None
    name: Optional[NewsletterName] = None
    description: Optional[NewsletterDescription] = None
    subscribers_count: Optional[str] = None
    verification: Optional[str] = None
    picture: Optional[NewsletterPicture] = None
    preview: Optional[NewsletterPicture] = None
    settings: Optional[NewsletterSettings] = None


class NewsletterViewerMetadata(BaseModelConfig):
    mute: Optional[str] = None
    role: Optional[str] = None


class NewsletterState(BaseModelConfig):
    type: Optional[str] = None


class Newsletter(BaseModelConfig):
    id: Optional[str] = None
    state: Optional[NewsletterState] = None
    thread_metadata: Optional[NewsletterThreadMetadata] = None
    viewer_metadata: Optional[NewsletterViewerMetadata] = None


class DataResult(BaseModelConfig, Generic[T]):
    data: T


# Request models
class SendMessageRequest(BaseModelConfig):
    phone: str
    message: str
    reply_message_id: Optional[str] = None
    is_forwarded: Optional[bool] = None
    duration: Optional[int] = None
    mentions: Optional[List[str]] = None


class SendMediaBaseRequest(BaseModelConfig):
    phone: str
    caption: Optional[str] = None
    view_once: Optional[bool] = None
    compress: Optional[bool] = None
    is_forwarded: Optional[bool] = None
    duration: Optional[int] = None
    mentions: Optional[List[str]] = None


class SendImageRequest(SendMediaBaseRequest):
    pass


class SendVideoRequest(SendMediaBaseRequest):
    pass


class SendAudioRequest(BaseModelConfig):
    phone: str
    ptt: Optional[bool] = None


class SendFileRequest(BaseModelConfig):
    phone: str
    caption: Optional[str] = None


class SendStickerRequest(BaseModelConfig):
    phone: str
    is_forwarded: Optional[bool] = None
    mentions: Optional[List[str]] = None


class SendContactRequest(BaseModelConfig):
    phone: str
    contact_name: str
    contact_phone: str


class SendLinkRequest(BaseModelConfig):
    phone: str
    link: str
    caption: Optional[str] = None


class SendLocationRequest(BaseModelConfig):
    phone: str
    latitude: float
    longitude: float
    name: Optional[str] = None
    address: Optional[str] = None


class SendPollRequest(BaseModelConfig):
    phone: str
    question: str
    options: List[str]
    max_answer: Optional[int] = None


class SendPresenceRequest(BaseModelConfig):
    phone: str
    presence: str


class SendChatPresenceRequest(BaseModelConfig):
    chat_id: str
    presence: str


class MessageActionRequest(BaseModelConfig):
    phone: str


class ManageParticipantRequest(BaseModelConfig):
    group_id: str
    participants: List[str]


class CreateGroupRequest(BaseModelConfig):
    title: str
    participants: List[str]


class JoinGroupRequest(BaseModelConfig):
    link: str


class LeaveGroupRequest(BaseModelConfig):
    group_id: str


class GroupPhotoRequest(BaseModelConfig):
    group_id: str


class GroupNameRequest(BaseModelConfig):
    group_id: str
    name: str


class GroupTopicRequest(BaseModelConfig):
    group_id: str
    topic: str


class GroupDescriptionRequest(BaseModelConfig):
    group_id: str
    description: str


class UnfollowNewsletterRequest(BaseModelConfig):
    newsletter_id: str


class DeviceCreateRequest(BaseModelConfig):
    name: Optional[str] = None
    description: Optional[str] = None


class DeviceLoginCodeRequest(BaseModelConfig):
    phone: str


# Response aliases
LoginResponse = ApiResponse[LoginResult]
LoginWithCodeResponse = ApiResponse[LoginWithCodeResult]
UserInfoResponse = ApiResponse[UserInfo]
UserAvatarResponse = ApiResponse[UserAvatar]
UserPrivacyResponse = ApiResponse[UserPrivacy]
MessageSendResponse = ApiResponse[MessageSendResult]
CreateGroupResponse = ApiResponse[CreateGroupResult]
ManageParticipantResponse = ApiResponse[List[ManageParticipantResult]]
NewsletterResponse = ApiResponse[DataResult[List[Newsletter]]]
GroupResponse = ApiResponse[DataResult[List[Group]]]
DeviceResponse = ApiResponse[List[DeviceResult]]
DeviceListResponse = ApiResponse[List[DeviceInfo]]
DeviceStatusResponse = ApiResponse[DeviceStatus]
GenericResponse = ApiResponse[None]
