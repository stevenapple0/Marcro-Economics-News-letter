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


def _send(msg_str, sender, recipient, app_password):
    """Try port 465 (SSL) first, fall back to 587 (STARTTLS)."""
    errors = []
    # Port 465 — SSL
    try:
        with smtplib.SMTP_SSL(SMTP_HOST, 465, timeout=30) as s:
            s.login(sender, app_password)
            s.sendmail(sender, [recipient], msg_str)
        print(f"[info] sent via port 465 (SSL) to {recipient}")
        return
    except Exception as e:
        errors.append(f"port 465: {e}")

    # Port 587 — STARTTLS (cloud environments often block 465)
    try:
        with smtplib.SMTP(SMTP_HOST, 587, timeout=30) as s:
            s.ehlo()
            s.starttls()
            s.ehlo()
            s.login(sender, app_password)
            s.sendmail(sender, [recipient], msg_str)
        print(f"[info] sent via port 587 (STARTTLS) to {recipient}")
        return
    except Exception as e:
        errors.append(f"port 587: {e}")

    sys.exit(f"[error] all SMTP attempts failed:\n" + "\n".join(errors))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--subject", required=True)
    parser.add_argument("--body-file", help="Path to HTML file with the email body. Reads stdin if omitted.")
    args = parser.parse_args()

    sender = os.environ.get("GMAIL_ADDRESS")
    app_password = os.environ.get("GMAIL_APP_PASSWORD", "").replace(" ", "")
    recipient = os.environ.get("DIGEST_RECIPIENT", sender)

    if not sender or not app_password:
        sys.exit("[error] GMAIL_ADDRESS and GMAIL_APP_PASSWORD environment variables are required")

    if args.body_file:
        with open(args.body_file, encoding="utf-8") as f:
            html_body = f.read()
    else:
        html_body = sys.stdin.read()

    # Ensure email clients render Korean correctly regardless of their default charset.
    if "<meta charset" not in html_body.lower():
        html_body = '<meta charset="utf-8">\n' + html_body

    msg = MIMEMultipart("alternative")
    msg["Subject"] = args.subject
    msg["From"] = sender
    msg["To"] = recipient
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    _send(msg.as_string(), sender, recipient, app_password)


if __name__ == "__main__":
    main()
