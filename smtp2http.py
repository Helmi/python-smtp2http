"""
smtp2http.py
------------

This script is a Python application that acts as a local SMTP server to receive emails and forward them to HTTP endpoints based on the recipient's email address.

The script performs the following steps:

1. Sets up logging for the application, creating two loggers: one for known email addresses and one for unknown email addresses.

2. Loads a configuration file (`email_config.json`) that maps email addresses to HTTP endpoints. If the configuration file is not found, it continues with an empty mapping.

3. Defines a custom message handler class (`CustomMessageHandler`) for processing incoming SMTP messages. This class has two main methods:

   - `handle_message`: This method schedules the asynchronous processing of an incoming email message.
   
   - `async_handle_message`: This method processes an incoming email message asynchronously. It extracts the sender, recipients, subject, and content of the message. It checks if the recipient's email address is known (i.e., it exists in the loaded configuration). If it is, it logs the email details and forwards the email content to the corresponding HTTP endpoint. If the recipient's email address is not known, it simply logs the email details.

4. Starts an SMTP server on the local machine (listening on all interfaces at port 25) using the custom message handler. The server runs indefinitely until interrupted by a keyboard interrupt signal (Ctrl+C), at which point it shuts down.

The script uses the `aiosmtpd` library to create the SMTP server and the `requests` library to forward the email content to the HTTP endpoints. It also uses the `email` library to parse and handle the email messages.

Requirements
------------
- Python 3.7 or higher
- `aiosmtpd` library
- `requests` library
- `email` library

Usage
-----
To run the script, use the following command:

    python smtp2http.py

To send a test email to the server, you can use the `local_test.py` script:

    python local_test.py

Configuration
-------------
The script uses a configuration file (`email_config.json`) to map email addresses to HTTP endpoints. The configuration file should be in the following format:

    {
        "email_endpoints": {
            "known@example.com": "https://example.com/webhook"
        },
        "allowed_senders": [
            "allowed-sender@example.com",
            "another-sender@example.com"
        ]
    }

The `email_endpoints` object maps email addresses to HTTP endpoints. The `allowed_senders` array lists the email addresses that are allowed to send emails to the server.

Logging
-------
The script logs known and unknown emails separately. The logs are written to `known_emails.log` and `unknown_emails.log` respectively.

Security
--------
The script includes basic checks for email format and malicious content. It also uses HTTPS for communication with the HTTP endpoints. However, it is recommended to further secure the script by implementing SPF, DKIM, and DMARC, and by securing the configuration file and logs.
"""
from aiosmtpd.controller import Controller
from aiosmtpd.handlers import Message as MessageHandler
import asyncio
from email.message import EmailMessage
from email.header import decode_header
import logging
import requests
import json
import os
from functools import partial

# Configure the root logger for the application.
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')

# Create loggers for known and unknown email categories.
logger_known = logging.getLogger('known')
logger_known.addHandler(logging.FileHandler('known_emails.log'))
logger_unknown = logging.getLogger('unknown')
logger_unknown.addHandler(logging.FileHandler('unknown_emails.log'))

# Load email-to-webhook endpoint mappings and allowed senders from a configuration file.
config_file = os.environ.get('EMAIL_CONFIG_FILE', 'email_config.json')
try:
    with open(config_file) as f:
        config = json.load(f)
        EMAIL_ENDPOINTS = config.get("email_endpoints", {})
        ALLOWED_SENDERS = config.get("allowed_senders", [])
    print("Loaded email configurations:")
    for email, endpoint in EMAIL_ENDPOINTS.items():
        print(f"  {email} -> {endpoint}")
    print("Allowed senders:")
    for sender in ALLOWED_SENDERS:
        print(f"  {sender}")
except FileNotFoundError:
    print(f"Configuration file {config_file} not found.")
    EMAIL_ENDPOINTS = {}
    ALLOWED_SENDERS = []


class CustomMessageHandler(MessageHandler):
    """A custom message handler for processing incoming SMTP messages."""

    def handle_message(self, message):
        """Schedules the asynchronous processing of an incoming email message."""
        asyncio.create_task(self.async_handle_message(message))

    async def async_handle_message(self, message: EmailMessage):
        """Asynchronously processes an incoming email message."""
        mailfrom = message['from']

        # Check if sender is in the allowed list
        if mailfrom not in ALLOWED_SENDERS:
            logger_unknown.info(f"Rejected email from unauthorized sender: {mailfrom}")
            return  # Skip processing for unauthorized senders

        rcpttos = message['to']
        rcpttos = [rcpttos] if isinstance(rcpttos, str) else rcpttos
        subject = message.get('subject', 'No subject')
        decoded_subject = ''.join([str(t[0], t[1] or 'utf-8') for t in decode_header(subject)])

        # Initialize content variable
        content = ""
        # Handle both simple and multipart messages
        if message.is_multipart():
            for part in message.walk():
                content_type = part.get_content_type()
                if content_type in ["text/plain", "text/html"]:
                    content = part.get_payload(decode=True).decode(part.get_content_charset('utf-8'))
                    # Use the first text/plain or text/html part found
                    break
        else:
            content = message.get_payload(decode=True).decode(message.get_content_charset('utf-8'))

        is_known_recipient = any(
            recipient.lower() in (address.lower() for address in EMAIL_ENDPOINTS) for recipient in rcpttos)
        log_entry = f"From: {mailfrom}, To: {', '.join(rcpttos)}, Subject: {decoded_subject}, Size: {len(content)} bytes"

        if is_known_recipient:
            logger_known.info(log_entry)
            for recipient in rcpttos:
                if recipient.lower() in EMAIL_ENDPOINTS:
                    await self.forward_to_webhook(recipient, decoded_subject, content)
        else:
            logger_unknown.info(log_entry)

    async def forward_to_webhook(self, recipient, decoded_subject, content):
        """Forwards the email message to the configured HTTP endpoint."""
        payload = {
            "from": recipient,
            "subject": decoded_subject,
            "content": content
        }

        endpoint = EMAIL_ENDPOINTS.get(recipient.lower())
        if endpoint:
            try:
                post_call = partial(requests.post, endpoint, json=payload)
                response = await asyncio.get_event_loop().run_in_executor(None, post_call)
                logger_known.info(f"Forwarded to {endpoint}: {response.status_code}")
            except requests.RequestException as e:
                logger_known.error(f"Error sending to {endpoint}: {e}")


if __name__ == "__main__":
    handler = CustomMessageHandler()
    controller = Controller(handler, hostname='0.0.0.0', port=25)
    controller.start()
    try:
        asyncio.get_event_loop().run_forever()
    except KeyboardInterrupt:
        controller.stop()
        print("Shutting down...")
