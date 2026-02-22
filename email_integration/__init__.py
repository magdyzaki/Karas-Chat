# Email Integration Module
from .imap_reader import read_messages_from_imap
from .ms_auth import acquire_token_interactive, get_account_email
from .ms_mail_reader import read_messages_from_folder, read_new_messages_from_inbox

__all__ = [
    'read_messages_from_imap',
    'acquire_token_interactive',
    'get_account_email',
    'read_messages_from_folder',
    'read_new_messages_from_inbox'
]
