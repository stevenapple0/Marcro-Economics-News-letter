"""Send the morning macro-economics digest by email via Gmail SMTP.

Reads the message body from a file (or stdin) and sends it as an HTML email.
Credentials come from environment variables so no secrets live in the repo:

  GMAIL_ADDRESS       - sender Gmail address (also used as recipient if
                        DIGEST_RECIPIENT is not set)
  GMAIL_APP_PASSWORD  - 16-char Gmail App Password (not the normal password)
  DIGEST_RECIPIENT    - optional, defaults to GMAIL_ADDRESS

Usage:
  python send_email.py --subject "2026-06-08 매크로 경제 브리핑" --body-file digest.html
  python send_email.py --subject "..." < digest.html
"""
import argparse
import os
import smtplib
import sys
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 465


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--subject", required=True)
    parser.add_argument("--body-file", help="Path to an HTML file with the email body. If omitted, reads from stdin.")
    args = parser.parse_args()

    sender = os.environ.get("GMAIL_ADDRESS")
    app_password = os.environ.get("GMAIL_APP_PASSWORD")
    recipient = os.environ.get("DIGEST_RECIPIENT", sender)

    if not sender or not app_password:
        sys.exit("[error] GMAIL_ADDRESS and GMAIL_APP_PASSWORD environment variables are required")

    if args.body_file:
        with open(args.body_file, encoding="utf-8") as f:
            html_body = f.read()
    else:
        html_body = sys.stdin.read()

    msg = MIMEMultipart("alternative")
    msg["Subject"] = args.subject
    msg["From"] = sender
    msg["To"] = recipient
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT) as server:
        server.login(sender, app_password)
        server.sendmail(sender, [recipient], msg.as_string())

    print(f"[info] sent digest to {recipient}")


if __name__ == "__main__":
    main()
