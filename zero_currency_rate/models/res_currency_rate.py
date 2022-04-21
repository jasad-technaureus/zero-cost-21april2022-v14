# -*- coding: utf-8 -*-
# This module and its content is copyright of Technaureus Info Solutions Pvt. Ltd.
# - © Technaureus Info Solutions Pvt. Ltd 2020. All rights reserved.

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class CurrencyRate(models.Model):
    _inherit = "res.currency.rate"

    main_currency_rate = fields.Float(digits=0, help='The rate of main currency to foreign currency to the rate of 1',
                                      )

    @api.onchange('main_currency_rate')
    def onchange_main_currency_rate(self):
        if self.main_currency_rate:
            self.rate = 1 / self.main_currency_rate

    @api.onchange('rate')
    def onchange_foreign_currency_rate(self):
        if self.rate:
            self.main_currency_rate = 1 / self.rate

    def write(self, vals):
        if 'main_currency_rate' in vals:
            if 'rate' in vals:
                if not vals['rate'] == 1 / vals['main_currency_rate']:
                    vals['rate'] = 1 / vals['main_currency_rate']
            if vals['main_currency_rate'] > 0:
                vals['rate'] = 1 / vals['main_currency_rate']
            else:
                raise UserError(_("Main currency Rate Cannot be zero"))

        if 'rate' in vals:
            if 'main_currency_rate' in vals:
                if not vals['main_currency_rate'] == 1 / vals['rate']:
                    vals['main_currency_rate'] = 1 / vals['rate']
            if vals['rate'] > 0:
                vals['main_currency_rate'] = 1 / vals['rate']
            else:
                raise UserError(_("Rate Cannot be zero"))

        res = super(CurrencyRate, self).write(vals)
        return res

    @api.model_create_multi
    def create(self, vals_list):
        for data in vals_list:
            if 'main_currency_rate' in data:
                if 'rate' in data:
                    if data['main_currency_rate'] > 0:
                        if not data['rate'] == 1 / data['main_currency_rate']:
                            data['rate'] = 1 / data['main_currency_rate']
                    else:
                        raise UserError(_("Main currency Rate Cannot be zero"))
                else:
                    if data['main_currency_rate'] > 0:
                        data['rate'] = 1 / data['main_currency_rate']
                    else:
                        raise UserError(_("Main currency Rate Cannot be zero"))
                if data['main_currency_rate'] > 0:
                    data['rate'] = 1 / data['main_currency_rate']
                else:
                    raise UserError(_("Main currency Rate Cannot be zero"))

            if 'rate' in data:
                if 'main_currency_rate' in data:
                    if not data['main_currency_rate'] == 1 / data['rate']:
                        data['main_currency_rate'] = 1 / data['rate']
                else:
                    data['main_currency_rate'] = 1 / data['rate']
                if data['rate'] > 0:
                    data['main_currency_rate'] = 1 / data['rate']
                else:
                    raise UserError(_("Rate Cannot be zero"))
        res = super(CurrencyRate, self).create(vals_list)
        return res


class Currency(models.Model):
    _inherit = "res.currency"

    @api.model
    def _get_conversion_rate(self, from_currency, to_currency, company, date):
        res = super(Currency, self)._get_conversion_rate(from_currency, to_currency, company, date)
        if self._context.get('main_currency_rate'):
            currency_rates = (from_currency + to_currency)._get_rates(company, date)

            if self._context.get('main_curr'):
                if currency_rates.get(self._context.get('main_curr')):
                    currency_rates[self._context.get('main_curr')] = 1 / self._context.get('main_currency_rate')

                    res = currency_rates.get(to_currency.id) / currency_rates.get(from_currency.id)

                    return res

                else:
                    return super(Currency, self)._get_conversion_rate(from_currency=from_currency,
                                                                      to_currency=to_currency, company=company,
                                                                      date=date)
            else:
                return super(Currency, self)._get_conversion_rate(from_currency=from_currency, to_currency=to_currency,
                                                                  company=company, date=date)
        else:
            return super(Currency, self)._get_conversion_rate(from_currency=from_currency, to_currency=to_currency,
                                                              company=company, date=date)
