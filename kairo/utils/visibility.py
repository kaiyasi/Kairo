from typing import List, Optional
from .tenant import tenant_db
import os

SUPER_ADMIN_ID = int(os.getenv('SUPER_ADMIN_ID', '759651999036997672'))

def get_visible_commands_for_guild(guild_id: int) -> List[str]:
    """Get list of commands that should be visible for a guild based on registration status and enabled modules."""

    registration = tenant_db.get_registration_status(guild_id)

    if not registration:
        return ['register']

    status = registration.get('status', 'none')

    if status in ['none', 'declined']:
        return ['register']
    elif status == 'needs_more_info':
        return ['response']
    elif status == 'pending':
        return []  # No commands during pending review
    elif status == 'approved':
        enabled_modules = tenant_db.get_enabled_modules(guild_id)

        commands = []

        if 'attendance' in enabled_modules:
            commands.extend([
                'signin_start', 'signin_in', 'signin_end',
                'signin_report', 'signin_summary'
            ])

        if 'plans' in enabled_modules:
            commands.extend([
                'plan_set', 'plan_show', 'plan_group_set'
            ])

        if 'qa' in enabled_modules:
            commands.extend([
                'qa_add', 'qa_ask', 'qa_scoreboard', 'qa_reset'
            ])

        if 'ctfd' in enabled_modules:
            commands.extend([
                'ctfd_link', 'ctfd_scoreboard'
            ])

        if 'crypto' in enabled_modules:
            commands.extend([
                'crypto_encrypt', 'crypto_decrypt'
            ])

        if 'bookkeeping' in enabled_modules:
            commands.extend([
                'book_add', 'book_balance', 'book_export', 'book_set_sheets'
            ])

        if 'routing' in enabled_modules:
            commands.extend([
                'org_channel_set', 'org_channel_get'
            ])

        return commands

    return []

def is_super_admin(user_id: int) -> bool:
    """Check if user is the super admin."""
    return user_id == SUPER_ADMIN_ID

def get_super_admin_commands() -> List[str]:
    """Get commands only available to super admin."""
    return [
        'register_accept',
        'register_reject_response',
        'register_decline',
        'modules_enable',
        'modules_disable',
        'modules_list',
        'org_config_set',
        'org_config_get'
    ]

