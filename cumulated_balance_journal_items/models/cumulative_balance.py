# -*- coding: utf-8 -*-
# This module and its content is copyright of Technaureus Info Solutions Pvt. Ltd.
# - © Technaureus Info Solutions Pvt. Ltd 2021. All rights reserved.

from odoo import models, fields, api


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    balance_in_currency = fields.Monetary(string='Balance in Currency', currency_field='currency_id',
                                          compute='_compute_balance_in_currency',
                                          read_only=True, )
    debit_in_currency = fields.Monetary(string='Debit in Currency', currency_field='currency_id',
                                        compute='_compute_debit_credit', store=True)
    credit_in_currency = fields.Monetary(string='Credit in Currency', currency_field='currency_id',
                                         compute='_compute_debit_credit', store=True)

    @api.model
    def search_read(self, domain=None, fields=None, offset=0, limit=None, order=None):
        def to_tuple(t):
            return tuple(map(to_tuple, t)) if isinstance(t, (list, tuple)) else t

        order = (order or self._order) + ', id'
        return super(AccountMoveLine, self.with_context(domain_balance_in_currency=to_tuple(domain or []),
                                                        order_balance_in_currency=order)).search_read(domain, fields,
                                                                                                      offset, limit,
                                                                                                      order)

    @api.depends_context('domain_balance_in_currency', 'order_balance_in_currency')
    def _compute_balance_in_currency(self):

        if not self.env.context.get('order_balance_in_currency'):
            self.balance_in_currency = 0
            return

        query = self._where_calc(self.env.context.get('domain_balance_in_currency'))
        order_string = ", ".join(
            self._generate_order_by_inner(self._table, self.env.context.get('order_balance_in_currency'), query,
                                          reverse_direction=True))
        from_clause, where_clause, where_clause_params = query.get_sql()
        sql = """
                SELECT account_move_line.id, SUM(account_move_line.amount_currency) OVER (
                    ORDER BY %(order_by)s
                    ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
                )
                FROM %(from)s
                WHERE %(where)s
            """ % {'from': from_clause, 'where': where_clause, 'order_by': order_string}
        self.env.cr.execute(sql, where_clause_params)
        result = {r[0]: r[1] for r in self.env.cr.fetchall()}
        for record in self:
            record.balance_in_currency = result[record.id]

    @api.depends('amount_currency')
    def _compute_debit_credit(self):
        self.debit_in_currency = 0
        self.credit_in_currency = 0
        for rec in self:
            if rec.amount_currency < 0:
                rec.credit_in_currency = abs(rec.amount_currency)
            if rec.amount_currency > 0:
                rec.debit_in_currency = rec.amount_currency
