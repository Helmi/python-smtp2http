# SMTP to HTTP Email Forwarder

This project contains a Python application that acts as a local SMTP server to receive emails and forward them to HTTP endpoints based on the recipient's email address. The intended use is for tools like n8n or other Webhook receivers to be able to receive email via SMTP. 

### Content decoding

Currently the script only supports decoding of `text/plain` and `text/html` content types. It will ignore other content types.

### Test script

The repo also includes a script for easy sending of test emails to the main script locally.

## Requirements

- Python 3.7 or higher
- `aiosmtpd` library
- `requests` library
- `email` library

## Installation

Clone the repository and install the required Python libraries.

```bash
git clone https://github.com/yourusername/yourrepository.git
cd yourrepository
pip install -r requirements.txt
```

## Usage

To run the SMTP server, use the following command:

```bash
python smtp2http.py
```

To send a test email to the server, you can use the `local_test.py` script:

```bash
python local_test.py
```

Modify the file itself to make it fit your testing needs.

## Configuration

The script uses a configuration file (`email_config.json`) to map email addresses to HTTP endpoints. The configuration file should be in the following format:

```json
{
    "email_endpoints": {
        "known@example.com": "https://example.com/webhook"
    },
    "allowed_senders": [
        "allowed-sender@example.com",
        "another-sender@example.com"
    ]
}
```

## Logging

The script logs known and unknown emails separately. The logs are written to `known_emails.log` and `unknown_emails.log` respectively.
Logging may as well seen as WIP. I'm not happy with it yet but wanted to have basic logging going early.

## Security

The script includes basic checks for email format and malicious content. It also uses HTTPS for communication with the HTTP endpoints. However, it is recommended to further secure the script by implementing SPF, DKIM, and DMARC, and by securing the configuration file and logs.

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

## License

[MIT](https://choosealicense.com/licenses/mit/)