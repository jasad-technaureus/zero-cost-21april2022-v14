# -*- coding: utf-8 -*-
# This module and its content is copyright of Technaureus Info Solutions Pvt. Ltd.
# - © Technaureus Info Solutions Pvt. Ltd 2020. All rights reserved.


from odoo import fields, models, api, _
from odoo.http import request
from datetime import date, datetime, timezone

from odoo.exceptions import UserError
from odoo.tools import float_is_zero


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    real_date = fields.Datetime(string="Real date")
    real_date_display = fields.Datetime(string="Real Date")
    account_move_id = fields.Many2one('account.move', string="Account Move")
    # date_done_display = fields.Datetime('Date of Transfer', copy=False, readonly=True,
    #                                     help="Date at which the transfer has been processed or cancelled.")

    @api.model
    def create(self, vals):
        print("create_vals", vals)
        res = super(StockPicking, self).create(vals)
        if self.env.context.get('account_move_id'):
            vals['account_move_id'] = self.env.context.get('account_move_id')
            vals['real_date'] = self.env.context.get('real_date')
            vals['real_date_display'] = self.env.context.get('real_date')
            move = self.env['account.move'].browse(self.env.context.get('account_move_id'))
            move.write({'picking_ids': [(4, res.id)]})
        return res

    def button_validate(self):
        res = super(StockPicking, self).button_validate()
        if self.real_date_display:
            self.date_done = self.real_date_display
            # self.date_done = self.real_date
            print('self.date_done....', self.date_done, self.real_date_display)
        elif not self.real_date_display and self.date_done:
            self.real_date = self.date_done
            self.real_date_display = self.date_done
        return res

    # def button_validate(self):
    #     res = super(StockPicking, self).button_validate()
    #     if self.date_done and not self.env.context.get('auto_receipt'):
    #         self.real_date = self.date_done
    #     return res

    # @api.model
    # def _create_picking_from_pos_order_lines(self, location_dest_id, lines, picking_type, partner=False):
    #     res = super(StockPicking, self)._create_picking_from_pos_order_lines(location_dest_id, lines, picking_type,
    #                                                                          partner=False)
    #     for rec in res:
    #         if rec.date_done:
    #             rec.update({'real_date': rec.date_done})
    #     return res

    @api.onchange('real_date_display')
    def onchange_real_date(self):
        print('real_date.............', self.real_date, self.real_date_display)
        if self.real_date_display:
            self.real_date = self.real_date_display
            import pytz
            local = pytz.timezone(self.env.user.tz)
            print('local...', local)
            display_date_result = datetime.strftime(
                pytz.utc.localize(datetime.strptime(str(self.real_date), "%Y-%m-%d %H:%M:%S")).astimezone(
                    local), "%Y-%m-%d %H:%M:%S")
            print('display_date_result', display_date_result, type(display_date_result))
            self.real_date = datetime.strptime(display_date_result, "%Y-%m-%d %H:%M:%S")
            print('...............datetime', self.real_date, type(self.real_date))

        if self.real_date_display and self.real_date_display > datetime.today():
            raise UserError(_('Choose a Date less than or equal to Today'))
        if self.state == 'done':
            journals = ''
            if self.move_lines:
                for move in self.move_lines:
                    if move.account_move_ids:
                        for journal in move.account_move_ids:
                            journals += journal.name + '\n'
            return {
                'warning': {'title': "Warning",
                            'message': "You are changing the Real Date of this inventory transfer. Do not forget to change the accounting date of the following journal entries.\n%s" % journals}
            }


class StockMove(models.Model):
    _inherit = 'stock.move'

    real_date = fields.Datetime(string="Real Date", related='picking_id.real_date', store=True)
    account_move_line_id = fields.Many2one('account.move.line', string='Account Move Line ID')

    def _create_account_move_line(self, credit_account_id, debit_account_id, journal_id, qty, description, svl_id,
                                  cost):
        self.ensure_one()
        AccountMove = self.env['account.move'].with_context(default_journal_id=journal_id)
        print('credit_account_id', credit_account_id, 'debit -account', debit_account_id)
        move_lines = self._prepare_account_move_line(qty, cost, credit_account_id, debit_account_id, description)
        if move_lines:
            date = self._context.get('force_period_date', fields.Date.context_today(self))
            svl = self.env['stock.valuation.layer'].browse(svl_id)
            if svl.real_date:
                date = svl.real_date
            new_account_move = AccountMove.sudo().create({
                'journal_id': journal_id,
                'line_ids': move_lines,
                'date': date,
                'ref': description,
                'stock_move_id': self.id,
                'stock_valuation_layer_ids': [(6, None, [svl_id])],
                'move_type': 'entry',
            })
            new_account_move._post()

    def create(self, vals_list):
        res = super(StockMove, self).create(vals_list)
        if res.inventory_id:
            res.real_date = res.inventory_id.accounting_date
        return res

    def write(self, vals):  # aaa
        for move in self:
            if move.real_date:
                vals.update({'date': move.real_date})
        res = super(StockMove, self).write(vals)
        return res


class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    real_date = fields.Datetime(string="Real Date", related='move_id.real_date', store=True)

    def write(self, vals):  # aaa
        for move in self:
            if move.real_date:
                vals.update({'date': move.real_date})
        res = super(StockMoveLine, self).write(vals)
        return res


class StockValuationLayer(models.Model):
    _inherit = 'stock.valuation.layer'
    # _order = 'real_date, id'

    real_date = fields.Datetime(string="Real Date", related='stock_move_id.real_date', store=True)


class StockValuationLayerRevaluation(models.TransientModel):
    _inherit = 'stock.valuation.layer.revaluation'

    def action_validate_revaluation(self):
        """ Revaluate the stock for `self.product_id` in `self.company_id`.

        - Change the stardard price with the new valuation by product unit.
        - Create a manual stock valuation layer with the `added_value` of `self`.
        - Distribute the `added_value` on the remaining_value of layers still in stock (with a remaining quantity)
        - If the Inventory Valuation of the product category is automated, create
        related account move.
        """
        self.ensure_one()
        if self.currency_id.is_zero(self.added_value):
            raise UserError(_("The added value doesn't have any impact on the stock valuation"))

        product_id = self.product_id.with_company(self.company_id)

        remaining_svls = self.env['stock.valuation.layer'].search([
            ('product_id', '=', product_id.id),
            ('remaining_qty', '>', 0),
            ('company_id', '=', self.company_id.id),
        ])

        # Create a manual stock valuation layer
        if self.reason:
            description = _("Manual Stock Valuation: %s.", self.reason)
        else:
            description = _("Manual Stock Valuation: No Reason Given.")
        if product_id.categ_id.property_cost_method == 'average':
            description += _(
                " Product cost updated from %(previous)s to %(new_cost)s.",
                previous=product_id.standard_price,
                new_cost=product_id.standard_price + self.added_value / self.current_quantity_svl
            )
        revaluation_svl_vals = {
            'company_id': self.company_id.id,
            'product_id': product_id.id,
            'description': description,
            'value': self.added_value,
            'real_date': self.date,
            'quantity': 0,
        }
        print('self.date', self.date, revaluation_svl_vals)
        remaining_qty = sum(remaining_svls.mapped('remaining_qty'))
        remaining_value = self.added_value
        remaining_value_unit_cost = self.currency_id.round(remaining_value / remaining_qty)
        for svl in remaining_svls:
            if float_is_zero(svl.remaining_qty - remaining_qty, precision_rounding=self.product_id.uom_id.rounding):
                svl.remaining_value += remaining_value
            else:
                taken_remaining_value = remaining_value_unit_cost * svl.remaining_qty
                svl.remaining_value += taken_remaining_value
                remaining_value -= taken_remaining_value
                remaining_qty -= svl.remaining_qty

        revaluation_svl = self.env['stock.valuation.layer'].with_context(real_date=self.date).create(
            revaluation_svl_vals)

        # Update the stardard price in case of AVCO
        if product_id.categ_id.property_cost_method == 'average':
            product_id.with_context(
                disable_auto_svl=True).standard_price += self.added_value / self.current_quantity_svl

        # If the Inventory Valuation of the product category is automated, create related account move.
        if self.property_valuation != 'real_time':
            return True

        accounts = product_id.product_tmpl_id.get_product_accounts()

        if self.added_value < 0:
            debit_account_id = self.account_id.id
            credit_account_id = accounts.get('stock_valuation') and accounts['stock_valuation'].id
        else:
            debit_account_id = accounts.get('stock_valuation') and accounts['stock_valuation'].id
            credit_account_id = self.account_id.id

        move_vals = {
            'journal_id': self.account_journal_id.id or accounts['stock_journal'].id,
            'company_id': self.company_id.id,
            'ref': _("Revaluation of %s", product_id.display_name),
            'stock_valuation_layer_ids': [(6, None, [revaluation_svl.id])],
            'date': self.date or fields.Date.today(),
            'move_type': 'entry',
            'line_ids': [(0, 0, {
                'name': _('%(user)s changed stock valuation from  %(previous)s to %(new_value)s - %(product)s',
                          user=self.env.user.name,
                          previous=self.current_value_svl,
                          new_value=self.current_value_svl + self.added_value,
                          product=product_id.display_name,
                          ),
                'account_id': debit_account_id,
                'debit': abs(self.added_value),
                'credit': 0,
                'product_id': product_id.id,
            }), (0, 0, {
                'name': _('%(user)s changed stock valuation from  %(previous)s to %(new_value)s - %(product)s',
                          user=self.env.user.name,
                          previous=self.current_value_svl,
                          new_value=self.current_value_svl + self.added_value,
                          product=product_id.display_name,
                          ),
                'account_id': credit_account_id,
                'debit': 0,
                'credit': abs(self.added_value),
                'product_id': product_id.id,
            })],
        }
        account_move = self.env['account.move'].create(move_vals)
        account_move._post()

        return True

    # @api.model_create_multi
    # def create(self, vals_list):
    #     print("val-svl", vals_list)
    #     print("cont-svl-", self.env.context)
    #     if self.env.context.get('auto_receipt') and self.env.context.get('account_move'):
    #         for val in vals_list:
    #             stock_move = self.env['stock.move'].browse(val.get('stock_move_id'))
    #             if stock_move:
    #                 invoice_line = self.env.context.get('account_move').invoice_line_ids.filtered(
    #                     lambda line: line == stock_move.invoice_line_id)
    #                 print("DEBIT", invoice_line.debit)
    #
    #         sailus
    #
    #     return super(StockValuationLayer, self).create(vals_list)


class ProductTemplate(models.Model):
    _inherit = "product.template"

    is_debug = fields.Boolean(string='Is Debug', compute='_compute_debug', default=False)

    def _compute_debug(self):
        for rec in self:
            if request.session.debug:
                rec.is_debug = True
            else:
                rec.is_debug = False


class ProductProduct(models.Model):
    _inherit = "product.product"

    is_debug = fields.Boolean(string='Is Debug', compute='_compute_debug', default=False)

    def _compute_debug(self):
        for rec in self:
            if request.session.debug:
                rec.is_debug = True
            else:
                rec.is_debug = False

# class MrpProduction(models.Model):
#     _inherit = 'mrp.production'
#
#     def button_mark_done(self):
#         res = super(MrpProduction, self).button_mark_done()
#         moves = self.env['stock.move'].search([('production_id', '=', self.id)])
#         if moves:
#             for move in moves:
#                 move.update({'real_date': self.date_finished})
#         if self.move_raw_ids:
#             for move in self.move_raw_ids:
#                 move.update({'real_date': self.date_finished})
#         return res
