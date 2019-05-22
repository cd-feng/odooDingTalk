# -*- coding: utf-8 -*-
import json
import logging
import requests
from requests import ReadTimeout
from odoo import api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class MailChannel(models.Model):
    _inherit = 'mail.channel'

    @api.multi
    @api.returns('mail.message', lambda value: value.id)
    def message_post(self, message_type='notification', **kwargs):
        moderation_status, email = self._extract_moderation_values(message_type, **kwargs)
        if moderation_status == 'rejected':
            return self.env['mail.message']

        self.filtered(lambda channel: channel.channel_type == 'chat').mapped('channel_last_seen_partner_ids').write(
            {'is_pinned': True})

        message = super(MailChannel, self.with_context(mail_create_nosubscribe=True)).message_post(
            message_type=message_type, moderation_status=moderation_status, **kwargs)

        # Notifies the message author when his message is pending moderation if required on channel.
        # The fields "email_from" and "reply_to" are filled in automatically by method create in model mail.message.
        if self.moderation_notify and self.moderation_notify_msg and message_type == 'email' and moderation_status == 'pending_moderation':
            self.env['mail.mail'].create({
                'body_html': self.moderation_notify_msg,
                'subject': 'Re: %s' % (kwargs.get('subject', '')),
                'email_to': email,
                'auto_delete': True,
                'state': 'outgoing'
            })
        return message