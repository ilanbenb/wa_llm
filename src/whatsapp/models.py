from datetime import datetime
from typing import Optional, List, Generic, TypeVar, Dict, Any

from pydantic import BaseModel, Field

T = TypeVar("T")


class BaseResponse(BaseModel, Generic[T]):
    code: str
    message: str
    results: Optional[T] = None


class ErrorResponse(BaseModel):
    code: str
    message: str
    results: Optional[Dict[str, Any]] = None


class Participant(BaseModel):
    JID: str
    LID: Optional[str] = None
    IsAdmin: bool
    IsSuperAdmin: bool
    DisplayName: Optional[str] = None
    Error: int = 0
    AddRequest: Optional[str] = None


class Group(BaseModel):
    JID: str
    OwnerJID: str
    OwnerPN: str | None
    Name: str
    NameSetAt: datetime
    NameSetBy: str
    Topic: str = ""
    TopicID: str = ""
    TopicSetAt: datetime
    TopicSetBy: str = ""
    TopicDeleted: bool = False
    IsLocked: bool = False
    IsAnnounce: bool = False
    AnnounceVersionID: str
    IsEphemeral: bool = False
    DisappearingTimer: int = 0
    IsIncognito: bool = False
    IsParent: bool = False
    DefaultMembershipApprovalMode: str = ""
    LinkedParentJID: str = ""
    IsDefaultSubGroup: bool = False
    IsJoinApprovalRequired: bool = False
    GroupCreated: datetime
    ParticipantVersionID: str
    Participants: List[Participant]
    MemberAddMode: str


class NewsletterPicture(BaseModel):
    url: str = ""
    id: str
    type: str
    direct_path: str


class NewsletterName(BaseModel):
    text: str
    id: str
    update_time: str


class NewsletterDescription(BaseModel):
    text: str
    id: str
    update_time: str


class NewsletterSettings(BaseModel):
    reaction_codes: Dict[str, str]


class NewsletterThreadMetadata(BaseModel):
    creation_time: str
    invite: str
    name: NewsletterName
    description: NewsletterDescription
    subscribers_count: str
    verification: str
    picture: NewsletterPicture
    preview: NewsletterPicture
    settings: NewsletterSettings


class NewsletterViewerMetadata(BaseModel):
    mute: str
    role: str


class NewsletterState(BaseModel):
    type: str


class Newsletter(BaseModel):
    id: str
    state: NewsletterState
    thread_metadata: NewsletterThreadMetadata
    viewer_metadata: NewsletterViewerMetadata


class Device(BaseModel):
    User: str
    Agent: int
    Device: str
    Server: str
    AD: bool


class UserInfo(BaseModel):
    verified_name: str
    status: str
    picture_id: str
    devices: List[Device]


class UserAvatar(BaseModel):
    url: str
    id: str
    type: str


class UserPrivacy(BaseModel):
    group_add: str
    last_seen: Optional[str]
    status: str
    profile: str
    read_receipts: str


class MessageResponse(BaseModel):
    message_id: str
    status: str


class LoginResult(BaseModel):
    qr_duration: int
    qr_link: str


class LoginWithCodeResult(BaseModel):
    pair_code: str


class CreateGroupResult(BaseModel):
    group_id: str


class ManageParticipantResult(BaseModel):
    participant: str
    status: str
    message: str


# Request Models
class SendMessageRequest(BaseModel):
    phone: str = Field(examples=["6289685028129@s.whatsapp.net"])
    message: str
    reply_message_id: Optional[str] = None


class SendLinkRequest(BaseModel):
    phone: str
    link: str
    caption: Optional[str] = None


class SendLocationRequest(BaseModel):
    phone: str
    latitude: str
    longitude: str


class SendPollRequest(BaseModel):
    phone: str
    question: str
    options: List[str]
    max_answer: int


class SendContactRequest(BaseModel):
    phone: str
    contact_name: str
    contact_phone: str


class MessageActionRequest(BaseModel):
    phone: str


class ManageParticipantRequest(BaseModel):
    group_id: str
    participants: List[str]


class CreateGroupRequest(BaseModel):
    title: str
    participants: List[str]


class JoinGroupRequest(BaseModel):
    link: str


class LeaveGroupRequest(BaseModel):
    group_id: str


class UnfollowNewsletterRequest(BaseModel):
    newsletter_id: str


class DeviceResult(BaseModel):
    name: str
    device: str


D = TypeVar("D")


class DataResult(BaseModel, Generic[D]):
    data: D


# Response Type Aliases
LoginResponse = BaseResponse[LoginResult]
LoginWithCodeResponse = BaseResponse[LoginWithCodeResult]
UserInfoResponse = BaseResponse[UserInfo]
UserAvatarResponse = BaseResponse[UserAvatar]
UserPrivacyResponse = BaseResponse[UserPrivacy]
MessageSendResponse = BaseResponse[MessageResponse]
CreateGroupResponse = BaseResponse[CreateGroupResult]
ManageParticipantResponse = BaseResponse[List[ManageParticipantResult]]
NewsletterResponse = BaseResponse[DataResult[List[Newsletter]]]
GroupResponse = BaseResponse[DataResult[List[Group]]]
DeviceResponse = BaseResponse[List[DeviceResult]]
GenericResponse = BaseResponse[None]
