import time
import traceback
from imapclient import IMAPClient
import pyzmail

from agent import handle_question
from mailer import send_email
from config import (
    GMAIL_ADDRESS,
    GMAIL_APP_PASSWORD,
    IMAP_SERVER,
)


# -----------------------------
# Helper functions
# -----------------------------

def is_no_reply(sender: str) -> bool:
    """
    Ignore automated/system-like senders.
    """
    blocked_keywords = [
        "no-reply",
        "noreply",
        "donotreply",
        "do-not-reply",
        "mailer-daemon",
        "postmaster",
        "bounce",
    ]
    sender_lower = sender.lower()
    return any(k in sender_lower for k in blocked_keywords)


def extract_text(message: pyzmail.PyzMessage) -> str:
    """
    Safely extract plain text body from email.
    """
    if message.text_part:
        return message.text_part.get_payload().decode(
            message.text_part.charset or "utf-8",
            errors="ignore",
        )
    elif message.html_part:
        return message.html_part.get_payload().decode(
            message.html_part.charset or "utf-8",
            errors="ignore",
        )
    return ""


# -----------------------------
# Main mailbox processing
# -----------------------------

def check_mailbox():
    print("📥 Connecting to mailbox...")

    with IMAPClient(IMAP_SERVER) as server:
        server.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
        server.select_folder("INBOX")

        # fetch unread messages
        uids = server.search(["UNSEEN"])

        if not uids:
            print("📭 No new emails.")
            return

        for uid in uids:
            raw = server.fetch(uid, ["RFC822"])[uid][b"RFC822"]
            msg = pyzmail.PyzMessage.factory(raw)

            sender = msg.get_addresses("from")[0][1]
            subject = msg.get_subject() or "(no subject)"
            body = extract_text(msg).strip()

            print(f"✉️ Processing email from {sender} | Subject: {subject}")

            # -----------------------------
            # Skips
            # -----------------------------
            if is_no_reply(sender):
                print(f"⚠️ Skipping system/no-reply email from {sender}")
                server.add_flags(uid, ["\\Seen"])
                continue

            if not body or len(body) < 5:
                print(f"⚠️ Skipping empty/short email from {sender}")
                server.add_flags(uid, ["\\Seen"])
                continue

            # -----------------------------
            # Handle using agent
            # -----------------------------
            try:
                # IMPORTANT:
                # handle_question() already includes the disclaimer
                reply_body = handle_question(sender, body)

                send_email(
                    to_address=sender,
                    subject=f"Re: {subject}",
                    body=reply_body,
                )

                print(f"✅ Replied to {sender}")

            except Exception as e:
                print(f"❌ Error processing email from {sender}: {repr(e)}")
                traceback.print_exc()

            finally:
                # mark as read in any case
                server.add_flags(uid, ["\\Seen"])


# -----------------------------
# Polling loop entry point
# -----------------------------

if __name__ == "__main__":
    print("📬 Email agent started. Polling inbox every 60 seconds...")

    while True:
        try:
            check_mailbox()
        except Exception as e:
            print("💥 Fatal error in polling loop:", repr(e))
            traceback.print_exc()

        time.sleep(60)
