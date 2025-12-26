import logging
import asyncio
import random
import csv
import os
from datetime import datetime
from typing import Annotated, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy import func

from api.deps import get_whatsapp, get_db_async_session
from models.group_member import GroupMember
from models.group import Group
from whatsapp import WhatsAppClient
from whatsapp.init_groups import gather_groups
from whatsapp.jid import DefaultUserServer, GroupServer
from whatsapp.models import (
    CreateGroupRequest,
    CreateGroupResponse,
    ManageParticipantRequest,
    ManageParticipantResponse,
    ManageParticipantResult,
    SendMessageRequest,
    GroupResponse,
    DataResult,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["group"])


class GroupSummary(BaseModel):
    JID: str
    Name: Optional[str] = None
    ParticipantCount: int = 0
    GroupCreated: Optional[datetime] = None
    AutoSummaryThreshold: Optional[int] = None
    EnableWebSearch: bool = False


class GroupListResponse(BaseModel):
    code: str
    message: str
    results: DataResult[List[GroupSummary]]


class BulkSendMessageRequest(BaseModel):
    phones: List[str]
    message: str


class BulkSendMessageResult(BaseModel):
    phone: str
    status: str
    message: str


class BulkSendMessageResponse(BaseModel):
    code: str
    message: str
    results: List[BulkSendMessageResult]


class MeResponse(BaseModel):
    jid: str
    platform: str = "Unknown"


class GroupSettingsRequest(BaseModel):
    group_id: str
    auto_summary_threshold: Optional[int] = None
    enable_web_search: Optional[bool] = None


def normalize_participant(phone: str) -> str:
    """
    Normalize a phone number to a WhatsApp JID.
    Removes +, -, spaces. Appends @s.whatsapp.net if missing.
    """
    clean = phone.replace("+", "").replace("-", "").replace(" ", "").strip()
    if "@" not in clean:
        return f"{clean}@{DefaultUserServer}"
    return clean


def normalize_group_id(group_id: str) -> str:
    """
    Normalize a group ID to a WhatsApp JID.
    Appends @g.us if missing. Fixes malformed suffixes.
    """
    clean = group_id.strip()
    if "@" in clean:
        # If it has an @, assume the user might have typed it wrong (e.g. @g.u)
        # We strip everything after @ and append the correct server
        user_part = clean.split('@')[0]
        return f"{user_part}@{GroupServer}"
    return f"{clean}@{GroupServer}"


class SaveReportRequest(BaseModel):
    csv_content: str
    filename: str

@router.post("/report/save")
async def save_report(request: SaveReportRequest):
    """
    Save a client-generated report to the server.
    """
    try:
        reports_dir = os.path.join("src", "reports")
        os.makedirs(reports_dir, exist_ok=True)
        
        # Ensure filename is safe
        safe_filename = os.path.basename(request.filename)
        if not safe_filename.endswith(".csv"):
            safe_filename += ".csv"
            
        report_path = os.path.join(reports_dir, safe_filename)
        
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(request.csv_content)
            
        logger.info(f"Report saved to {report_path}")
        return {"status": "success", "path": report_path}
    except Exception as e:
        logger.error(f"Failed to save report: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/group/{group_id}/members")
async def get_group_members(
    group_id: str,
    session: Annotated[AsyncSession, Depends(get_db_async_session)],
    whatsapp: Annotated[WhatsAppClient, Depends(get_whatsapp)],
):
    """
    Get members of a specific group (DB first, then API).
    """
    group_id = normalize_group_id(group_id)
    try:
        # Check DB
        stmt = select(GroupMember.sender_jid).where(GroupMember.group_jid == group_id)
        result = await session.exec(stmt)
        db_members = result.all()
        
        if db_members:
            return {"source": "db", "members": db_members}
            
        # Fallback to API
        groups_response = await whatsapp.get_user_groups()
        if groups_response.results and groups_response.results.data:
            target_group = next((g for g in groups_response.results.data if g.JID == group_id), None)
            if target_group and target_group.Participants:
                members = [p.JID for p in target_group.Participants]
                return {"source": "api", "members": members}
                
        return {"source": "none", "members": []}
    except Exception as e:
        logger.error(f"Error fetching members: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/group/sync")
async def sync_groups(
    request: Request,
    whatsapp: Annotated[WhatsAppClient, Depends(get_whatsapp)],
):
    """
    Force sync of groups from WhatsApp to DB.
    """
    try:
        logger.info("Starting manual group sync...")
        await gather_groups(request.app.state.db_engine, whatsapp)
        logger.info("Manual group sync completed.")
        return {"status": "success", "message": "Groups synced successfully"}
    except Exception as e:
        logger.error(f"Manual group sync failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/group/me", response_model=MeResponse)
async def get_me(
    whatsapp: Annotated[WhatsAppClient, Depends(get_whatsapp)],
) -> MeResponse:
    """
    Get the current connected device JID.
    """
    try:
        devices = await whatsapp.get_devices()
        if devices.results and len(devices.results) > 0:
            # Assuming the first device is the active one
            device = devices.results[0]
            return MeResponse(jid=device.device, platform=device.platform if hasattr(device, 'platform') else "WhatsApp")
        return MeResponse(jid="Unknown", platform="Unknown")
    except Exception as e:
        logger.error(f"Error fetching device info: {e}")
        return MeResponse(jid="Error", platform="Error")


@router.get("/group/list", response_model=GroupListResponse)
async def list_groups(
    session: Annotated[AsyncSession, Depends(get_db_async_session)],
) -> GroupListResponse:
    """
    List all groups from DB (Summary only).
    """
    try:
        logger.info("Fetching user groups from DB...")
        
        # Query groups with participant count
        stmt = (
            select(Group, func.count(GroupMember.sender_jid))
            .join(GroupMember, Group.group_jid == GroupMember.group_jid, isouter=True)
            .group_by(Group)
        )
        
        result = await session.exec(stmt)
        rows = result.all()
        
        summaries = []
        for group, count in rows:
            # Debug log to verify threshold values
            if group.auto_summary_threshold:
                logger.info(f"Group {group.group_jid} has threshold: {group.auto_summary_threshold}")
            
            summaries.append(GroupSummary(
                JID=group.group_jid, 
                Name=group.group_name,
                ParticipantCount=count,
                GroupCreated=group.created_at,
                AutoSummaryThreshold=group.auto_summary_threshold,
                EnableWebSearch=group.enable_web_search
            ))
        
        logger.info(f"Returning {len(summaries)} group summaries from DB")
        return GroupListResponse(
            code="200",
            message="Success (DB Cached)",
            results=DataResult(data=summaries)
        )
    except Exception as e:
        logger.error(f"Error listing groups from DB: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/group/ui", response_class=HTMLResponse)
async def get_group_ui():
    return r"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>WhatsApp Group Manager</title>
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/semantic-ui/2.5.0/semantic.min.css">
        <style>
            body {
                background-color: #f0f2f5;
                padding: 20px;
            }
            .main.container {
                background-color: #ffffff;
                padding: 2rem;
                border-radius: 8px;
                box-shadow: 0 4px 12px rgba(0,0,0,0.1);
                margin-top: 20px;
            }
            .ui.menu .item {
                font-weight: 600;
            }
            .form-section {
                display: none;
                margin-top: 20px;
            }
            .form-section.active {
                display: block;
            }
            .result-box {
                margin-top: 1.5rem;
                padding: 1rem;
                border-radius: 6px;
                display: none;
            }
        </style>
    </head>
    <body>
        <div class="ui container main">
            <h2 class="ui header center aligned" style="color: #00a884;">
                <i class="whatsapp icon"></i>
                <div class="content">
                    WhatsApp Group Manager
                    <div class="sub header" id="connected-as" style="display:none; margin-top: 5px;">
                        Connected as: <span id="my-jid" style="font-weight:bold;">...</span>
                    </div>
                </div>
            </h2>

            <div style="text-align: right; margin-bottom: 10px;">
                <a href="/bot/ui" class="ui labeled icon button teal">
                    <i class="robot icon"></i>
                    Bot Settings
                </a>
            </div>

            <div class="ui secondary pointing menu">
                <a class="item active" onclick="switchTab('create')">Create Group</a>
                <a class="item" onclick="switchTab('add')">Add Members</a>
                <a class="item" onclick="switchTab('message')">Send Messages</a>
                <a class="item" onclick="switchTab('list')">List Groups</a>
                <a class="item" onclick="switchTab('settings')">Settings</a>
            </div>

            <!-- Create Group Form -->
            <div id="create-section" class="form-section active">
                <div class="ui form">
                    <h4 class="ui dividing header">Create New Group</h4>
                    <div class="field">
                        <label>Group Name</label>
                        <input type="text" id="title" placeholder="e.g. My Awesome Group">
                    </div>
                    <div class="field">
                        <label>Sender Phone (Optional)</label>
                        <input type="text" id="sender-create" placeholder="e.g. 628123456789 (Leave empty for default)">
                    </div>
                    <div class="field">
                        <label>Participants</label>
                        <textarea id="participants-create" rows="3" placeholder="628123456789&#10;628987654321"></textarea>
                        <div class="ui pointing label">
                            Enter phone numbers (with country code), one per line or comma-separated.
                        </div>
                    </div>
                    <button class="ui primary button" onclick="createGroup()">Create Group</button>
                </div>
                <div id="result-create" class="result-box"></div>
            </div>

            <!-- Add Members Form -->
            <div id="add-section" class="form-section">
                <div class="ui form">
                    <h4 class="ui dividing header">Add Members to Group</h4>
                    <div class="field">
                        <label>Group ID (JID)</label>
                        <input type="text" id="group-id" placeholder="e.g. 123456789@g.us">
                    </div>
                    <div class="field">
                        <label>Sender Phone (Optional)</label>
                        <input type="text" id="sender-add" placeholder="e.g. 628123456789 (Leave empty for default)">
                    </div>
                    <div class="field">
                        <label>Participants</label>
                        <textarea id="participants-add" rows="3" placeholder="628123456789&#10;628987654321"></textarea>
                        <div class="ui pointing label">
                            Enter phone numbers (with country code), one per line or comma-separated.
                        </div>
                    </div>
                    <div class="ui buttons">
                        <button class="ui primary button" id="btn-add-start" onclick="startAddParticipants()">Start Adding</button>
                        <button class="ui red button disabled" id="btn-add-stop" onclick="stopAddParticipants()">Stop</button>
                    </div>
                    
                    <div id="progress-container" style="display:none; margin-top: 15px;">
                        <div class="ui indicating progress" id="add-progress">
                            <div class="bar">
                                <div class="progress"></div>
                            </div>
                            <div class="label">Processing...</div>
                        </div>
                        <div id="current-status" style="font-style: italic; color: #666;"></div>
                    </div>
                </div>
                <div id="result-add" class="result-box"></div>
            </div>

            <!-- Send Messages Form -->
            <div id="message-section" class="form-section">
                <div class="ui form">
                    <h4 class="ui dividing header">Bulk Send Messages</h4>
                    <div class="field">
                        <label>Message</label>
                        <textarea id="message-text" rows="3" placeholder="Hello! This is a message."></textarea>
                    </div>
                    <div class="field">
                        <label>Phone Numbers</label>
                        <textarea id="phones-message" rows="3" placeholder="628123456789&#10;628987654321"></textarea>
                        <div class="ui pointing label">
                            Enter phone numbers (with country code), one per line or comma-separated.
                        </div>
                    </div>
                    <button class="ui primary button" onclick="sendMessages()">Send Messages</button>
                </div>
                <div id="result-message" class="result-box"></div>
            </div>

            <!-- List Groups Section -->
            <div id="list-section" class="form-section">
                <h4 class="ui dividing header">My Group List</h4>
                <div class="ui buttons">
                    <button class="ui teal button" onclick="listGroups()">
                        <i class="sync icon"></i> Refresh List
                    </button>
                    <button class="ui blue button" onclick="syncGroupsDB()">
                        <i class="database icon"></i> Sync DB (Fix Missing Data)
                    </button>
                </div>
                
                <div id="result-list" style="margin-top: 20px; display: none;">
                    <table class="ui celled table" id="account_groups_table">
                        <thead>
                            <tr>
                                <th>Group ID</th>
                                <th>Name</th>
                                <th>Participants</th>
                                <th>Auto-Summary</th>
                                <th>Web Search</th>
                                <th>Created At</th>
                                <th>Action</th>
                            </tr>
                        </thead>
                        <tbody id="groups-table-body">
                            <!-- Rows will be inserted here -->
                        </tbody>
                    </table>
                </div>
            </div>

            <!-- Settings Section -->
            <div id="settings-section" class="form-section">
                <div class="ui form">
                    <h4 class="ui dividing header">Group Settings</h4>
                    <div class="field">
                        <label>Group ID (JID)</label>
                        <input type="text" id="settings-group-id" placeholder="e.g. 123456789@g.us">
                    </div>
                    <div class="field">
                        <label>Auto Summary Threshold (Messages)</label>
                        <input type="number" id="settings-threshold" placeholder="e.g. 50 (Leave empty to disable)">
                        <div class="ui pointing label">
                            Automatically summarize and send to group after this many messages.
                        </div>
                    </div>
                    <div class="field">
                        <div class="ui checkbox">
                            <input type="checkbox" id="settings-web-search">
                            <label>Enable Web Search</label>
                        </div>
                        <div class="ui pointing label">
                            Allow the bot to search the web to answer questions in this group.
                        </div>
                    </div>
                    <div class="ui buttons">
                        <button class="ui primary button" onclick="saveSettings()">Save Settings</button>
                        <div class="or"></div>
                        <button class="ui red button" onclick="disableAutoSummary()">Disable Auto-Summary</button>
                    </div>
                </div>
                <div id="result-settings" class="result-box"></div>
            </div>
        </div>

        <script src="https://cdnjs.cloudflare.com/ajax/libs/jquery/3.6.0/jquery.min.js"></script>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/semantic-ui/2.5.0/semantic.min.js"></script>
        <script>
            $(document).ready(function() {
                fetchMe();
            });

            async function fetchMe() {
                try {
                    const response = await fetch('/group/me');
                    const data = await response.json();
                    if (data.jid && data.jid !== 'Unknown' && data.jid !== 'Error') {
                        $('#my-jid').text(data.jid);
                        $('#connected-as').show();
                        
                        // Update placeholders
                        const cleanJid = data.jid.split('@')[0];
                        $('#sender-create').attr('placeholder', `Default: ${cleanJid}`);
                        $('#sender-add').attr('placeholder', `Default: ${cleanJid}`);
                    }
                } catch (e) {
                    console.error("Failed to fetch identity", e);
                }
            }

            function switchTab(tab) {
                $('.item').removeClass('active');
                $('.form-section').removeClass('active');
                
                if (tab === 'create') {
                    $('.item:nth-child(1)').addClass('active');
                    $('#create-section').addClass('active');
                } else if (tab === 'add') {
                    $('.item:nth-child(2)').addClass('active');
                    $('#add-section').addClass('active');
                } else if (tab === 'message') {
                    $('.item:nth-child(3)').addClass('active');
                    $('#message-section').addClass('active');
                } else if (tab === 'list') {
                    $('.item:nth-child(4)').addClass('active');
                    $('#list-section').addClass('active');
                } else if (tab === 'settings') {
                    $('.item:nth-child(5)').addClass('active');
                    $('#settings-section').addClass('active');
                }
            }

            function parseParticipants(text) {
                if (!text) return [];
                return text.split(/[\\n,]+/).map(p => p.trim()).filter(p => p);
            }

            async function createGroup() {
                const title = $('#title').val();
                const sender = $('#sender-create').val();
                const participantsText = $('#participants-create').val();
                const btn = $('#create-section button');
                const resultDiv = $('#result-create');
                
                const participants = parseParticipants(participantsText);
                
                if (!title || participants.length === 0) {
                    alert('Please provide a title and at least one participant.');
                    return;
                }

                setLoading(btn, resultDiv, true);

                try {
                    const body = { title, participants };
                    if (sender && sender.trim()) {
                        body.from = normalizeParticipant(sender);
                    }

                    const response = await fetch('/group/create', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(body)
                    });
                    
                    const data = await response.json();
                    handleResponse(response, data, resultDiv, 'Group created successfully! ID: ' + (data.results ? data.results.group_id : 'Unknown'));
                } catch (error) {
                    handleError(error, resultDiv);
                } finally {
                    setLoading(btn, resultDiv, false);
                }
            }

            let isAddingStopped = false;

            async function startAddParticipants() {
                const groupId = $('#group-id').val();
                const sender = $('#sender-add').val();
                const participantsText = $('#participants-add').val();
                const btnStart = $('#btn-add-start');
                const btnStop = $('#btn-add-stop');
                const resultDiv = $('#result-add');
                const progressContainer = $('#progress-container');
                const progressBar = $('#add-progress');
                const statusLabel = $('#current-status');
                
                const participants = parseParticipants(participantsText);
                
                if (!groupId || participants.length === 0) {
                    alert('Please provide a Group ID and at least one participant.');
                    return;
                }

                // Reset UI
                isAddingStopped = false;
                btnStart.addClass('loading disabled');
                btnStop.removeClass('disabled');
                resultDiv.hide().empty();
                progressContainer.show();
                progressBar.progress({ percent: 0 });
                statusLabel.text('Initializing...');

                const results = [];
                
                try {
                    // Step 1: Fetch existing members
                    statusLabel.text('Checking existing members...');
                    let existingMembers = new Set();
                    try {
                        const resp = await fetch(`/group/${encodeURIComponent(groupId)}/members`);
                        if (resp.ok) {
                            const data = await resp.json();
                            if (data.members) {
                                data.members.forEach(m => existingMembers.add(m.split('@')[0]));
                            }
                            console.log(`Found ${existingMembers.size} existing members via ${data.source}`);
                        }
                    } catch (e) {
                        console.warn("Failed to fetch existing members", e);
                    }

                    // Step 2: Process Loop
                    const total = participants.length;
                    
                    for (let i = 0; i < total; i++) {
                        if (isAddingStopped) {
                            statusLabel.text('Stopped by user.');
                            results.push({ participant: "STOPPED", status: "ABORTED", message: "User stopped the process" });
                            break;
                        }

                        const p = participants[i];
                        const userPart = p.replace(/\D/g, ''); // simple cleanup
                        const pJid = normalizeParticipant(p);

                        // Update Progress
                        const percent = Math.round(((i) / total) * 100);
                        progressBar.progress({ percent: percent });
                        statusLabel.text(`Processing ${i+1}/${total}: ${p}`);

                        // Check Duplicate
                        if (existingMembers.has(userPart)) {
                            console.log(`Skipping ${p} (Already in group)`);
                            results.push({ participant: p, status: "200", message: "Skipped (Already in group)" });
                            continue;
                        }

                        // Add via API
                        try {
                            const body = { group_id: groupId, participants: [p] };
                            if (sender && sender.trim()) body.from = normalizeParticipant(sender);

                            const resp = await fetch('/group/participants/add', {
                                method: 'POST',
                                headers: { 'Content-Type': 'application/json' },
                                body: JSON.stringify(body)
                            });
                            
                            const data = await resp.json();
                            if (data.results && data.results.length > 0) {
                                results.push(data.results[0]);
                            } else {
                                results.push({ participant: p, status: "200", message: "Processed" });
                            }

                        } catch (e) {
                            console.error(e);
                            results.push({ participant: p, status: "500", message: e.message });
                        }

                        // Delay (only if not last and not stopped)
                        if (i < total - 1 && !isAddingStopped) {
                            const delay = Math.floor(Math.random() * (60 - 30 + 1) + 30);
                            for (let d = delay; d > 0; d--) {
                                if (isAddingStopped) break;
                                statusLabel.text(`Waiting ${d}s before next...`);
                                await new Promise(r => setTimeout(r, 1000));
                            }
                        }
                    }
                    
                    progressBar.progress({ percent: 100 });
                    statusLabel.text('Completed.');

                    // Generate Report
                    generateAndSaveReport(results);
                    
                    // Show Summary
                    let msg = '<strong>Results:</strong><br>';
                    results.forEach(r => {
                        const color = r.status === '200' ? 'green' : 'red';
                        msg += `<span style="color:${color}">${r.participant}: ${r.status} (${r.message})</span><br>`;
                    });
                    resultDiv.html(`<div class="ui message"><div class="header">Process Finished</div><p>${msg}</p></div>`).show();

                } catch (error) {
                    handleError(error, resultDiv);
                } finally {
                    btnStart.removeClass('loading disabled');
                    btnStop.addClass('disabled');
                }
            }

            function stopAddParticipants() {
                isAddingStopped = true;
                $('#current-status').text('Stopping...');
                $('#btn-add-stop').addClass('disabled');
            }

            async function generateAndSaveReport(results) {
                // Generate CSV
                let csvContent = "Phone,Status,Message\\n";
                results.forEach(r => {
                    const phone = (r.participant || "").replace(/,/g, "");
                    const status = r.status || "";
                    const message = (r.message || "").replace(/,/g, " ");
                    csvContent += `${phone},${status},${message}\\n`;
                });

                // Download Client Side
                const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
                const url = URL.createObjectURL(blob);
                const link = document.createElement("a");
                link.setAttribute("href", url);
                const timestamp = new Date().toISOString().slice(0,19).replace(/:/g,"-");
                const filename = `participants_report_${timestamp}.csv`;
                link.setAttribute("download", filename);
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);

                // Upload to Server
                try {
                    await fetch('/report/save', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ csv_content: csvContent, filename: filename })
                    });
                    console.log("Report saved to server.");
                } catch (e) {
                    console.error("Failed to save report to server", e);
                }
            }

            function normalizeParticipant(phone) {
                let clean = phone.replace("+", "").replace("-", "").replace(" ", "").trim();
                if (clean.indexOf("@") === -1) {
                    return clean + "@s.whatsapp.net";
                }
                return clean;
            }

            async function sendMessages() {
                const message = $('#message-text').val();
                const phonesText = $('#phones-message').val();
                const btn = $('#message-section button');
                const resultDiv = $('#result-message');
                
                const phones = parseParticipants(phonesText);
                
                if (!message || phones.length === 0) {
                    alert('Please provide a message and at least one phone number.');
                    return;
                }

                setLoading(btn, resultDiv, true);

                try {
                    const response = await fetch('/message/bulk-send', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ message, phones })
                    });
                    
                    const data = await response.json();
                    
                    if (data.results && Array.isArray(data.results)) {
                        let msg = '<strong>Results:</strong><br>';
                        data.results.forEach(r => {
                            const color = r.status === '200' ? 'green' : 'red';
                            msg += `<span style="color:${color}">${r.phone}: ${r.status} (${r.message})</span><br>`;
                        });
                        handleResponse(response, data, resultDiv, msg);
                    } else {
                        handleResponse(response, data, resultDiv, 'Messages sent successfully!');
                    }
                } catch (error) {
                    handleError(error, resultDiv);
                } finally {
                    setLoading(btn, resultDiv, false);
                }
            }

            async function saveSettings() {
                const groupId = $('#settings-group-id').val();
                const thresholdVal = $('#settings-threshold').val();
                const enableWebSearch = $('#settings-web-search').is(':checked');
                const btn = $('#settings-section button');
                const resultDiv = $('#result-settings');
                
                if (!groupId) {
                    alert('Please provide a Group ID.');
                    return;
                }

                setLoading(btn, resultDiv, true);

                try {
                    const threshold = thresholdVal ? parseInt(thresholdVal) : null;
                    const body = { 
                        group_id: groupId, 
                        auto_summary_threshold: threshold,
                        enable_web_search: enableWebSearch
                    };

                    const response = await fetch('/group/settings', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(body)
                    });
                    
                    const data = await response.json();
                    handleResponse(response, data, resultDiv, data.message || 'Settings saved successfully!');
                } catch (error) {
                    handleError(error, resultDiv);
                } finally {
                    setLoading(btn, resultDiv, false);
                }
            }

            async function disableAutoSummary() {
                const groupId = $('#settings-group-id').val();
                const btn = $('#settings-section button');
                const resultDiv = $('#result-settings');
                
                if (!groupId) {
                    alert('Please provide a Group ID.');
                    return;
                }

                if (!confirm('Are you sure you want to disable auto-summary for this group?')) {
                    return;
                }

                setLoading(btn, resultDiv, true);

                try {
                    const body = { group_id: groupId, auto_summary_threshold: null };

                    const response = await fetch('/group/settings', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(body)
                    });
                    
                    const data = await response.json();
                    handleResponse(response, data, resultDiv, 'Auto-summary disabled successfully!');
                    $('#settings-threshold').val('');
                } catch (error) {
                    handleError(error, resultDiv);
                } finally {
                    setLoading(btn, resultDiv, false);
                }
            }

            async function syncGroupsDB() {
                const btn = $('#list-section .blue.button');
                btn.addClass('loading disabled');
                try {
                    const response = await fetch('/group/sync', { method: 'POST' });
                    const data = await response.json();
                    if (response.ok) {
                        alert('Groups synced to DB successfully!');
                    } else {
                        alert('Sync failed: ' + (data.detail || data.message));
                    }
                } catch (e) {
                    alert('Sync error: ' + e.message);
                } finally {
                    btn.removeClass('loading disabled');
                }
            }

            async function listGroups() {
                const btn = $('#list-section button');
                const resultDiv = $('#result-list');
                const tbody = $('#groups-table-body');
                
                btn.addClass('loading disabled');
                resultDiv.hide();
                tbody.empty();

                try {
                    const response = await fetch('/group/list');
                    const data = await response.json();
                    
                    if (response.ok && data.results && data.results.data) {
                        data.results.data.forEach(g => {
                            const created = g.GroupCreated ? new Date(g.GroupCreated).toLocaleString() : '-';
                            
                            let autoSummaryHtml = '-';
                            if (g.AutoSummaryThreshold) {
                                autoSummaryHtml = `
                                    <div class="ui label">
                                        ${g.AutoSummaryThreshold} msgs
                                        <i class="delete icon" onclick="disableAutoSummaryForGroup('${g.JID}')"></i>
                                    </div>
                                `;
                            }

                            const webSearchHtml = g.EnableWebSearch ? '<i class="check circle icon green"></i> Enabled' : '<i class="times circle icon red"></i> Disabled';

                            const row = `
                                <tr>
                                    <td style="font-family:monospace;">${g.JID}</td>
                                    <td>${g.Name || '(No Name)'}</td>
                                    <td>${g.ParticipantCount}</td>
                                    <td>${autoSummaryHtml}</td>
                                    <td>${webSearchHtml}</td>
                                    <td>${created}</td>
                                    <td>
                                        <button class="ui mini basic button" onclick="copyToClipboard('${g.JID}')">
                                            <i class="copy icon"></i> Copy ID
                                        </button>
                                        <button class="ui mini basic button" onclick="openSettings('${g.JID}', ${g.AutoSummaryThreshold}, ${g.EnableWebSearch})">
                                            <i class="cog icon"></i> Settings
                                        </button>
                                    </td>
                                </tr>
                            `;
                            tbody.append(row);
                        });
                        resultDiv.show();
                    } else {
                        // Handle FastAPI error format (detail) or standard format (message)
                        const errorMsg = data.detail || data.message || 'Unknown error';
                        alert('Failed to fetch groups: ' + errorMsg);
                    }
                } catch (error) {
                    console.error(error);
                    alert('Error fetching groups: ' + error.message);
                } finally {
                    btn.removeClass('loading disabled');
                }
            }

            async function disableAutoSummaryForGroup(groupId) {
                if (!confirm(`Are you sure you want to disable auto-summary for group ${groupId}?`)) {
                    return;
                }

                const btn = $('#list-section button'); // Use list section buttons for loading state
                btn.addClass('loading disabled');

                try {
                    const body = { group_id: groupId, auto_summary_threshold: null };

                    const response = await fetch('/group/settings', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(body)
                    });
                    
                    const data = await response.json();
                    if (response.ok) {
                        // Refresh the list to show updated status
                        listGroups(); 
                    } else {
                        alert('Failed to disable: ' + (data.message || data.detail));
                    }
                } catch (error) {
                    console.error(error);
                    alert('Error: ' + error.message);
                } finally {
                    btn.removeClass('loading disabled');
                }
            }

            function copyToClipboard(text) {
                navigator.clipboard.writeText(text).then(() => {
                    alert('Copied to clipboard!');
                }).catch(err => {
                    console.error('Failed to copy: ', err);
                });
            }

            function openSettings(groupId, threshold, enableWebSearch) {
                switchTab('settings');
                $('#settings-group-id').val(groupId);
                $('#settings-threshold').val(threshold || '');
                $('#settings-web-search').prop('checked', enableWebSearch === true);
            }

            function setLoading(btn, resultDiv, isLoading) {
                if (isLoading) {
                    resultDiv.show().html('<div class="ui active centered inline loader"></div>').css('background-color', 'transparent');
                    btn.addClass('loading disabled');
                } else {
                    btn.removeClass('loading disabled');
                }
            }

            function handleError(error, resultDiv) {
                console.error(error);
                resultDiv.html(`<div class="ui negative message"><div class="header">Error</div><p>${error.message}</p></div>`);
                resultDiv.show();
            }

            function handleResponse(response, data, resultDiv, successMsg) {
                if (response.ok) {
                    resultDiv.html(`<div class="ui success message"><div class="header">Success</div><p>${successMsg}</p></div>`);
                } else {
                    // Handle FastAPI error format (detail) or standard format (message)
                    const errorMsg = data.detail || data.message || 'Unknown error';
                    resultDiv.html(`<div class="ui negative message"><div class="header">Error</div><p>${errorMsg}</p></div>`);
                }
                resultDiv.show();
            }
        </script>
    </body>
    </html>
    """


@router.post("/group/create", response_model=CreateGroupResponse)
async def create_group(
    request: CreateGroupRequest,
    whatsapp: Annotated[WhatsAppClient, Depends(get_whatsapp)],
) -> CreateGroupResponse:
    """
    Create a new WhatsApp group with the specified participants.
    """
    try:
        # Normalize participants
        request.participants = [normalize_participant(p) for p in request.participants]
        logger.info(f"Creating group '{request.title}' with participants: {request.participants}")

        # If 'from' is not specified, fetch connected devices to get the default 'from' JID
        if not request.from_:
            # devices = await whatsapp.get_devices()
            # if devices.results and len(devices.results) > 0:
            #     request.from_ = devices.results[0].device
            #     logger.info(f"Using default 'from' JID: {request.from_}")
            pass
        else:
            # Normalize the provided 'from' JID
            request.from_ = normalize_participant(request.from_)
            logger.info(f"Using provided 'from' JID: {request.from_}")

        return await whatsapp.create_group(request)
    except Exception as e:
        logger.error(f"Error creating group: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/message/bulk-send", response_model=BulkSendMessageResponse)
async def bulk_send_message(
    request: BulkSendMessageRequest,
    whatsapp: Annotated[WhatsAppClient, Depends(get_whatsapp)],
) -> BulkSendMessageResponse:
    """
    Send a message to multiple phone numbers with a delay.
    """
    try:
        # Normalize phones
        request.phones = [normalize_participant(p) for p in request.phones]
        logger.info(f"Sending bulk message to {len(request.phones)} recipients")

        all_results = []
        
        # Process phones one by one with delay
        for i, phone in enumerate(request.phones):
            try:
                logger.info(f"Sending message to {phone} ({i+1}/{len(request.phones)})")
                
                send_request = SendMessageRequest(
                    phone=phone,
                    message=request.message
                )
                
                await whatsapp.send_message(send_request)
                
                all_results.append(BulkSendMessageResult(
                    phone=phone,
                    status="200",
                    message="Sent"
                ))
            except Exception as e:
                error_msg = str(e)
                logger.error(f"Failed to send to {phone}: {error_msg}")
                
                status_code = "500"
                if "401" in error_msg or "Unauthorized" in error_msg:
                    status_code = "401"
                elif "429" in error_msg or "rate-overlimit" in error_msg:
                    status_code = "429"
                
                all_results.append(BulkSendMessageResult(
                    phone=phone,
                    status=status_code,
                    message=error_msg
                ))
                
                # Stop processing if we hit a rate limit or auth error
                if status_code in ["401", "429"] or "rate-overlimit" in error_msg:
                    logger.warning(f"Aborting batch due to critical error: {error_msg}")
                    all_results.append(BulkSendMessageResult(
                        phone="BATCH_ABORTED",
                        status="ABORTED",
                        message=f"Process stopped early due to error: {error_msg}"
                    ))
                    break

            # Wait 10 seconds between requests, but not after the last one
            if i < len(request.phones) - 1:
                await asyncio.sleep(10)

        return BulkSendMessageResponse(
            code="200",
            message="Batch processing completed",
            results=all_results
        )

    except Exception as e:
        logger.error(f"Error sending bulk messages: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/group/participants/add", response_model=ManageParticipantResponse)
async def add_participants(
    request: ManageParticipantRequest,
    whatsapp: Annotated[WhatsAppClient, Depends(get_whatsapp)],
    session: Annotated[AsyncSession, Depends(get_db_async_session)],
) -> ManageParticipantResponse:
    """
    Add participants to an existing WhatsApp group.
    """
    try:
        # Normalize inputs
        request.group_id = normalize_group_id(request.group_id)
        request.participants = [normalize_participant(p) for p in request.participants]
        logger.info(f"Adding participants to group '{request.group_id}': {request.participants}")

        # Determine 'from' JID
        from_jid = request.from_
        if from_jid:
            from_jid = normalize_participant(from_jid)
            logger.info(f"Using provided 'from' JID: {from_jid}")
        
        # Optimization: Check DB first for existing participants
        existing_user_parts = set()
        db_check_success = False
        try:
            logger.info(f"Checking DB for existing members in {request.group_id}...")
            stmt = select(GroupMember.sender_jid).where(GroupMember.group_jid == request.group_id)
            result = await session.exec(stmt)
            db_members = result.all()
            
            if db_members:
                 existing_user_parts = {m.split('@')[0] for m in db_members}
                 logger.info(f"Found {len(existing_user_parts)} members in DB.")
                 db_check_success = True
            else:
                 logger.info("No members found in DB.")
        except Exception as e:
            logger.error(f"DB check failed: {e}")

        # Fallback to API if DB check failed or returned nothing
        if not db_check_success:
            try:
                logger.info(f"Fetching group info from API for {request.group_id}...")
                # We have to fetch all groups because there isn't a specific get_group endpoint exposed yet
                groups_response = await whatsapp.get_user_groups()
                if groups_response.results and groups_response.results.data:
                    target_group = next((g for g in groups_response.results.data if g.JID == request.group_id), None)
                    if target_group:
                        if target_group.Participants:
                            # Store just the user part (phone number) for robust comparison
                            existing_user_parts = {p.JID.split('@')[0] for p in target_group.Participants}
                            logger.info(f"Found {len(existing_user_parts)} existing participants in group {request.group_id}")
                            logger.info(f"Sample existing participants: {list(existing_user_parts)[:5]}")
                        else:
                            logger.warning(f"Target group {request.group_id} found but has no participants list")
                    else:
                        logger.warning(f"Target group {request.group_id} not found in user groups list")
            except Exception as e:
                logger.warning(f"Failed to fetch group info from API, proceeding without duplicate check: {e}")

        all_results = []
        
        # Process participants one by one with delay
        # NOTE: If client-side loop is used, this loop will only run once per request
        for i, participant in enumerate(request.participants):
            # Check if already in group (compare user parts)
            participant_user_part = participant.split('@')[0]
            if participant_user_part in existing_user_parts:
                msg = f"Participant {participant} (user: {participant_user_part}) is already in the group. Skipping add and wait."
                logger.info(msg)
                print(msg, flush=True)
                all_results.append(ManageParticipantResult(
                    participant=participant,
                    status="200",
                    message="Skipped (Already in group)"
                ))
                continue
            
            logger.info(f"Participant {participant} NOT found in existing list. Proceeding to add.")

            single_request = ManageParticipantRequest(
                group_id=request.group_id,
                participants=[participant],
                from_=from_jid
            )
            
            try:
                logger.info(f"Adding participant {participant} ({i+1}/{len(request.participants)})")
                response = await whatsapp.add_participants(single_request)
                if response.results:
                    # Override the participant ID with the requested JID for clarity in the UI
                    # (WhatsApp sometimes returns LIDs which are confusing for users)
                    for res in response.results:
                        res.participant = participant
                    all_results.extend(response.results)
                else:
                    # If no results returned, assume success or unknown
                    all_results.append(ManageParticipantResult(
                        participant=participant,
                        status="200",
                        message="Processed (No details)"
                    ))
            except Exception as e:
                error_msg = str(e)
                logger.error(f"Failed to add {participant}: {error_msg}")
                
                status_code = "500"
                if "401" in error_msg or "Unauthorized" in error_msg:
                    status_code = "401"
                elif "429" in error_msg or "rate-overlimit" in error_msg:
                    status_code = "429"
                
                all_results.append(ManageParticipantResult(
                    participant=participant,
                    status=status_code,
                    message=error_msg
                ))
                
                # Stop processing if we hit a rate limit or auth error
                if status_code in ["401", "429"] or "rate-overlimit" in error_msg:
                    logger.warning(f"Aborting batch due to critical error: {error_msg}")
                    all_results.append(ManageParticipantResult(
                        participant="BATCH_ABORTED",
                        status="ABORTED",
                        message=f"Process stopped early due to error: {error_msg}"
                    ))
                    break

            # Wait 30-60 seconds between requests to avoid blocking
            # Only wait if there are more items in THIS request
            if i < len(request.participants) - 1:
                delay = random.randint(30, 60)
                msg = f"Waiting {delay} seconds before processing next participant ({i+2}/{len(request.participants)})..."
                logger.info(msg)
                print(msg, flush=True) # Force output to console
                await asyncio.sleep(delay)

        # Generate CSV Report on Server (Only if batch > 1, otherwise client handles it)
        if len(request.participants) > 1:
            try:
                timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                report_filename = f"participants_report_{timestamp}.csv"
                # Save to src/reports so it syncs to host via volume mount
                reports_dir = os.path.join("src", "reports")
                os.makedirs(reports_dir, exist_ok=True)
                report_path = os.path.join(reports_dir, report_filename)
                
                with open(report_path, mode='w', newline='', encoding='utf-8') as file:
                    writer = csv.writer(file)
                    writer.writerow(["Phone", "Status", "Message"])
                    for res in all_results:
                        writer.writerow([res.participant, res.status, res.message])
                
                logger.info(f"CSV Report saved to {report_path}")
                
            except Exception as e:
                logger.error(f"Failed to save CSV report to server: {e}")

        return ManageParticipantResponse(
            code="200",
            message="Batch processing completed",
            results=all_results
        )

    except Exception as e:
        logger.error(f"Error adding participants: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/group/settings")
async def update_group_settings(
    request: GroupSettingsRequest,
    session: Annotated[AsyncSession, Depends(get_db_async_session)],
):
    """
    Update group settings (e.g. auto-summary threshold).
    """
    try:
        group_id = normalize_group_id(request.group_id)
        group = await session.get(Group, group_id)
        
        if not group:
            # If group doesn't exist in DB, we can't set settings for it yet
            # The user should sync groups first
            raise HTTPException(status_code=404, detail="Group not found in database. Please sync groups first.")
            
        if request.auto_summary_threshold is not None:
            group.auto_summary_threshold = request.auto_summary_threshold
        
        if request.enable_web_search is not None:
            group.enable_web_search = request.enable_web_search
        
        # If setting a threshold, automatically mark the group as managed
        # so the bot will respond to mentions in this group
        if request.auto_summary_threshold is not None and request.auto_summary_threshold > 0:
            group.managed = True
             
        session.add(group)
        await session.commit()
        
        return {"status": "success", "message": f"Settings updated for {group.group_name or group_id}"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating group settings: {e}")
        raise HTTPException(status_code=500, detail=str(e))
