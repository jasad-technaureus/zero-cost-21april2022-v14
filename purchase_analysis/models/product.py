# -*- coding: utf-8 -*-
# This module and its content is copyright of Technaureus Info Solutions Pvt. Ltd.
# - © Technaureus Info Solutions Pvt. Ltd 2020. All rights reserved.


from odoo import fields, models, api
from datetime import datetime
import time
from datetime import date, timedelta


class ProductProduct(models.Model):
    _inherit = "product.product"

    def action_order_wizard(self):
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'purchase.create.wizard',
            'target': 'new',
        }

    last_sale_date = fields.Date('Last Sale Date', compute='_compute_purchase_analysis_fields_values')
    last_sale_qty = fields.Float('Last Sale Quantity', compute='_compute_purchase_analysis_fields_values')
    last_purchase_date = fields.Date('Last Purchase Date', compute='_compute_purchase_analysis_fields_values')
    last_purchase_qty = fields.Float('Last Purchase Quantity', compute='_compute_purchase_analysis_fields_values')
    end_qty = fields.Float('End Qty on Hand', compute='_compute_purchase_analysis_fields_values', default=0)
    avg_consumption = fields.Float('Daily Average Consumption', compute='_compute_purchase_analysis_fields_values')
    end_stock_date = fields.Date('Stock End Date', compute='_compute_purchase_analysis_fields_values')
    to_order = fields.Float('To Order')
    confirmed_order = fields.Float('Confirmed Orders', compute='_compute_purchase_analysis_fields_values')
    arriving_order = fields.Float('Arriving Orders', compute='_compute_purchase_analysis_fields_values')
    sale_number_invoiced = fields.Float('Total Sold', compute='_compute_purchase_analysis_fields_values')

    purchase_number_invoiced = fields.Float('Total Purchased', compute='_compute_purchase_analysis_fields_values')
    available_qty = fields.Float('Available qty', compute='_compute_purchase_analysis_fields_values')

    # @api.depends('stock_move_ids.product_qty', 'stock_move_ids.state')
    # @api.depends_context(
    #     'lot_id', 'owner_id', 'package_id', 'from_date', 'to_date',
    #     'location', 'warehouse',
    # )
    # def _compute_end_quantities(self):
    #     # products = self.filtered(lambda p: p.type != 'service')
    #     res = self._compute_quantities_dict(self._context.get('lot_id'), self._context.get('owner_id'),
    #                                         self._context.get('package_id'), None,
    #                                         None)
    #     for product in self:
    #         product.end_qty = res[product.id]['qty_available']

    # def _compute_purchase_analysis_fields_values(self, field_names=None):
    #     res = {}
    #     if field_names is None:
    #         field_names = []
    #     for val in self:
    #         res[val.id] = {}
    #         date_from = self.env.context.get('date_from')
    #         date_to = self.env.context.get('to_date')
    #         day_count = 0.0
    #         self.env['account.move.line'].flush(['create_date', 'type', 'product_id', 'date_order_inv_last'])
    #         self.env['account.move'].flush(['move_type'])
    #         if date_from and date_to:
    #             date_from = datetime.strptime(date_from, '%Y-%m-%d')
    #             date_to = datetime.strptime(date_to, '%Y-%m-%d')
    #             days = date_to - date_from
    #             if days.days == 0:
    #                 day_count = 1
    #             else:
    #                 day_count = days.days
    #                 day_count += 1
    #
    #             res[val.id]['date_from'] = date_from
    #             res[val.id]['date_to'] = date_to
    #             # inv_line = self.env['account.move.line'].search(
    #             #     [("product_id", "=", val.id), ('create_date', '>', date_from),
    #             #      ('create_date', '<', date_to), ('type', '=', 'out_invoice')],
    #             #     limit=1,
    #             #     order="date_order_inv_last desc",
    #             # )
    #             # vendor_line = self.env['account.move.line'].search(
    #             #     [("product_id", "=", val.id), ('create_date', '>', date_from),
    #             #      ('create_date', '<', date_to), ('type', '=', 'in_invoice'), ('parent_state', '=', 'posted')],
    #             #     limit=1,
    #             #     order="date_order_inv_last desc",
    #             # )
    #             # for invoice
    #             sql_invoice_line = '''SELECT id,date_order_inv_last,quantity  FROM account_move_line where parent_state='posted' and product_id = %s and type ='out_invoice' and create_date> %s and create_date< %s order by date_order_inv_last desc limit 1'''
    #             self._cr.execute(sql_invoice_line, (val.id, date_from, date_to))
    #             inv_line = self.env.cr.dictfetchall()
    #             sale_num_invoiced = '''SELECT sum(quantity) from account_move_line where product_id =%s and  parent_state='posted' and type IN %s and create_date> %s and create_date<%s '''
    #             invoice_type = ('out_invoice', 'out_refund')
    #             self._cr.execute(sale_num_invoiced, (val.id, invoice_type, date_from, date_to))
    #             sale_num_invoiced_total = self.env.cr.dictfetchall()
    #             # for bill
    #             sql_vendor_line = '''SELECT date_order_inv_last,quantity  FROM account_move_line where product_id = %s and type ='in_invoice' and parent_state='posted' and create_date> %s and create_date <%s order by date_order_inv_last desc limit 1'''
    #             self._cr.execute(sql_vendor_line, (val.id, date_from, date_to))
    #             vendor_line = self.env.cr.dictfetchall()
    #             purchase_num_invoiced = '''SELECT sum(quantity) from account_move_line where product_id =%s and  parent_state='posted' and type IN %s  and create_date> %s and create_date<%s '''
    #             invoice_types = ('in_invoice', 'in_refund')
    #             self._cr.execute(purchase_num_invoiced, (val.id, invoice_types, date_from, date_to))
    #             purchase_num_invoiced_total = self.env.cr.dictfetchall()
    #         else:
    #             # inv_line = self.env['account.move.line'].search(
    #             #     [("product_id", "=", val.id), ('type', '=', 'out_invoice'), ('parent_state', '=', 'posted')],
    #             #     limit=1,
    #             #     order="date_order_inv_last desc",
    #             # )
    #             # vendor_line = self.env['account.move.line'].search(
    #             #     [("product_id", "=", val.id), ('type', '=', 'in_invoice'), ('parent_state', '=', 'posted')],
    #             #     limit=1,
    #             #     order="date_order_inv_last desc",
    #             # )
    #             sql_invoice_line = '''SELECT date_order_inv_last,quantity  FROM account_move_line  where product_id = %s and type ='out_invoice' and parent_state='posted' order by date_order_inv_last desc limit 1'''
    #             self._cr.execute(sql_invoice_line, (val.id,))
    #             inv_line = self.env.cr.dictfetchall()
    #             sale_num_invoiced = '''SELECT sum(quantity) from account_move_line where product_id =%s and  parent_state='posted' and type IN %s '''
    #             invoice_type = ('out_invoice', 'out_refund')
    #             self._cr.execute(sale_num_invoiced, (val.id, invoice_type))
    #             sale_num_invoiced_total = self.env.cr.dictfetchall()
    #
    #             sql_vendor_line = '''SELECT date_order_inv_last,quantity  FROM account_move_line where product_id = %s and type='in_invoice' and parent_state='posted' order by date_order_inv_last desc limit 1'''
    #             self._cr.execute(sql_vendor_line, (val.id,))
    #             vendor_line = self.env.cr.dictfetchall()
    #             purchase_num_invoiced = '''SELECT sum(quantity) from account_move_line where product_id =%s and  parent_state='posted' and type IN %s '''
    #             invoice_types = ('in_invoice', 'in_refund')
    #             self._cr.execute(purchase_num_invoiced, (val.id, invoice_types))
    #             purchase_num_invoiced_total = self.env.cr.dictfetchall()
    #         res[val.id]['last_sale_date'] = inv_line[0].get('date_order_inv_last') if inv_line else False
    #         res[val.id]['sale_number_invoiced'] = sale_num_invoiced_total[0].get(
    #             'sum') if sale_num_invoiced_total else False
    #         res[val.id]['purchase_number_invoiced'] = purchase_num_invoiced_total[0].get(
    #             'sum') if purchase_num_invoiced_total else False
    #         res[val.id]['last_sale_qty'] = inv_line[0].get('quantity') if inv_line else False
    #         res[val.id]['last_purchase_date'] = vendor_line[0].get('date_order_inv_last') if vendor_line else False
    #         res[val.id]['last_purchase_qty'] = vendor_line[0].get('quantity') if vendor_line else False
    #         res[val.id]['avg_consumption'] = res[val.id]['sale_number_invoiced'] / day_count if day_count != 0.0 and \
    #                                                                                             res[val.id][
    #                                                                                                 'sale_number_invoiced'] else 0.0
    #         e_qty = val._compute_quantities_dict(val._context.get('lot_id'), val._context.get('owner_id'),
    #                                              val._context.get('package_id'), None,
    #                                              None)
    #         # available=val._compute_quantities_dict(val._context.get('lot_id'), val._context.get('owner_id'),
    #         #                              val._context.get('package_id'), date_from,
    #         #                              date_to)
    #         res[val.id]['end_qty'] = e_qty[val.id]['qty_available']
    #         res[val.id]['available_qty'] = val.qty_available
    #
    #         if res[val.id]['avg_consumption'] != 0:
    #             try:
    #                 end_stock_date = (
    #                         date_to + timedelta(
    #                     days=res[val.id]['end_qty'] / res[val.id]['avg_consumption'])).strftime(
    #                     '%Y-%m-%d')
    #                 res[val.id]['end_stock_date'] = end_stock_date
    #                 # val.end_stock_date = end_stock_date
    #             except:
    #                 res[val.id]['end_stock_date'] = False
    #         else:
    #             res[val.id]['end_stock_date'] = False
    #
    #         for k, v in res[val.id].items():
    #             setattr(val, k, v)
    #     return res
    #
    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
        """
            Inherit read_group to calculate the sum of the non-stored fields, as it is not automatically done anymore through the XML.
        """
        res = super(ProductProduct, self).read_group(domain, fields, groupby, offset=offset, limit=limit,
                                                     orderby=orderby, lazy=lazy)
        fields_list = ['last_sale_qty', 'last_purchase_qty',
                       'avg_consumption', 'end_qty', 'available_qty']
        if any(x in fields for x in fields_list):
            # Calculate first for every product in which line it needs to be applied
            re_ind = 0
            prod_re = {}
            tot_products = self.browse([])
            for re in res:
                if re.get('__domain'):
                    products = self.search(re['__domain'])
                    tot_products |= products
                    for prod in products:
                        prod_re[prod.id] = re_ind
                re_ind += 1
            res_val = tot_products._compute_purchase_analysis_fields_values(
                field_names=[x for x in fields if fields in fields_list])
            for key in res_val:
                for l in res_val[key]:
                    re = res[prod_re[key]]
                    if re.get(l):
                        if res_val[key][l] and type(res_val[key][l]) == float:
                            re[l] += res_val[key][l]
                    else:
                        if res_val[key][l]:
                            re[l] = res_val[key][l]
        return res

    def _compute_purchase_analysis_fields_values(self, field_names=None):
        day_count = 0.0
        date_from = self.env.context.get('date_from')
        date_to = self.env.context.get('to_date')
        res = {
            product_id: {'date_from': date_from, 'date_to': date_to, 'last_sale_date': False, 'last_sale_qty': 0.0,
                         'last_purchase_date': False, 'last_purchase_qty': 0.0, 'end_qty': 0.0, 'avg_consumption': 0.0,
                         'end_stock_date': False, 'sale_number_invoiced': 0.0,
                         'purchase_number_invoiced': 0.0}
            for product_id in self.ids
        }
        if "force_company" in self.env.context:
            company_id = self.env.context['force_company']
        else:
            company_id = self.env.company.id
        self.env['account.move.line'].flush(['create_date', 'type', 'product_id', 'date_order_inv_last'])
        self.env['account.move'].flush(['move_type', 'company_id'])
        if date_from and date_to:
            date_from = datetime.strptime(date_from, '%Y-%m-%d')
            date_to = datetime.strptime(date_to, '%Y-%m-%d')
            days = date_to - date_from
            if days.days == 0:
                day_count = 1
            else:
                day_count = days.days
                day_count += 1
            # sql_invoice_line = '''SELECT product_id,date_order_inv_last,quantity  FROM account_move_line where parent_state='posted' and product_id IN %s and type ='out_invoice' and create_date >= %s and create_date <= %s group by product_id,date_order_inv_last,quantity order by date_order_inv_last desc'''
            if date_from == date_to:
                sql_invoice_line = '''  SELECT t1.product_id, t1.quantity,t1.date_order_inv_last,sum
                                                 FROM account_move_line AS t1  inner join
                                                 (select distinct product_id, max(date_order_inv_last) as Maxdate ,sum(quantity) 
                                                 as sum from account_move_line where product_id IN %s and type='out_invoice'
                                                 and parent_state='posted'  group by product_id) as t2
                                                 ON (t1.product_id = t2.product_id AND t1.date_order_inv_last = t2.MaxDate) 
                                                 and type='out_invoice' and parent_state='posted'
                                                 group by t1.product_id,t1.quantity,t1.date_order_inv_last,sum '''
                self._cr.execute(sql_invoice_line, (tuple(self.ids),))
                inv_line = self.env.cr.dictfetchall()
                sql_vendor_line = '''  SELECT t1.product_id, t1.quantity,t1.date_order_inv_last,sum
                                                      FROM account_move_line AS t1  inner join
                                                      (select distinct product_id, max(date_order_inv_last) as Maxdate ,sum(quantity) 
                                                      as sum from account_move_line where product_id IN %s and type='in_invoice' 
                                                      and parent_state='posted'  group by product_id) as t2
                                                      ON (t1.product_id = t2.product_id AND t1.date_order_inv_last = t2.MaxDate) 
                                                      and type='in_invoice' and parent_state='posted' 
                                                      group by t1.product_id,t1.quantity,t1.date_order_inv_last,sum '''
                self._cr.execute(sql_vendor_line, (tuple(self.ids),))
                vendor_line = self.env.cr.dictfetchall()
            else:
                sql_invoice_line = '''SELECT t1.product_id, t1.quantity,t1.date_order_inv_last,sum
                                      FROM account_move_line AS t1  inner join
                                      (select distinct product_id, max(date_order_inv_last) as Maxdate ,sum(quantity) 
                                      as sum from account_move_line where product_id IN %s and type='out_invoice' and create_date >= %s and create_date <= %s
                                      and parent_state='posted'  group by product_id) as t2
                                      ON (t1.product_id = t2.product_id AND t1.date_order_inv_last = t2.MaxDate) 
                                      and type='out_invoice' and parent_state='posted'  and create_date >= %s and create_date <= %s
                                      group by t1.product_id,t1.quantity,t1.date_order_inv_last,sum '''
                self._cr.execute(sql_invoice_line, (tuple(self.ids), date_from, date_to, date_from, date_to))
                inv_line = self.env.cr.dictfetchall()
                # sale_num_invoiced = '''SELECT product_id,sum(quantity) from account_move_line where product_id IN %s and  parent_state='posted' and type IN %s and create_date> %s and create_date<%s group by product_id '''
                # invoice_type = ('out_invoice', 'out_refund')
                # self._cr.execute(sale_num_invoiced, (tuple(self.ids), invoice_type, date_from, date_to))
                # sale_num_invoiced_total = self.env.cr.dictfetchall()
                # for bill
                # sql_vendor_line = '''SELECT product_id,date_order_inv_last,quantity  FROM account_move_line where product_id IN %s and type ='in_invoice' and parent_state='posted' and create_date> %s and create_date <%s group by product_id,date_order_inv_last,quantity order by date_order_inv_last desc'''
                sql_vendor_line = '''  SELECT t1.product_id, t1.quantity,t1.date_order_inv_last,sum
                                      FROM account_move_line AS t1  inner join
                                      (select distinct product_id, max(date_order_inv_last) as Maxdate ,sum(quantity) 
                                      as sum from account_move_line where product_id IN %s and type='in_invoice' and create_date >= %s and create_date <= %s
                                      and parent_state='posted'  group by product_id) as t2
                                      ON (t1.product_id = t2.product_id AND t1.date_order_inv_last = t2.MaxDate) 
                                      and type='in_invoice' and parent_state='posted' and create_date >= %s and create_date <= %s
                                      group by t1.product_id,t1.quantity,t1.date_order_inv_last,sum '''
                self._cr.execute(sql_vendor_line, (tuple(self.ids), date_from, date_to, date_from, date_to))
                vendor_line = self.env.cr.dictfetchall()
            # purchase_num_invoiced = '''SELECT product_id, sum(quantity) from account_move_line where product_id IN %s and  parent_state='posted' and type IN %s  and create_date> %s and create_date<%s group by product_id '''
            # invoice_types = ('in_invoice', 'in_refund')
            # self._cr.execute(purchase_num_invoiced, (tuple(self.ids), invoice_types, date_from, date_to))
            # purchase_num_invoiced_total = self.env.cr.dictfetchall()
        else:
            # sql_invoice_line = '''SELECT product_id,date_order_inv_last,quantity   FROM account_move_line  where product_id IN %s and type ='out_invoice' and parent_state='posted' group by product_id,date_order_inv_last,quantity order by date_order_inv_last desc '''
            sql_invoice_line = '''SELECT t1.product_id, t1.quantity,t1.date_order_inv_last,sum
                                  FROM account_move_line AS t1  inner join
                                  (select distinct product_id, max(date_order_inv_last) as Maxdate ,sum(quantity) 
                                  as sum from account_move_line where product_id IN %s and type='out_invoice' 
                                  and parent_state='posted' and company_id = %s  group by product_id) as t2
                                  ON (t1.product_id = t2.product_id AND t1.date_order_inv_last = t2.MaxDate) 
                                  and type='out_invoice' and parent_state='posted' 
                                  group by t1.product_id,t1.quantity,t1.date_order_inv_last,sum '''
            ctx = self.env.context.copy()
            ctx['force_company'] = company_id
            self._cr.execute(sql_invoice_line, (tuple(self.ids), company_id))
            inv_line = self.env.cr.dictfetchall()
            # sale_num_invoiced = '''SELECT product_id,sum(quantity)  from account_move_line where product_id IN %s and  parent_state='posted' and type IN %s group by product_id '''
            # invoice_type = ('out_invoice', 'out_refund')
            # self._cr.execute(sale_num_invoiced, (tuple(self.ids), invoice_type))
            sale_num_invoiced_total = self.env.cr.dictfetchall()
            # sql_vendor_line = '''SELECT product_id,date_order_inv_last,quantity  FROM account_move_line where product_id IN %s and type='in_invoice' and parent_state='posted' group by product_id,date_order_inv_last,quantity order by date_order_inv_last desc '''
            # sql_vendor_line = '''SELECT product_id,date_order_inv_last,quantity  FROM account_move_line where product_id IN %s and type='in_invoice' and parent_state='posted' group by product_id,date_order_inv_last,quantity order by date_order_inv_last desc '''
            sql_vendor_line = ''' SELECT t1.product_id, t1.quantity,t1.date_order_inv_last,sum
                                  FROM account_move_line AS t1  inner join
                                  (select distinct product_id, max(date_order_inv_last) as Maxdate ,sum(quantity) 
                                  as sum from account_move_line where product_id IN %s and type='in_invoice' 
                                  and parent_state='posted' and company_id = %s group by product_id) as t2
                                  ON (t1.product_id = t2.product_id AND t1.date_order_inv_last = t2.MaxDate) 
                                  and type='in_invoice' and parent_state='posted' 
                                  group by t1.product_id,t1.quantity,t1.date_order_inv_last,sum  '''
            self._cr.execute(sql_vendor_line, (tuple(self.ids), company_id))
            vendor_line = self.env.cr.dictfetchall()
            # purchase_num_invoiced = '''SELECT product_id, sum(quantity) from account_move_line where product_id IN %s and  parent_state='posted' and type IN %s group by product_id '''
            # invoice_types = ('in_invoice', 'in_refund')
            # self._cr.execute(purchase_num_invoiced, (tuple(self.ids), invoice_types))
            # purchase_num_invoiced_total = self.env.cr.dictfetchall()
        for product_id in inv_line:
            if not res[product_id['product_id']]['last_sale_date']:
                res[product_id['product_id']]['last_sale_date'] = product_id.get(
                    'date_order_inv_last') if inv_line else False
                res[product_id['product_id']]['last_sale_qty'] = product_id.get('quantity') if inv_line else False
                res[product_id['product_id']]['sale_number_invoiced'] = product_id.get(
                    'sum')
                res[product_id['product_id']]['avg_consumption'] = res[product_id[
                    'product_id']]['sale_number_invoiced'] / day_count if day_count != 0.0 and \
                                                                          res[product_id[
                                                                              'product_id']][
                                                                              'sale_number_invoiced'] else 0.0
        for product_id in vendor_line:
            if not res[product_id['product_id']]['last_purchase_date']:
                res[product_id['product_id']]['last_purchase_date'] = product_id.get(
                    'date_order_inv_last') if vendor_line else False
                res[product_id['product_id']]['last_purchase_qty'] = product_id.get(
                    'quantity') if vendor_line else False
                res[product_id['product_id']]['purchase_number_invoiced'] = product_id.get(
                    'sum')

        for product in self:
            res[product.id]['end_qty'] = product.qty_available
            total_moves = product.env['stock.move'].search(
                [('product_id', '=', product.id), ('state', '=', 'done')])
            in_moves = total_moves.filtered(lambda x: x._is_in())
            out_moves = total_moves.filtered(lambda x: x._is_out())
            qty_available = sum(in_moves.mapped('product_uom_qty')) - sum(out_moves.mapped('product_uom_qty'))
            res[product.id]['available_qty'] = qty_available
            if res[product.id]['avg_consumption'] != 0:
                try:
                    end_stock_date = (
                            date_to + timedelta(
                        days=res[product.id]['end_qty'] / res[product.id][
                            'avg_consumption'])).strftime(
                        '%Y-%m-%d')
                    res[product.id]['end_stock_date'] = end_stock_date
                    # val.end_stock_date = end_stock_date
                except:
                    res[product.id]['end_stock_date'] = False
            else:
                res[product.id]['end_stock_date'] = False
            product.write(res[product.id])
        return res
