from unittest.mock import AsyncMock, MagicMock

import pytest

from app import sender
from app.browser import AuthenticationError
from app.douyin import PageOperationError


@pytest.mark.asyncio
@pytest.mark.parametrize("url,payload,rejected", [
    ("https://imapi.douyin.com/v1/message/send", {"decision": "KICK"}, True),
    ("https://imapi.douyin.com/v1/message/send", {"status": 0}, False),
    ("https://example.com/v1/message/send", {"decision": "KICK"}, False),
])
async def test_send_rejection_overrides_generic_failure(monkeypatch, url, payload, rejected):
    page = MagicMock()
    response = MagicMock(url=url)
    response.json = AsyncMock(return_value=payload)

    async def dispatch(*args):
        page.on.call_args.args[1](response)
        raise PageOperationError("bubble failed")

    monkeypatch.setattr(sender, "_send_message", dispatch)
    with pytest.raises(AuthenticationError if rejected else PageOperationError):
        await sender.send_message(page, None, None, {})
    page.remove_listener.assert_called_once()


@pytest.mark.asyncio
async def test_explicit_sticker_failure_does_not_publish_again(monkeypatch):
    monkeypatch.setattr(sender, "_sticker_resource_key", AsyncMock(return_value="sticker"))
    monkeypatch.setattr(sender, "_confirm_sticker_sent", AsyncMock(side_effect=sender.SendRejectedError("failed")))
    publish = AsyncMock()
    monkeypatch.setattr(sender, "_trigger_send", publish)
    with pytest.raises(sender.SendRejectedError):
        await sender._click_and_confirm_sticker(MagicMock(), AsyncMock(), ("a", ""), "test")
    publish.assert_not_awaited()
