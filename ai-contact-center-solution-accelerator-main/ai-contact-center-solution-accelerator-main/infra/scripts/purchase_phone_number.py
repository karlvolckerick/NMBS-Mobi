#!/usr/bin/env python3

import argparse
import subprocess
import sys

from azure.communication.phonenumbers import (
    PhoneNumberAssignmentType,
    PhoneNumberCapabilities,
    PhoneNumberCapabilityType,
    PhoneNumbersClient,
    PhoneNumberType,
)
from azure.identity import DefaultAzureCredential


def get_acs_endpoint() -> str:
    """Get ACS endpoint from Terraform output."""
    try:
        result = subprocess.run(
            ["terraform", "-chdir=infra", "output", "-raw", "acs_name"],
            capture_output=True,
            text=True,
            check=True,
        )
        acs_name = result.stdout.strip()
        return f"https://{acs_name}.communication.azure.com"
    except subprocess.CalledProcessError as e:
        print(f"Failed to get ACS name from Terraform: {e.stderr}")
        print("Make sure you've run 'terraform -chdir=infra apply' first.")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Purchase an ACS phone number")
    parser.add_argument("--country", default="GB", help="Country code (default: GB)")
    parser.add_argument(
        "--type", dest="number_type", default="toll-free", choices=["toll-free", "geographic"], help="Number type"
    )
    parser.add_argument("--auto-approve", action="store_true", help="Skip confirmation")
    args = parser.parse_args()

    endpoint = get_acs_endpoint()
    print(f"ACS Endpoint: {endpoint}")

    client = PhoneNumbersClient(endpoint, DefaultAzureCredential())
    phone_type = PhoneNumberType.TOLL_FREE if args.number_type == "toll-free" else PhoneNumberType.GEOGRAPHIC
    capabilities = PhoneNumberCapabilities(
        calling=PhoneNumberCapabilityType.INBOUND_OUTBOUND,
        sms=PhoneNumberCapabilityType.NONE,
    )

    print(f"Searching for {args.country} {args.number_type} numbers...")
    search_poller = client.begin_search_available_phone_numbers(
        country_code=args.country,
        phone_number_type=phone_type,
        assignment_type=PhoneNumberAssignmentType.APPLICATION,
        capabilities=capabilities,
        quantity=1,
    )
    search_result = search_poller.result()

    if not search_result.phone_numbers:
        print("No phone numbers available. Try a different country or type.")
        sys.exit(1)

    phone_number = search_result.phone_numbers[0]
    cost = search_result.cost
    print(f"\nFound: {phone_number}")
    print(f"Type: {args.number_type}")
    if cost:
        print(f"Cost: {cost.amount} {cost.currency_code}")
    print("\nThis will incur charges to your Azure account.")

    if not args.auto_approve:
        confirm = input("Purchase this number? (yes/no): ").strip().lower()
        if confirm not in ["yes", "y"]:
            print("Purchase cancelled.")
            sys.exit(0)

    print("Purchasing...")
    purchase_poller = client.begin_purchase_phone_numbers(search_result.search_id)
    purchase_poller.result()

    print(f"\nSuccess! Purchased: {phone_number}")
    print("The number is now associated with your ACS resource.")
    print("Incoming calls will route via Event Grid to your app.")


if __name__ == "__main__":
    main()
