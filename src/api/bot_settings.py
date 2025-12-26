"""
Bot Settings API - Manage DM auto-reply and other bot settings at runtime.
"""
import logging
import os
from typing import Optional
from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(tags=["bot-settings"])

# Path to .env file (relative to app root)
ENV_FILE_PATH = ".env"


class DMAutoReplySettings(BaseModel):
    """DM Auto-Reply settings model."""
    enabled: bool
    message: str


class DMAutoReplyResponse(BaseModel):
    """Response model for DM Auto-Reply settings."""
    status: str
    settings: DMAutoReplySettings


def read_env_file() -> dict[str, str]:
    """Read the .env file and return as a dictionary."""
    env_vars = {}
    if os.path.exists(ENV_FILE_PATH):
        with open(ENV_FILE_PATH, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, _, value = line.partition("=")
                    # Remove quotes if present
                    value = value.strip()
                    if (value.startswith('"') and value.endswith('"')) or \
                       (value.startswith("'") and value.endswith("'")):
                        value = value[1:-1]
                    env_vars[key.strip()] = value
    return env_vars


def write_env_file(env_vars: dict[str, str]) -> None:
    """Write the environment variables back to .env file, preserving comments."""
    lines = []
    existing_keys = set()
    
    # Read existing file to preserve comments and order
    if os.path.exists(ENV_FILE_PATH):
        with open(ENV_FILE_PATH, "r", encoding="utf-8") as f:
            for line in f:
                stripped = line.strip()
                if stripped and not stripped.startswith("#") and "=" in stripped:
                    key, _, _ = stripped.partition("=")
                    key = key.strip()
                    existing_keys.add(key)
                    if key in env_vars:
                        # Update the value
                        value = env_vars[key]
                        # Quote the value if it contains spaces or special chars
                        if " " in value or "'" in value:
                            value = f'"{value}"'
                        lines.append(f"{key}={value}\n")
                    else:
                        lines.append(line)
                else:
                    lines.append(line)
    
    # Add any new keys that weren't in the file
    for key, value in env_vars.items():
        if key not in existing_keys:
            if " " in value or "'" in value:
                value = f'"{value}"'
            lines.append(f"{key}={value}\n")
    
    with open(ENV_FILE_PATH, "w", encoding="utf-8") as f:
        f.writelines(lines)


@router.get("/bot/settings/dm-autoreply", response_model=DMAutoReplyResponse)
async def get_dm_autoreply_settings() -> DMAutoReplyResponse:
    """
    Get current DM auto-reply settings.
    """
    try:
        env_vars = read_env_file()
        
        enabled_str = env_vars.get("DM_AUTOREPLY_ENABLED", "false")
        enabled = enabled_str.lower() in ("true", "1", "yes")
        
        message = env_vars.get(
            "DM_AUTOREPLY_MESSAGE", 
            "Hello, I am not designed to answer to personal messages."
        )
        
        return DMAutoReplyResponse(
            status="success",
            settings=DMAutoReplySettings(enabled=enabled, message=message)
        )
    except Exception as e:
        logger.error(f"Error reading DM auto-reply settings: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/bot/settings/dm-autoreply", response_model=DMAutoReplyResponse)
async def update_dm_autoreply_settings(settings: DMAutoReplySettings) -> DMAutoReplyResponse:
    """
    Update DM auto-reply settings.
    
    Note: Changes are written to .env file but require a server restart to take effect
    in the running application (settings are cached at startup).
    """
    try:
        env_vars = read_env_file()
        
        # Update the settings
        env_vars["DM_AUTOREPLY_ENABLED"] = str(settings.enabled)
        env_vars["DM_AUTOREPLY_MESSAGE"] = settings.message
        
        write_env_file(env_vars)
        
        logger.info(f"Updated DM auto-reply settings: enabled={settings.enabled}")
        
        return DMAutoReplyResponse(
            status="success",
            settings=settings
        )
    except Exception as e:
        logger.error(f"Error updating DM auto-reply settings: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/bot/ui", response_class=HTMLResponse)
async def get_bot_settings_ui():
    """
    Bot Settings UI - Manage DM auto-reply and other bot settings.
    """
    return r"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Bot Settings</title>
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
                max-width: 800px;
            }
            .toggle-container {
                display: flex;
                align-items: center;
                gap: 15px;
                margin-bottom: 20px;
            }
            .status-indicator {
                display: inline-block;
                width: 12px;
                height: 12px;
                border-radius: 50%;
                margin-left: 8px;
            }
            .status-on {
                background-color: #21ba45;
                box-shadow: 0 0 8px #21ba45;
            }
            .status-off {
                background-color: #db2828;
                box-shadow: 0 0 8px #db2828;
            }
            .result-box {
                margin-top: 1.5rem;
                padding: 1rem;
                border-radius: 6px;
            }
            .back-link {
                margin-bottom: 20px;
            }
            .restart-notice {
                margin-top: 15px;
            }
        </style>
    </head>
    <body>
        <div class="ui container main">
            <div class="back-link">
                <a href="/group/ui" class="ui labeled icon button">
                    <i class="left arrow icon"></i>
                    Back to Group Manager
                </a>
            </div>

            <h2 class="ui header" style="color: #00a884;">
                <i class="robot icon"></i>
                <div class="content">
                    Bot Settings
                    <div class="sub header">Configure bot behavior for direct messages</div>
                </div>
            </h2>

            <div class="ui divider"></div>

            <!-- DM Auto-Reply Section -->
            <div class="ui segment">
                <h3 class="ui header">
                    <i class="reply icon"></i>
                    <div class="content">
                        DM Auto-Reply
                        <span class="status-indicator" id="status-indicator"></span>
                    </div>
                </h3>

                <div class="ui form" id="dm-form">
                    <div class="toggle-container">
                        <div class="ui toggle checkbox" id="dm-toggle">
                            <input type="checkbox" id="dm-enabled">
                            <label><strong>Enable Auto-Reply for Direct Messages</strong></label>
                        </div>
                    </div>
                    
                    <p class="ui text grey">
                        When enabled, the bot will automatically respond to direct messages (DMs) with the message below.
                        <br>
                        <small>Note: Users can still use <code>opt-out</code>, <code>opt-in</code>, and <code>status</code> commands in DMs.</small>
                    </p>

                    <div class="field">
                        <label>Auto-Reply Message</label>
                        <textarea id="dm-message" rows="4" placeholder="Enter the message to send when someone DMs the bot..."></textarea>
                    </div>

                    <button class="ui primary button" id="save-btn" onclick="saveSettings()">
                        <i class="save icon"></i>
                        Save Settings
                    </button>
                    <button class="ui button" onclick="loadSettings()">
                        <i class="refresh icon"></i>
                        Reset
                    </button>
                </div>

                <div id="result-box" class="result-box" style="display: none;"></div>

                <div class="ui warning message restart-notice" style="display: none;" id="restart-notice">
                    <i class="exclamation triangle icon"></i>
                    <strong>Restart Required:</strong> Settings have been saved to the configuration file. 
                    Please restart the web-server container for changes to take effect.
                    <br><br>
                    <code>docker restart wa_llm-web-server-1</code>
                </div>
            </div>

            <!-- Info Section -->
            <div class="ui info message">
                <div class="header">How DM Commands Work</div>
                <p>Users can send the following commands via direct message to the bot:</p>
                <ul class="list">
                    <li><code>opt-out</code> - Stop being tagged in bot-generated messages</li>
                    <li><code>opt-in</code> - Resume being tagged in bot-generated messages</li>
                    <li><code>status</code> - Check current opt-out status</li>
                </ul>
                <p>These commands always work, regardless of the auto-reply setting.</p>
            </div>
        </div>

        <script src="https://cdnjs.cloudflare.com/ajax/libs/jquery/3.6.0/jquery.min.js"></script>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/semantic-ui/2.5.0/semantic.min.js"></script>
        <script>
            $(document).ready(function() {
                // Initialize checkbox
                $('#dm-toggle').checkbox();
                
                // Load current settings
                loadSettings();
            });

            async function loadSettings() {
                const btn = $('#save-btn');
                btn.addClass('loading');
                
                try {
                    const response = await fetch('/bot/settings/dm-autoreply');
                    const data = await response.json();
                    
                    if (data.status === 'success' && data.settings) {
                        // Set checkbox state
                        if (data.settings.enabled) {
                            $('#dm-toggle').checkbox('check');
                        } else {
                            $('#dm-toggle').checkbox('uncheck');
                        }
                        
                        // Set message
                        $('#dm-message').val(data.settings.message);
                        
                        // Update status indicator
                        updateStatusIndicator(data.settings.enabled);
                    }
                } catch (error) {
                    console.error('Failed to load settings:', error);
                    showResult('error', 'Failed to load settings: ' + error.message);
                } finally {
                    btn.removeClass('loading');
                }
            }

            async function saveSettings() {
                const btn = $('#save-btn');
                const enabled = $('#dm-enabled').is(':checked');
                const message = $('#dm-message').val().trim();
                
                if (!message) {
                    showResult('warning', 'Please enter an auto-reply message.');
                    return;
                }

                btn.addClass('loading');
                
                try {
                    const response = await fetch('/bot/settings/dm-autoreply', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            enabled: enabled,
                            message: message
                        })
                    });
                    
                    const data = await response.json();
                    
                    if (response.ok && data.status === 'success') {
                        showResult('success', 'Settings saved successfully!');
                        updateStatusIndicator(enabled);
                        
                        // Show restart notice
                        $('#restart-notice').show();
                    } else {
                        showResult('error', 'Failed to save settings: ' + (data.detail || 'Unknown error'));
                    }
                } catch (error) {
                    console.error('Failed to save settings:', error);
                    showResult('error', 'Failed to save settings: ' + error.message);
                } finally {
                    btn.removeClass('loading');
                }
            }

            function updateStatusIndicator(enabled) {
                const indicator = $('#status-indicator');
                if (enabled) {
                    indicator.removeClass('status-off').addClass('status-on');
                    indicator.attr('title', 'Auto-reply is ON');
                } else {
                    indicator.removeClass('status-on').addClass('status-off');
                    indicator.attr('title', 'Auto-reply is OFF');
                }
            }

            function showResult(type, message) {
                const resultBox = $('#result-box');
                let className = 'ui message ';
                
                if (type === 'success') {
                    className += 'positive';
                } else if (type === 'error') {
                    className += 'negative';
                } else if (type === 'warning') {
                    className += 'warning';
                }
                
                resultBox.html(`<div class="${className}"><p>${message}</p></div>`);
                resultBox.show();
                
                // Hide after 5 seconds for success
                if (type === 'success') {
                    setTimeout(() => resultBox.fadeOut(), 5000);
                }
            }
        </script>
    </body>
    </html>
    """
