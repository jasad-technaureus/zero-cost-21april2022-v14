# -*- coding: utf-8 -*-
# This module and its content is copyright of Technaureus Info Solutions Pvt. Ltd.
# - © Technaureus Info Solutions Pvt. Ltd 2020. All rights reserved.
from . import models
from . import models
from odoo import api, SUPERUSER_ID
import datetime


def post_init_check_main_currency(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    currency = env['res.currency.rate'].search([])
    if currency:
        for data in currency:
            data.onchange_foreign_currency_rate()

    records = env['account.move'].search([])
    if records:
        for rec in records:
            rec.is_diff_currency_main = False
            if rec.currency_id != rec.company_currency_id:
                rec.is_diff_currency_main = True
                if not rec.is_manual:
                    rec.env['res.currency.rate'].flush(['rate', 'currency_id', 'company_id', 'name'])
                    query = """SELECT c.id,
                                    COALESCE((SELECT r.rate FROM res_currency_rate r
                                    WHERE r.currency_id = c.id AND r.name <= %s
                                    AND (r.company_id IS NULL OR r.company_id = %s)
                                    ORDER BY r.company_id, r.name DESC
                                    LIMIT 1), 1.0) AS rate
                                    FROM res_currency c
                                    WHERE c.id = %s"""

                    if rec.invoice_date:

                        rec._cr.execute(query, (rec.invoice_date, rec.company_id.id, rec.currency_id.id))
                        currency_rates = dict(rec._cr.fetchall())

                        rec.main_curr_rate = 1 / currency_rates.get(rec.currency_id.id)


                    else:

                        rec._cr.execute(query,
                                        (datetime.datetime.now().date(), rec.company_id.id, rec.currency_id.id))
                        currency_rates = dict(rec._cr.fetchall())

                        rec.main_curr_rate = 1 / currency_rates.get(rec.currency_id.id)
    records = env['account.payment'].search([])
    if records:
        for rec in records:
            rec.is_diff_currency_main = False
            if rec.currency_id != rec.company_currency_id:
                rec.is_diff_currency_main = True
                if not rec.is_manual:
                    rec.env['res.currency.rate'].flush(['rate', 'currency_id', 'company_id', 'name'])
                    query = """SELECT c.id,
                                    COALESCE((SELECT r.rate FROM res_currency_rate r
                                    WHERE r.currency_id = c.id AND r.name <= %s
                                    AND (r.company_id IS NULL OR r.company_id = %s)
                                    ORDER BY r.company_id, r.name DESC
                                    LIMIT 1), 1.0) AS rate
                                    FROM res_currency c
                                    WHERE c.id = %s"""

                    if rec.invoice_date:

                        rec._cr.execute(query, (rec.invoice_date, rec.company_id.id, rec.currency_id.id))
                        currency_rates = dict(rec._cr.fetchall())

                        rec.main_curr_rate = 1 / currency_rates.get(rec.currency_id.id)


                    else:

                        rec._cr.execute(query,
                                        (datetime.datetime.now().date(), rec.company_id.id, rec.currency_id.id))
                        currency_rates = dict(rec._cr.fetchall())

                        rec.main_curr_rate = 1 / currency_rates.get(rec.currency_id.id)
