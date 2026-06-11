"""Send the morning macro-economics digest by email.

Tries Resend HTTP API first (works in any cloud environment), then falls back
to Gmail SMTP (ports 465 → 587) for local use.

Environment variables:
  RESEND_API_KEY      - Resend.com API key (primary, cloud-friendly)
  DIGEST_RECIPIENT    - recipient address(es), comma-separated (required)
  GMAIL_ADDRESS       - Gmail sender (SMTP fallback only)
  GMAIL_APP_PASSWORD  - 16-char Gmail App Password (SMTP fallback only)

Usage:
  python send_email.py --subject "2026-06-09 매크로 경제 브리핑" --body-file digest.html
"""
import argparse
import json
import os
import smtplib
import sys
import urllib.request
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

SMTP_HOST = "smtp.gmail.com"
RESEND_FROM = "onboarding@resend.dev"


def _send_resend(api_key, recipients, subject, html_body):
    """Send via Resend HTTP API (HTTPS port 443 — never blocked)."""
    payload = json.dumps({
        "from": RESEND_FROM,
        "to": recipients,
        "subject": subject,
        "html": html_body,
    }).encode("utf-8")
    req = urllib.request.Request(
        "https://api.resend.com/emails",
        data=payload,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        result = json.loads(resp.read())
    print(f"[info] sent via Resend API to {recipients} (id: {result.get('id', '?')})")


def _send_smtp(sender, app_password, recipients, subject, html_body):
    """Gmail SMTP fallback: try port 465 then 587."""
    if "<meta charset" not in html_body.lower():
        html_body = '<meta charset="utf-8">\n' + html_body
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = ", ".join(recipients)
    msg.attach(MIMEText(html_body, "html", "utf-8"))
    msg_str = msg.as_string()

    errors = []
    for port, use_ssl in [(465, True), (587, False)]:
        try:
            if use_ssl:
                ctx = smtplib.SMTP_SSL(SMTP_HOST, port, timeout=30)
            else:
                ctx = smtplib.SMTP(SMTP_HOST, port, timeout=30)
            with ctx as s:
                if not use_ssl:
                    s.ehlo(); s.starttls(); s.ehlo()
                s.login(sender, app_password)
                s.sendmail(sender, recipients, msg_str)
            print(f"[info] sent via SMTP port {port} to {recipients}")
            return
        except Exception as e:
            errors.append(f"port {port}: {e}")

    sys.exit("[error] all SMTP attempts failed:\n" + "\n".join(errors))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--subject", required=True)
    parser.add_argument("--body-file", help="Path to HTML file. Reads stdin if omitted.")
    args = parser.parse_args()

    recipient_str = os.environ.get("DIGEST_RECIPIENT") or os.environ.get("GMAIL_ADDRESS")
    if not recipient_str:
        sys.exit("[error] DIGEST_RECIPIENT environment variable is required")
    recipients = [r.strip() for r in recipient_str.split(",") if r.strip()]

    if args.body_file:
        with open(args.body_file, encoding="utf-8") as f:
            html_body = f.read()
    else:
        html_body = sys.stdin.buffer.read().decode("utf-8")

    resend_key = os.environ.get("RESEND_API_KEY", "")
    if resend_key:
        _send_resend(resend_key, recipients, args.subject, html_body)
        return

    # SMTP fallback
    sender = os.environ.get("GMAIL_ADDRESS")
    app_password = os.environ.get("GMAIL_APP_PASSWORD", "").replace(" ", "")
    if not sender or not app_password:
        sys.exit("[error] Set RESEND_API_KEY, or both GMAIL_ADDRESS and GMAIL_APP_PASSWORD")
    _send_smtp(sender, app_password, recipients, args.subject, html_body)


if __name__ == "__main__":
    main()
