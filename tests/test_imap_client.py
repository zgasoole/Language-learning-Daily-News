import imaplib

from app.services.feedback.imap_client import IMAPFeedbackClient


class _AlwaysBadClient:
    def select(self, _mailbox):
        raise imaplib.IMAP4.error("BAD")


class _QuotedOnlyClient:
    def select(self, mailbox):
        return ("OK", [b"1"]) if mailbox == '"[Gmail]/All Mail"' else ("NO", [b""])


def _build_client() -> IMAPFeedbackClient:
    return IMAPFeedbackClient(
        host="imap.gmail.com",
        port=993,
        username="u",
        password="p",
        subject_prefix="[LLDN]",
        allowed_senders=[],
        mailboxes=["INBOX"],
    )


def test_select_mailbox_returns_false_on_bad_command() -> None:
    client = _build_client()
    assert client._select_mailbox(_AlwaysBadClient(), "[Gmail]/All Mail") is False


def test_select_mailbox_tries_quoted_candidate() -> None:
    client = _build_client()
    assert client._select_mailbox(_QuotedOnlyClient(), "[Gmail]/All Mail") is True
