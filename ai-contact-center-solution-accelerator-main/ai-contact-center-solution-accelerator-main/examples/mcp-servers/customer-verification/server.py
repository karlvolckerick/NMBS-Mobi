"""Customer Verification MCP Server.

A minimal example MCP server that demonstrates how to connect an external
service to the AI Contact Centre. Provides a single tool for looking up
customers by phone number.
"""

from fastmcp import FastMCP

mcp = FastMCP("Customer Verification")

CUSTOMERS = {
    "07700900001": {
        "customer_id": "CUST-001",
        "name": "Sarah Johnson",
        "email": "sarah.johnson@email.com",
        "account_status": "active",
    },
    "07700900002": {
        "customer_id": "CUST-002",
        "name": "James Smith",
        "email": "james.smith@email.com",
        "account_status": "active",
    },
    "07700900003": {
        "customer_id": "CUST-003",
        "name": "Emily Davis",
        "email": "emily.davis@email.com",
        "account_status": "suspended",
    },
}


@mcp.tool
def verify_customer(phone_number: str) -> dict:
    """Look up a customer by their phone number.

    Args:
        phone_number: Phone number with no spaces (e.g., "07700900001")

    Returns customer details if found, or a not-found message.
    """
    customer = CUSTOMERS.get(phone_number)
    if customer:
        return {"status": "verified", **customer}
    return {
        "status": "not_found",
        "message": f"No customer found with phone number {phone_number}",
    }


if __name__ == "__main__":
    mcp.run(transport="streamable-http", host="0.0.0.0", port=8001)
