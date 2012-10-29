# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Nicolas Bessi
#    Copyright 2012 Camptocamp SA
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp.osv.orm import  TransientModel, fields
from openerp.osv.osv import except_osv
from openerp.tools.translate import _


class CreditControlMailer(TransientModel):
    """Send emails for each selected credit control lines."""

    _name = "credit.control.mailer"
    _description = """Mass credit line mailer"""
    _rec_name = 'id'

    def _get_line_ids(self, cursor, uid, context=None):
        if context is None:
            context = {}
        res = False
        if (context.get('active_model') == 'credit.control.line' and
                context.get('active_ids')):
            res = self._filter_line_ids(
                    cursor, uid,
                    False,
                    context['active_ids'],
                    context=context)
        return res

    _columns = {
        'mail_all': fields.boolean('Send an e-mail for all "Ready To Send" lines of the "E-Mail" channel'),
        'line_ids': fields.many2many(
            'credit.control.line',
            string='Credit Control Lines',
            domain="[('state', '=', 'to_be_sent'), ('canal', '=', 'mail')]"),
    }

    _defaults = {
        'line_ids': _get_line_ids,
    }

    def _filter_line_ids(self, cursor, uid, mail_all, active_ids, context=None):
        """filter lines to use in the wizard"""
        line_obj = self.pool.get('credit.control.line')
        if mail_all:
            domain = [('state', '=', 'to_be_sent'),
                      ('canal', '=', 'mail')]
        else:
            domain = [('state', '=', 'to_be_sent'),
                      ('id', 'in', active_ids),
                      ('canal', '=', 'mail')]
        return line_obj.search(cursor, uid, domain, context=context)

    def mail_lines(self, cursor, uid, wiz_id, context=None):
        assert not (isinstance(wiz_id, list) and len(wiz_id) > 1), \
                "wiz_id: only one id expected"
        comm_obj = self.pool.get('credit.control.communication')
        if isinstance(wiz_id, list):
            wiz_id = wiz_id[0]
        form = self.browse(cursor, uid, wiz_id, context)

        if not form.line_ids and not form.mail_all:
            raise except_osv(_('Error'), _('No credit control lines selected.'))

        line_ids = [l.id for l in form.line_ids]
        filtered_ids = self._filter_line_ids(
                cursor, uid, form.mail_all, line_ids, context)
        comms = comm_obj._generate_comm_from_credit_line_ids(
                cursor, uid, filtered_ids, context=context)
        comm_obj._generate_mails(cursor, uid, comms, context=context)
        return {}
