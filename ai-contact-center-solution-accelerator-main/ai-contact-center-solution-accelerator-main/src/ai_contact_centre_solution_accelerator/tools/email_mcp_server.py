"""ACS Email MCP Server.

Sends emails via Azure Communication Services Email.
Runs as a stdio MCP process inside the main container.

Required environment variables:
  ACS_CONNECTION_STRING  - ACS Communication Services connection string
  ACS_EMAIL_SENDER       - Verified sender address (e.g. DoNotReply@<domain>.azurecomm.net)
"""

import os

from azure.communication.email import EmailClient
from fastmcp import FastMCP

mcp = FastMCP("NMBS Email Sender")

_client: EmailClient | None = None
_sender: str | None = None


def _get_client() -> tuple[EmailClient, str]:
    global _client, _sender
    if _client is None:
        conn_str = os.environ["ACS_CONNECTION_STRING"]
        _client = EmailClient.from_connection_string(conn_str)
        _sender = os.environ["ACS_EMAIL_SENDER"]
    return _client, _sender


@mcp.tool
def send_email(to_address: str, subject: str, body: str) -> dict:
    """Send an email to a caller.

    Use this to send ticket confirmations, journey timetables, disruption updates,
    or any other helpful information the caller requests.
    Always ask the caller for their email address before calling this tool.

    Args:
        to_address: Recipient email address.
        subject: Email subject line.
        body: Plain text email body. Use newlines to separate sections.
    """
    client, sender = _get_client()
    message = {
        "senderAddress": sender,
        "recipients": {
            "to": [{"address": to_address}],
        },
        "content": {
            "subject": subject,
            "plainText": body,
        },
    }
    try:
        poller = client.begin_send(message)
        result = poller.result()
        return {"status": "sent", "message_id": result.get("id", "unknown")}
    except Exception as exc:
        return {"status": "error", "message": str(exc)}


if __name__ == "__main__":
    mcp.run(transport="stdio")
