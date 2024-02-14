"""
local_test.py
-------------

This script is a Python application that sends a test email to a local SMTP server. It's intended to be used for testing the `smtp2http.py` script.

The script performs the following steps:

1. Creates a plain text email message with a subject and body. The sender's email address is 'sender@example.com' and the recipient's email address is 'known@example.com'.

2. Sends the email message via a local SMTP server running on 'localhost' at port 25.

Requirements
------------
- Python 3.7 or higher
- `smtplib` library
- `email` library

Usage
-----
To run the script, use the following command:

    python local_test.py

This will send a test email to 'known@example.com' via the local SMTP server. If the email is sent successfully, it will print "Email sent successfully!" to the console.

Note: Before running this script, make sure the local SMTP server (`smtp2http.py`) is running and configured to accept emails from 'sender@example.com' and to 'known@example.com'.
"""
import smtplib
from email.mime.text import MIMEText
from email.header import Header

# Create a text/plain message
msg = MIMEText('This is the body of the test email.', 'plain', 'utf-8')
msg['Subject'] = Header('Test Email thing', 'utf-8')
msg['From'] = 'sender@example.com'
msg['To'] = 'known@example.com'

# Send the message via our local SMTP server.
with smtplib.SMTP('localhost', 25) as server:
    server.sendmail(msg['From'], [msg['To']], msg.as_string())
    print("Email sent successfully!")