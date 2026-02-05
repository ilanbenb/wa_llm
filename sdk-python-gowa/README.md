# gowa-sdk

Async Python SDK for go-whatsapp-web-multidevice, with Pydantic models and webhook helpers.

## Install (local dev)

```bash
uv pip install -e ./sdk-python-gowa
```

## Quick start

```python
import asyncio
from gowa_sdk import GoWaClient, SendMessageRequest


async def main() -> None:
    async with GoWaClient(base_url="http://localhost:3000") as client:
        resp = await client.send_message(
            SendMessageRequest(phone="1234567890@s.whatsapp.net", message="Hello")
        )
        print(resp)


asyncio.run(main())
```

## Multi-device support (v8+)

Device scoping required: All device-scoped REST API calls now require either:

- `X-Device-Id` header, or
- `device_id` query parameter

If only one device is registered, it will be used as the default.

When running multiple devices, pass `device_id` on the client or per call. This is sent as the `X-Device-Id` header per the v8 API changes.

```python
async with GoWaClient(base_url="http://localhost:3000", device_id="device_id") as client:
    await client.get_status()
```

## Webhook parsing

```python
from gowa_sdk.webhooks import WebhookEnvelope, WebhookMessagePayload

envelope = WebhookEnvelope.model_validate(payload_dict)
if envelope.event == "message":
    message = WebhookMessagePayload.model_validate(envelope.payload)
    print(message.text)
```

## Docs reference

- OpenAPI spec: https://github.com/aldinokemal/go-whatsapp-web-multidevice/blob/main/docs/openapi.yaml
- Webhook payload: https://github.com/aldinokemal/go-whatsapp-web-multidevice/blob/main/docs/webhook-payload.md
- Releases: https://github.com/aldinokemal/go-whatsapp-web-multidevice/releases
