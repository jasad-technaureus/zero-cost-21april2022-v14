# -*- coding: utf-8 -*-
# This module and its content is copyright of Technaureus Info Solutions Pvt. Ltd.
# - © Technaureus Info Solutions Pvt. Ltd 2020. All rights reserved.

from odoo import models, fields
import io
from odoo.tools.misc import xlsxwriter


class PurchaseSaleBook(models.TransientModel):
    _name = 'purchase.sale.book'
    _description = 'Creating excel report'

    def calc_amount_tax(self, line, type, sign, liney, special):
        line_amt = 0
        if special:
            if liney:
                main_curr = line.move_id.currency_id.id
                for zer_line in liney:
                    main_curr = zer_line.move_id.currency_id.id
                    context = self._context.copy()
                    context.update({'main_currency_rate': zer_line.move_id.main_curr_rate, 'main_curr': main_curr})
                    self.env.context = context
                    amount = zer_line.currency_id._convert(zer_line.price_subtotal, zer_line.company_currency_id,
                                                           zer_line.company_id,
                                                           zer_line.date or fields.Date.context_today(self))
                    line_amt += round(amount)
                    if 'main_currency_rate' in context:
                        context.pop('main_currency_rate')
                        context.pop('main_curr')
                    self.env.context = context
        # for each in line:
        else:
            if type == 'exclude':
                for each in line:
                    line_amt += round(each.tax_base_amount)
            else:
                for each in line:
                    main_curr = line.move_id.currency_id.id
                    context = self._context.copy()
                    if line.move_id.is_manual:
                        context.update({'main_currency_rate': line.move_id.main_curr_rate, 'main_curr': main_curr})
                        self.env.context = context
                    amount = each.currency_id._convert(each.price_total, each.company_currency_id,
                                                       each.company_id,
                                                       each.date or fields.Date.context_today(self))
                    line_amt += round(amount)
                    if 'main_currency_rate' in context:
                        context.pop('main_currency_rate')
                        context.pop('main_curr')
                    self.env.context = context

        return line_amt * sign

    def excel_report_generate(self, report_type, date_start, date_end):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output)
        worksheet = workbook.add_worksheet('Sheet 1')
        worksheet.set_landscape()
        bold = workbook.add_format({'font_name': 'Agency FB', 'font_size': 16, 'bold': True, 'align': 'left'})
        text = workbook.add_format({'font_name': 'Agency FB', 'font_size': 12, 'align': 'left',
                                    'border': 1})
        text_end = workbook.add_format({'font_name': 'Agency FB', 'font_size': 12, 'align': 'left'})
        text_3 = workbook.add_format({'font_name': 'Agency FB', 'font_size': 12, 'align': 'center',
                                      'border': 5})
        text_4 = workbook.add_format({'font_name': 'Agency FB', 'font_size': 12, 'align': 'right',
                                      'border': 1})
        text_5 = workbook.add_format({'font_name': 'Agency FB', 'font_size': 10, 'align': 'center',
                                      'valign': 'vcenter', 'left': 1, 'right': 1, 'top': 5, 'bottom': 5,
                                      'text_wrap': True})
        text_5_s = workbook.add_format({'font_name': 'Agency FB', 'font_size': 12, 'align': 'center',
                                        'valign': 'vcenter', 'left': 1, 'right': 1, 'top': 5, 'bottom': 5,
                                        'text_wrap': True})

        text_6 = workbook.add_format({'font_name': 'Agency FB', 'font_size': 12, 'bold': True, 'align': 'left'})
        sub_header = workbook.add_format({'font_name': 'Agency FB', 'font_size': 12, 'bold': True, 'align': 'center',
                                          'valign': 'vcenter', 'border': 5})
        sub_header_sub = workbook.add_format(
            {'font_name': 'Agency FB', 'font_size': 12, 'bold': True, 'align': 'center',
             'valign': 'vcenter', 'border': 5, 'text_wrap': True})
        sub_header_sub_1 = workbook.add_format(
            {'font_name': 'Agency FB', 'font_size': 12, 'bold': True, 'align': 'right',
             'valign': 'vcenter', 'border': 5, 'text_wrap': True})
        col_a = workbook.add_format({'font_name': 'Agency FB', 'font_size': 10, 'align': 'center',
                                     'valign': 'vcenter', 'left': 5, 'right': 1, 'top': 5, 'bottom': 5,
                                     'text_wrap': True})
        col_a_s = workbook.add_format({'font_name': 'Agency FB', 'font_size': 12, 'align': 'center',
                                       'valign': 'vcenter', 'left': 5, 'right': 1, 'top': 5, 'bottom': 5,
                                       'text_wrap': True})
        col_z = workbook.add_format({'font_name': 'Agency FB', 'font_size': 10, 'align': 'center',
                                     'valign': 'vcenter', 'left': 1, 'right': 5, 'top': 5, 'bottom': 5,
                                     'text_wrap': True})
        col_z_s = workbook.add_format({'font_name': 'Agency FB', 'font_size': 12, 'align': 'center',
                                       'valign': 'vcenter', 'left': 1, 'right': 5, 'top': 5, 'bottom': 5,
                                       'text_wrap': True})
        worksheet.set_column(0, 0, 8.8)
        worksheet.set_row(0, 21)
        worksheet.set_row(1, 16)
        worksheet.set_row(2, 16)
        worksheet.set_row(3, 16)
        worksheet.set_row(4, 16)
        worksheet.set_row(6, 16)
        worksheet.write(1, 0, 'Shoqëria ', text_end)
        worksheet.write(1, 2, self.env.company.name, text_end)
        worksheet.write(2, 0, 'Nipti ', text_end)
        worksheet.write(2, 2, self.env.company.vat if self.env.company.vat else '', text_end)
        worksheet.write(3, 0, 'Viti ', text_end)
        worksheet.write(3, 2, date_start.year, text_end)
        worksheet.write(4, 0, 'Muaji ', text_end)
        worksheet.write(4, 2, date_start.month, text_end)
        worksheet.write(6, 0, 'Pa veprimtari  ', text_end)
        worksheet.write(6, 2, 'Plotëso PO nëse gjatë muajit nuk është bërë asnjë transaksion. ', text_end)
        # worksheet.row(10).height = 960
        if report_type == 'purchase':
            worksheet.set_column(1, 1, 8)
            worksheet.set_column(2, 2, 12)
            worksheet.set_column(3, 3, 6.4)
            worksheet.set_column(4, 4, 6.4)
            worksheet.set_column(5, 5, 6.95)
            worksheet.set_column(6, 6, 11.2)
            worksheet.merge_range(8, 0, 8, 2, "Fatura", sub_header)
            worksheet.merge_range(8, 3, 8, 5, "Shitësi", sub_header)
            worksheet.merge_range(9, 0, 10, 0, "Nr Faturës ", sub_header_sub)
            worksheet.merge_range(9, 1, 10, 1, "Numri Serial ", sub_header_sub)
            worksheet.merge_range(9, 2, 10, 2, "Data (dd/mm/yyyy)", sub_header_sub)
            worksheet.merge_range(9, 3, 10, 3, "Emri tregtar/personi", sub_header_sub)
            worksheet.merge_range(9, 4, 10, 4, "Rrethi", sub_header_sub)
            worksheet.merge_range(9, 5, 10, 5, "NIPT/Kodi Fermerit", sub_header_sub)
            worksheet.set_row(8, 26)
            worksheet.set_row(9, 38)
            worksheet.set_row(10, 48)
            worksheet.merge_range(8, 6, 10, 6, "Totali(përfshirë TVSH)", sub_header_sub)
            worksheet.set_row(11, 42)
            worksheet.write(11, 0, 'a', col_a)
            worksheet.write(11, 1, 'b', text_5)
            worksheet.write(11, 2, 'c', text_5)
            worksheet.write(11, 3, 'ç', text_5)
            worksheet.write(11, 4, 'd', text_5)
            worksheet.write(11, 5, 'dh', text_5)
            worksheet.write(11, 6, 'e=(ë+f+g+gj+h+i+j+k+l+ll+m+n+nj+o+p+q+r+rr+s+sh+t+t+u+v+x+xh+y+z)',
                            text_5)

            domain2 = [
                ('move_type', 'in', ('in_invoice', 'in_refund')),
                ('state', '=', 'posted'),
                ('date', '>=', date_start),
                ('date', '<=', date_end),
                ('not_in_book', '=', False),
                ('fiscal_position_id', '!=', False),
            ]
            moves = self.env['account.move'].search(domain2, order='date')
            if moves:
                for move in moves:
                    if move.customs:
                        if move.vendor_bill:
                            if move.vendor_bill.id in moves.ids:
                                moves = moves - move.vendor_bill
                    if move.reversed_entry_id and not move.is_partial:
                        if move.reversed_entry_id.payment_state == 'reversed':
                            moves = moves - move
                            if move.reversed_entry_id.id in moves.ids:
                                moves = moves - move.reversed_entry_id
            worksheet.write(0, 0, 'Libri i Blerjeve', bold)
            worksheet.merge_range(8, 7, 8, 28, "Blerje", sub_header_sub)
            worksheet.merge_range(9, 7, 10, 7, "Të përjashtuara,me Tvsh jo të zbritshme/pa tvsh",
                                  sub_header_sub)
            worksheet.merge_range(9, 8, 10, 8, "Blerje investime  brenda vendit pa TVSH", sub_header_sub)
            worksheet.merge_range(9, 9, 10, 9, "Importe të përjashtuara  të investimit pa TVSH", sub_header_sub)
            worksheet.merge_range(9, 10, 10, 10, "Import mallra  të përjashtuara", sub_header_sub)
            worksheet.merge_range(9, 11, 9, 12, "Importe mallra me shkallë 20%", sub_header_sub)
            worksheet.write(10, 11, "Vlera e Tatueshme ", sub_header_sub)
            worksheet.write(10, 12, "Tvsh", sub_header_sub)
            worksheet.merge_range(9, 13, 9, 14, "Importe mallra me shkallë 10%", sub_header_sub)
            worksheet.write(10, 13, "Vlera e Tatueshme", sub_header_sub)
            worksheet.write(10, 14, "Tvsh", sub_header_sub)
            worksheet.merge_range(9, 15, 9, 16, "Importe mallra me shkallë 6%", sub_header_sub)
            worksheet.write(10, 15, "Vlera e Tatueshme", sub_header_sub)
            worksheet.write(10, 16, "Tvsh", sub_header_sub)
            worksheet.merge_range(9, 17, 9, 18, "Importe të investimit me shkallë 20%", sub_header_sub)
            worksheet.write(10, 17, "Vlera e Tatueshme", sub_header_sub)
            worksheet.write(10, 18, "Tvsh", sub_header_sub)
            worksheet.merge_range(9, 19, 9, 20, "Nga Furnitorë Vendas me shkalle 20%", sub_header_sub)
            worksheet.write(10, 19, "Vlera e Tatueshme", sub_header_sub)
            worksheet.write(10, 20, "Tvsh", sub_header_sub)
            worksheet.merge_range(9, 21, 9, 22, "Nga Furnitorë Vendas me shkallë 10%", sub_header_sub)
            worksheet.write(10, 21, "Vlera e Tatueshme", sub_header_sub)
            worksheet.write(10, 22, "Tvsh", sub_header_sub)
            worksheet.merge_range(9, 23, 9, 24, "Nga Furnitorë Vendas me shkallë 6%", sub_header_sub)
            worksheet.write(10, 23, "Vlera e Tatueshme", sub_header_sub)
            worksheet.write(10, 24, "Tvsh", sub_header_sub)
            worksheet.merge_range(9, 25, 9, 26, " Të Investimit nga Furnitorë Vendas me shkallë 20%",
                                  sub_header_sub)
            worksheet.write(10, 25, "Vlera e Tatueshme", sub_header_sub)
            worksheet.write(10, 26, "Tvsh", sub_header_sub)
            worksheet.merge_range(9, 27, 9, 28, "Nga Fermerët vendas", sub_header_sub)
            worksheet.write(10, 27, "Vlera e Tatueshme", sub_header_sub)
            worksheet.write(10, 28, "Tvsh", sub_header_sub)
            worksheet.merge_range(8, 29, 8, 34, "Të tjera veprime ", sub_header_sub)
            worksheet.merge_range(9, 29, 9, 30, "Autongarkesë TVSH në blerje me të drejtë kreditimi",
                                  sub_header_sub)
            worksheet.write(10, 29, "Vlera e Tatueshme", sub_header_sub)
            worksheet.write(10, 30, "Tvsh", sub_header_sub)
            worksheet.merge_range(9, 31, 9, 32, "Rregullime të TVSH-së së zbritshme", sub_header_sub)
            worksheet.write(10, 31, "Vlera e Tatueshme", sub_header_sub)
            worksheet.write(10, 32, "Tvsh", sub_header_sub)
            worksheet.merge_range(9, 33, 9, 34, "Veprime të borxhit të keq", sub_header_sub)
            worksheet.write(10, 33, "Vlera e Tatueshme", sub_header_sub)
            worksheet.write(10, 34, "Tvsh", sub_header_sub)
            worksheet.write(11, 7, 'ë', text_5)
            worksheet.write(11, 8, 'f', text_5)
            worksheet.write(11, 9, 'g', text_5)
            worksheet.write(11, 10, 'gj', text_5)
            worksheet.write(11, 11, 'h', text_5)
            worksheet.write(11, 12, 'i = (h) x 20%', text_5)
            worksheet.write(11, 13, 'j', text_5)
            worksheet.write(11, 14, 'k = (j) x 10%', text_5)
            worksheet.write(11, 15, 'l', text_5)
            worksheet.write(11, 16, 'll =(l) x 6%', text_5)
            worksheet.write(11, 17, 'm', text_5)
            worksheet.write(11, 18, 'n =( m)  x 20%)', text_5)
            worksheet.write(11, 19, 'nj', text_5)
            worksheet.write(11, 20, 'o = ( nj)  x 20%)', text_5)
            worksheet.write(11, 21, 'p', text_5)
            worksheet.write(11, 22, 'q=(p)  x 10%)', text_5)
            worksheet.write(11, 23, 'r', text_5)
            worksheet.write(11, 24, 'rr=(r)  x 6%)', text_5)
            worksheet.write(11, 25, 's', text_5)
            worksheet.write(11, 26, 'sh =( s)  x 20%)', text_5)
            worksheet.write(11, 27, 't', text_5)
            worksheet.write(11, 28, 'th=( t)  x 6%)', text_5)
            worksheet.write(11, 29, 'u', text_5)
            worksheet.write(11, 30, 'v = (u)  x 20/10/6 %)', text_5)
            worksheet.write(11, 31, 'x', text_5)
            worksheet.write(11, 32, 'xh =(x) x 20/10/6 %)', text_5)
            worksheet.write(11, 33, 'y', text_5)
            worksheet.write(11, 34, 'z =(y)  x 20/10/6 %)', col_z)
            row = 12
            col = 0
            col_total = 0
            col_e = 0
            col_f = 0
            col_g = 0
            col_gj = 0
            col_h = 0
            col_i = 0
            col_j = 0
            col_k = 0
            col_l = 0
            col_ll = 0
            col_m = 0
            col_n = 0
            col_nj = 0
            col_o = 0
            col_p = 0
            col_q = 0
            col_r = 0
            col_rr = 0
            col_s = 0
            col_sh = 0
            col_t = 0
            col_th = 0
            col_u = 0
            col_v = 0
            col_x = 0
            col_xh = 0
            col_y = 0
            col_z = 0
            initial_row = row
            if moves:
                for move in moves:
                    sign = 1
                    if move.move_type == 'in_refund':
                        sign = -1
                    covered_column = []
                    if move.fiscal_position_id:
                        tax_lines = move.line_ids.filtered(lambda line: line.tax_line_id)
                        new_tax = move.line_ids.mapped('tax_ids')
                        books = self.env['purchase.book.mapping'].search(
                            [('fiscal_position_id', '=', move.fiscal_position_id.id), ('tax_id', 'in', new_tax.ids)])
                        book_tax = books.mapped('tax_id')
                        new_line = tax_lines.filtered(lambda x: x.tax_line_id not in book_tax)
                        tax_lines = tax_lines - new_line
                        zero_tax = move.line_ids.tax_ids.filtered(lambda x: x.amount == 0)

                        if tax_lines or zero_tax:
                            row_total = 0
                            worksheet.set_row(row, 17.3)
                            # worksheet.write(row, col, move.ref, text)
                            # worksheet.write(row, col + 1, move.ref_2, text)
                            # date_from = move.invoice_date.strftime("%d/%m/%Y")
                            # worksheet.write(row, col + 2, date_from, text)
                            # worksheet.write(row, col + 3, move.partner_id.name, text)
                            # worksheet.write(row, col + 4, move.partner_id.city, text)
                            # worksheet.write(row, col + 5, move.partner_id.vat, text)
                            written = False
                            #
                            for book in books:
                                if book.book_column == 'ë':
                                    written = True
                                    special = False
                                    line = tax_lines.filtered(lambda x: x.tax_line_id == book.tax_id)
                                    liney = []
                                    if book.tax_id in zero_tax:
                                        special = True
                                        for linex in move.line_ids:
                                            for taxex in linex.tax_ids:
                                                if taxex == book.tax_id:
                                                    liney.append(linex)
                                    # zero_line
                                    line_amt = self.calc_amount_tax(line, book.value, sign, liney, special)
                                    col_e += line_amt
                                    worksheet.write(row, 7, line_amt, text_4)
                                    row_total += line_amt
                                    covered_column.append(7)
                                elif book.book_column == 'f':
                                    written = True
                                    liney = []
                                    special = False
                                    if book.tax_id in zero_tax:
                                        if book.tax_id in zero_tax:
                                            special = True
                                            for linex in move.line_ids:
                                                for taxex in linex.tax_ids:
                                                    if taxex == book.tax_id:
                                                        liney.append(linex)
                                    line = tax_lines.filtered(lambda x: x.tax_line_id == book.tax_id)
                                    line_amt = self.calc_amount_tax(line, book.value, sign, liney, special)
                                    col_f += line_amt
                                    worksheet.write(row, 8, line_amt, text_4)
                                    row_total += line_amt
                                    covered_column.append(8)
                                elif book.book_column == 'g':
                                    written = True
                                    liney = []
                                    special = False
                                    if book.tax_id in zero_tax:
                                        if book.tax_id in zero_tax:
                                            special = True
                                            for linex in move.line_ids:
                                                for taxex in linex.tax_ids:
                                                    if taxex == book.tax_id:
                                                        liney.append(linex)
                                    line = tax_lines.filtered(lambda x: x.tax_line_id == book.tax_id)
                                    line_amt = self.calc_amount_tax(line, book.value, sign, liney, special)
                                    col_g += line_amt
                                    worksheet.write(row, 9, line_amt, text_4)
                                    row_total += line_amt
                                    covered_column.append(9)
                                elif book.book_column == 'gj':
                                    written = True

                                    liney = []
                                    special = False
                                    if book.tax_id in zero_tax:
                                        if book.tax_id in zero_tax:
                                            special = True
                                            for linex in move.line_ids:
                                                for taxex in linex.tax_ids:
                                                    if taxex == book.tax_id:
                                                        liney.append(linex)
                                    line = tax_lines.filtered(lambda x: x.tax_line_id == book.tax_id)
                                    line_amt = self.calc_amount_tax(line, book.value, sign, liney, special)
                                    col_gj += line_amt
                                    worksheet.write(row, 10, line_amt, text_4)
                                    row_total += line_amt
                                    covered_column.append(10)
                                elif book.book_column == 'h':
                                    written = True

                                    liney = []
                                    special = False
                                    line = tax_lines.filtered(lambda x: x.tax_line_id == book.tax_id)
                                    line_amt = self.calc_amount_tax(line, book.value, sign, liney, special)
                                    col_h += line_amt
                                    worksheet.write(row, 11, line_amt, text_4)
                                    row_total += line_amt
                                    covered_column.append(11)
                                elif book.book_column == 'i':
                                    written = True

                                    liney = []
                                    special = False
                                    line = tax_lines.filtered(lambda x: x.tax_line_id == book.tax_id)
                                    line_amt = self.calc_amount_tax(line, book.value, sign, liney, special)
                                    col_i += line_amt
                                    worksheet.write(row, 12, line_amt, text_4)
                                    row_total += line_amt
                                    covered_column.append(12)
                                elif book.book_column == 'j':
                                    written = True

                                    liney = []
                                    special = False
                                    line = tax_lines.filtered(lambda x: x.tax_line_id == book.tax_id)
                                    line_amt = self.calc_amount_tax(line, book.value, sign, liney, special)
                                    col_j += line_amt
                                    worksheet.write(row, 13, line_amt, text_4)
                                    row_total += line_amt
                                    covered_column.append(13)
                                elif book.book_column == 'k':
                                    written = True

                                    liney = []
                                    special = False
                                    line = tax_lines.filtered(lambda x: x.tax_line_id == book.tax_id)
                                    line_amt = self.calc_amount_tax(line, book.value, sign, liney, special)
                                    col_k += line_amt
                                    worksheet.write(row, 14, line_amt, text_4)
                                    row_total += line_amt
                                    covered_column.append(14)
                                elif book.book_column == 'l':
                                    written = True

                                    liney = []
                                    special = False
                                    line = tax_lines.filtered(lambda x: x.tax_line_id == book.tax_id)
                                    line_amt = self.calc_amount_tax(line, book.value, sign, liney, special)
                                    col_l += line_amt
                                    worksheet.write(row, 15, line_amt, text_4)
                                    row_total += line_amt
                                    covered_column.append(15)
                                elif book.book_column == 'll':
                                    written = True

                                    liney = []
                                    special = False
                                    line = tax_lines.filtered(lambda x: x.tax_line_id == book.tax_id)
                                    line_amt = self.calc_amount_tax(line, book.value, sign, liney, special)
                                    col_ll += line_amt
                                    worksheet.write(row, 16, line_amt, text_4)
                                    row_total += line_amt
                                    covered_column.append(16)
                                elif book.book_column == 'm':
                                    written = True

                                    liney = []
                                    special = False
                                    line = tax_lines.filtered(lambda x: x.tax_line_id == book.tax_id)
                                    line_amt = self.calc_amount_tax(line, book.value, sign, liney, special)
                                    col_m += line_amt
                                    worksheet.write(row, 17, line_amt, text_4)
                                    row_total += line_amt
                                    covered_column.append(17)
                                elif book.book_column == 'n':
                                    written = True

                                    liney = []
                                    special = False
                                    line = tax_lines.filtered(lambda x: x.tax_line_id == book.tax_id)
                                    line_amt = self.calc_amount_tax(line, book.value, sign, liney, special)
                                    col_n += line_amt
                                    worksheet.write(row, 18, line_amt, text_4)
                                    row_total += line_amt
                                    covered_column.append(18)
                                elif book.book_column == 'nj':
                                    written = True

                                    liney = []
                                    special = False
                                    line = tax_lines.filtered(lambda x: x.tax_line_id == book.tax_id)
                                    line_amt = self.calc_amount_tax(line, book.value, sign, liney, special)
                                    col_nj += line_amt
                                    worksheet.write(row, 19, line_amt, text_4)
                                    row_total += line_amt
                                    covered_column.append(19)
                                elif book.book_column == 'o':
                                    written = True

                                    liney = []
                                    special = False
                                    line = tax_lines.filtered(lambda x: x.tax_line_id == book.tax_id)
                                    line_amt = self.calc_amount_tax(line, book.value, sign, liney, special)
                                    col_o += line_amt
                                    worksheet.write(row, 20, line_amt, text_4)
                                    row_total += line_amt
                                    covered_column.append(20)
                                elif book.book_column == 'p':
                                    written = True

                                    liney = []
                                    special = False
                                    line = tax_lines.filtered(lambda x: x.tax_line_id == book.tax_id)
                                    line_amt = self.calc_amount_tax(line, book.value, sign, liney, special)
                                    col_p += line_amt
                                    worksheet.write(row, 21, line_amt, text_4)
                                    row_total += line_amt
                                    covered_column.append(21)
                                elif book.book_column == 'q':
                                    written = True

                                    liney = []
                                    special = False
                                    line = tax_lines.filtered(lambda x: x.tax_line_id == book.tax_id)
                                    line_amt = self.calc_amount_tax(line, book.value, sign, liney, special)
                                    col_q += line_amt
                                    worksheet.write(row, 22, line_amt, text_4)
                                    row_total += line_amt
                                    covered_column.append(22)
                                elif book.book_column == 'r':
                                    written = True

                                    liney = []
                                    special = False
                                    line = tax_lines.filtered(lambda x: x.tax_line_id == book.tax_id)
                                    line_amt = self.calc_amount_tax(line, book.value, sign, liney, special)
                                    col_r += line_amt
                                    worksheet.write(row, 23, line_amt, text_4)
                                    row_total += line_amt
                                    covered_column.append(23)
                                elif book.book_column == 'rr':
                                    written = True

                                    liney = []
                                    special = False
                                    line = tax_lines.filtered(lambda x: x.tax_line_id == book.tax_id)
                                    line_amt = self.calc_amount_tax(line, book.value, sign, liney, special)
                                    col_rr += line_amt
                                    worksheet.write(row, 24, line_amt, text_4)
                                    row_total += line_amt
                                    covered_column.append(24)
                                elif book.book_column == 's':
                                    written = True

                                    liney = []
                                    special = False
                                    line = tax_lines.filtered(lambda x: x.tax_line_id == book.tax_id)
                                    line_amt = self.calc_amount_tax(line, book.value, sign, liney, special)
                                    col_s += line_amt
                                    worksheet.write(row, 25, line_amt, text_4)
                                    row_total += line_amt
                                    covered_column.append(25)
                                elif book.book_column == 'sh':
                                    written = True

                                    liney = []
                                    special = False
                                    line = tax_lines.filtered(lambda x: x.tax_line_id == book.tax_id)
                                    line_amt = self.calc_amount_tax(line, book.value, sign, liney, special)
                                    col_sh += line_amt
                                    worksheet.write(row, 26, line_amt, text_4)
                                    row_total += line_amt
                                    covered_column.append(26)
                                elif book.book_column == 't':
                                    written = True

                                    liney = []
                                    special = False
                                    line = tax_lines.filtered(lambda x: x.tax_line_id == book.tax_id)
                                    line_amt = self.calc_amount_tax(line, book.value, sign, liney, special)
                                    col_t += line_amt
                                    worksheet.write(row, 27, line_amt, text_4)
                                    row_total += line_amt
                                    covered_column.append(27)
                                elif book.book_column == 'th':
                                    written = True

                                    liney = []
                                    special = False
                                    line = tax_lines.filtered(lambda x: x.tax_line_id == book.tax_id)
                                    line_amt = self.calc_amount_tax(line, book.value, sign, liney, special)
                                    col_th += line_amt
                                    worksheet.write(row, 28, line_amt, text_4)
                                    row_total += line_amt
                                    covered_column.append(28)
                                elif book.book_column == 'u':
                                    written = True

                                    liney = []
                                    special = False
                                    line = tax_lines.filtered(lambda x: x.tax_line_id == book.tax_id)
                                    line_amt = self.calc_amount_tax(line, book.value, sign, liney, special)
                                    col_u += line_amt
                                    worksheet.write(row, 29, line_amt, text_4)
                                    row_total += line_amt
                                    covered_column.append(29)
                                elif book.book_column == 'v':
                                    written = True

                                    liney = []
                                    special = False
                                    line = tax_lines.filtered(lambda x: x.tax_line_id == book.tax_id)
                                    line_amt = self.calc_amount_tax(line, book.value, sign, liney, special)
                                    col_v += line_amt
                                    worksheet.write(row, 30, line_amt, text_4)
                                    row_total += line_amt
                                    covered_column.append(30)
                                elif book.book_column == 'x':
                                    written = True

                                    liney = []
                                    special = False
                                    line = tax_lines.filtered(lambda x: x.tax_line_id == book.tax_id)
                                    line_amt = self.calc_amount_tax(line, book.value, sign, liney, special)
                                    col_x += line_amt
                                    worksheet.write(row, 31, line_amt, text_4)
                                    row_total += line_amt
                                    covered_column.append(31)
                                elif book.book_column == 'xh':
                                    written = True

                                    liney = []
                                    special = False
                                    line = tax_lines.filtered(lambda x: x.tax_line_id == book.tax_id)
                                    line_amt = self.calc_amount_tax(line, book.value, sign, liney, special)
                                    col_xh += line_amt
                                    worksheet.write(row, 32, line_amt, text_4)
                                    row_total += line_amt
                                    covered_column.append(32)
                                elif book.book_column == 'y':
                                    written = True

                                    liney = []
                                    special = False
                                    line = tax_lines.filtered(lambda x: x.tax_line_id == book.tax_id)
                                    line_amt = self.calc_amount_tax(line, book.value, sign, liney, special)
                                    col_y += line_amt
                                    worksheet.write(row, 33, line_amt, text_4)
                                    row_total += line_amt
                                    covered_column.append(33)
                                elif book.book_column == 'z':
                                    written = True

                                    liney = []
                                    special = False
                                    line = tax_lines.filtered(lambda x: x.tax_line_id == book.tax_id)
                                    line_amt = self.calc_amount_tax(line, book.value, sign, liney, special)
                                    col_z += line_amt
                                    worksheet.write(row, 34, line_amt, text_4)
                                    row_total += line_amt
                                    covered_column.append(34)
                                for cols in range(7, 35):
                                    if cols not in covered_column:
                                        worksheet.write(row, cols, 0, text_4)

                            if written:
                                worksheet.write(row, col, move.ref, text)
                                worksheet.write(row, col + 1, move.ref_2, text)
                                date_from = move.invoice_date.strftime("%d/%m/%Y")
                                worksheet.write(row, col + 2, date_from, text)
                                worksheet.write(row, col + 3, move.partner_id.name, text)
                                worksheet.write(row, col + 4, move.partner_id.city, text)
                                worksheet.write(row, col + 5, move.partner_id.vat, text)
                                worksheet.write(row, 6, row_total, text_4)
                                if move.customs:
                                    if move.rel_vendor:
                                        worksheet.write(row, col + 3, move.rel_vendor.name, text)
                                        worksheet.write(row, col + 4, move.rel_vendor.city, text)
                                        worksheet.write(row, col + 5, move.rel_vendor.vat, text)

                                row += 1
                                col_total += row_total
            worksheet.set_row(row, 16.4)
            worksheet.merge_range(row, 0, row, 5, "Shuma totale", sub_header_sub)
            worksheet.write(row, 6, col_total, sub_header_sub_1)
            # worksheet.row(row + 1).height = 330
            worksheet.merge_range(row + 1, 0, row + 1, 6, "Kutia sipas Formularit të Deklarimit dhe Pagesës së TVSH-së",
                                  text_3)
            worksheet.write(row, 7, col_e, sub_header_sub_1)
            worksheet.write(row + 1, 7, "kutia (26)", text_3)
            worksheet.write(row, 8, col_f, sub_header_sub_1)
            worksheet.write(row + 1, 8, "kutia (27)", text_3)
            worksheet.write(row, 9, col_g, sub_header_sub_1)
            worksheet.write(row + 1, 9, "kutia (28)", text_3)
            worksheet.write(row, 10, col_gj, sub_header_sub_1)
            worksheet.write(row + 1, 10, "kutia (29)", text_3)
            worksheet.write(row, 11, col_h, sub_header_sub_1)
            worksheet.write(row + 1, 11, "kutia (30)", text_3)
            worksheet.write(row, 12, col_i, sub_header_sub_1)
            worksheet.write(row + 1, 12, "kutia (31)", text_3)
            worksheet.write(row, 13, col_j, sub_header_sub_1)
            worksheet.write(row + 1, 13, "kutia (32)", text_3)
            worksheet.write(row, 14, col_k, sub_header_sub_1)
            worksheet.write(row + 1, 14, "kutia (33)", text_3)
            worksheet.write(row, 15, col_l, sub_header_sub_1)
            worksheet.write(row + 1, 15, "kutia (34)", text_3)
            worksheet.write(row, 16, col_ll, sub_header_sub_1)
            worksheet.write(row + 1, 16, "kutia (35)", text_3)
            worksheet.write(row, 17, col_m, sub_header_sub_1)
            worksheet.write(row + 1, 17, "kutia (36)", text_3)
            worksheet.write(row, 18, col_n, sub_header_sub_1)
            worksheet.write(row + 1, 18, "kutia (37)", text_3)
            worksheet.write(row, 19, col_nj, sub_header_sub_1)
            worksheet.write(row + 1, 19, "kutia (38)", text_3)
            worksheet.write(row, 20, col_o, sub_header_sub_1)
            worksheet.write(row + 1, 20, "kutia (39)", text_3)
            worksheet.write(row, 21, col_p, sub_header_sub_1)
            worksheet.write(row + 1, 21, "kutia (40)", text_3)
            worksheet.write(row, 22, col_q, sub_header_sub_1)
            worksheet.write(row + 1, 22, "kutia (41)", text_3)
            worksheet.write(row, 23, col_r, sub_header_sub_1)
            worksheet.write(row + 1, 23, "kutia (42)", text_3)
            worksheet.write(row, 24, col_rr, sub_header_sub_1)
            worksheet.write(row + 1, 24, "kutia (43)", text_3)
            worksheet.write(row, 25, col_s, sub_header_sub_1)
            worksheet.write(row + 1, 25, "kutia (44)", text_3)
            worksheet.write(row, 26, col_sh, sub_header_sub_1)
            worksheet.write(row + 1, 26, "kutia (45)", text_3)
            worksheet.write(row, 27, col_t, sub_header_sub_1)
            worksheet.write(row + 1, 27, "kutia (46)", text_3)
            worksheet.write(row, 28, col_th, sub_header_sub_1)
            worksheet.write(row + 1, 28, "kutia (47)", text_3)
            worksheet.write(row, 29, col_u, sub_header_sub_1)
            worksheet.write(row + 1, 29, "kutia (48)", text_3)
            worksheet.write(row, 30, col_v, sub_header_sub_1)
            worksheet.write(row + 1, 30, "kutia (49)", text_3)
            worksheet.write(row, 31, col_x, sub_header_sub_1)
            worksheet.write(row + 1, 31, "kutia (50)", text_3)
            worksheet.write(row, 32, col_xh, sub_header_sub_1)
            worksheet.write(row + 1, 32, "kutia (51)", text_3)
            worksheet.write(row, 33, col_y, sub_header_sub_1)
            worksheet.write(row + 1, 33, "kutia (52)", text_3)
            worksheet.write(row, 34, col_z, sub_header_sub_1)
            worksheet.write(row + 1, 34, "kutia (53)", text_3)
            # worksheet.write(row, 7, xlwt.Formula("SUM($I$%d:$I$%d)" % (initial_row + 1, row)))
            worksheet.write(row + 4, 19, "Emri Mbiemri", text_6)
            worksheet.set_row(row + 7, 16)
            worksheet.write(row + 7, 0, "Shpjegim:", text_end)
            worksheet.set_row(row + 8, 16)
            worksheet.write(row + 8, 0,
                            "Në rastin kur ky libër do të printohet, për qëllime të ruajtjes/ mbajtjes së dokumentacionit, çdo faqe e printuar duhet të ketë në krye përmbajtjen / rreshtat nga 1 në 12. ",
                            text_end)
            worksheet.set_row(row + 9, 16)
            worksheet.write(row + 9, 0, "Nr i rreshtave mund të shtohet në përputhje me nr e transaksioneve.", text_end)
        #
        if report_type == 'sale':
            worksheet.set_column(0, 0, 10)
            worksheet.set_column(1, 1, 8)
            worksheet.set_column(2, 2, 12)
            worksheet.set_column(3, 3, 11)
            worksheet.set_column(4, 4, 11)
            worksheet.set_column(5, 5, 11)
            worksheet.set_column(6, 6, 12)
            worksheet.set_column(7, 7, 11)
            worksheet.set_column(8, 8, 11)
            worksheet.set_column(9, 9, 11)
            worksheet.set_column(10, 10, 11)
            worksheet.set_column(11, 11, 11)
            worksheet.set_column(12, 12, 11)
            worksheet.set_column(13, 13, 11)
            worksheet.set_column(14, 14, 11)
            worksheet.set_column(15, 15, 11)
            worksheet.set_column(16, 16, 11)
            worksheet.set_column(17, 17, 11)
            worksheet.set_column(18, 18, 11)
            worksheet.set_column(19, 19, 11)
            worksheet.set_column(20, 20, 11)
            worksheet.set_column(21, 21, 11)
            worksheet.set_column(21, 21, 11)
            worksheet.set_row(9, 31)
            worksheet.set_row(10, 32.2)
            worksheet.set_row(11, 31)
            worksheet.merge_range(8, 0, 9, 2, "Fatura", sub_header)
            worksheet.merge_range(8, 3, 9, 5, "Blerësi", sub_header)
            worksheet.write(10, 0, "Nr Faturës ", sub_header_sub)
            worksheet.write(10, 1, "Numri Serial ", sub_header_sub)
            worksheet.write(10, 2, "Data  (dd/mm/yyyy)", sub_header_sub)
            worksheet.write(10, 3, "Emri tregtar/personi", sub_header_sub)
            worksheet.write(10, 4, "Rrethi", sub_header_sub)
            worksheet.write(10, 5, "NIPT/KodiFermerit", sub_header_sub)
            worksheet.merge_range(8, 6, 10, 6, "Totali (përfshirë TVSH)", sub_header_sub)
            worksheet.write(11, 0, 'a', col_a_s)
            worksheet.write(11, 1, 'b', text_5_s)
            worksheet.write(11, 2, 'c', text_5_s)
            worksheet.write(11, 3, 'ç', text_5_s)
            worksheet.write(11, 4, 'd', text_5_s)
            worksheet.write(11, 5, 'dh', text_5_s)
            worksheet.write(11, 6, 'e=(ë+f+g+gj+h+i+j+k+l+ll+m+n+nj+o+p+q+r+rr+s+sh+t+th+u+v+x+xh+y+z)',
                            text_5_s)

            domain1 = [
                ('move_type', 'in', ('out_invoice', 'out_refund')),
                ('state', '=', 'posted'),
                ('invoice_date', '>=', date_start),
                ('invoice_date', '<=', date_end),
                ('not_in_book', '=', False),
                ('fiscal_position_id', '!=', False),

            ]
            moves_1 = self.env['account.move'].search(domain1, order='ref_2')
            if moves_1:
                for move in moves_1:
                    if move.reversed_entry_id and not move.is_partial:
                        if move.reversed_entry_id.payment_state == 'reversed':
                            moves_1 = moves_1 - move
                            if move.reversed_entry_id.id in moves_1.ids:
                                moves_1 = moves_1 - move.reversed_entry_id

            worksheet.write(0, 0, 'Libri i Shitjeve', bold)
            # worksheet.row(8).height = 400
            worksheet.merge_range(8, 7, 10, 7, "Shitjet e përjashtuara",
                                  sub_header_sub)
            worksheet.merge_range(8, 8, 10, 8, "Shitjet pa  TVSH", sub_header_sub)
            worksheet.merge_range(8, 9, 10, 9, "Eksporte mallrash", sub_header_sub)
            worksheet.merge_range(8, 10, 10, 10, "Furnizime me 0%", sub_header_sub)
            worksheet.merge_range(8, 11, 9, 12, "Shitje me shkallë 20%", sub_header_sub)
            worksheet.write(10, 11, "Vlera e Tatueshme", sub_header_sub)
            worksheet.write(10, 12, "Tvsh", sub_header_sub)
            worksheet.merge_range(8, 13, 9, 14, "Shitje me shkallë 10%", sub_header_sub)
            worksheet.write(10, 13, "Vlera e Tatueshme", sub_header_sub)
            worksheet.write(10, 14, "Tvsh", sub_header_sub)
            worksheet.merge_range(8, 15, 9, 16, "Shitje me shkallë 6%", sub_header_sub)
            worksheet.write(10, 15, "Vlera e Tatueshme", sub_header_sub)
            worksheet.write(10, 16, "Tvsh", sub_header_sub)
            worksheet.merge_range(8, 17, 9, 18,
                                  "Shitje regjimi agjentëve të udhëtimit/ marzhi fitimit /shitje në ankand",
                                  sub_header_sub)
            worksheet.write(10, 17, "Vlera e Tatueshme", sub_header_sub)
            worksheet.write(10, 18, "Tvsh", sub_header_sub)
            worksheet.merge_range(8, 19, 9, 20, "Autongarkesë TVSH në shitje", sub_header_sub)
            worksheet.write(10, 19, "Vlera e Tatueshme", sub_header_sub)
            worksheet.write(10, 20, "Tvsh", sub_header_sub)
            worksheet.merge_range(8, 21, 9, 22, "Borxh i keq", sub_header_sub)
            worksheet.write(10, 21, "Vlera e Tatueshme", sub_header_sub)
            worksheet.write(10, 22, "Tvsh", sub_header_sub)
            worksheet.write(11, 7, 'ë', text_5_s)
            worksheet.write(11, 8, 'f', text_5_s)
            worksheet.write(11, 9, 'g', text_5_s)
            worksheet.write(11, 10, 'gj', text_5_s)
            worksheet.write(11, 11, 'h', text_5_s)
            worksheet.write(11, 12, 'i = ( h) x 20%', text_5_s)
            worksheet.write(11, 13, 'j', text_5_s)
            worksheet.write(11, 14, 'k = ( j) x 10%', text_5_s)
            worksheet.write(11, 15, 'l', text_5_s)
            worksheet.write(11, 16, 'll =(l) x 6%', text_5_s)
            worksheet.write(11, 17, 'm', text_5_s)
            worksheet.write(11, 18, 'n =( m)  x 20%)', text_5_s)
            worksheet.write(11, 19, 'nj', text_5_s)
            worksheet.write(11, 20, 'o = (nj)  x 20/10/6 %)', text_5_s)
            worksheet.write(11, 21, 'p', text_5_s)
            worksheet.write(11, 22, 'q = (p)  x 20/10/6 %)', col_z_s)

            row = 12
            col = 0
            col_total = 0
            initial_row = row
            col_e = 0
            col_f = 0
            col_g = 0
            col_gj = 0
            col_h = 0
            col_i = 0
            col_j = 0
            col_k = 0
            col_l = 0
            col_ll = 0
            col_m = 0
            col_n = 0
            col_nj = 0
            col_o = 0
            col_p = 0
            col_q = 0
            # covered_sale = []
            if moves_1:
                for move in moves_1:
                    covered_sale = []
                    if move.fiscal_position_id:
                        sign = 1
                        if move.move_type == 'out_refund':
                            sign = -1
                        row_total = 0
                        tax_lines = move.line_ids.filtered(lambda line: line.tax_line_id)
                        new_tax = move.line_ids.mapped('tax_ids')
                        books = self.env['sale.book.mapping'].search(
                            [('fiscal_position_id', '=', move.fiscal_position_id.id), ('tax_id', 'in', new_tax.ids)])
                        book_tax = books.mapped('tax_id')
                        new_line = tax_lines.filtered(lambda x: x.tax_line_id not in book_tax)
                        tax_lines = tax_lines - new_line
                        zero_tax = move.line_ids.tax_ids.filtered(lambda x: x.amount == 0)

                        if tax_lines or zero_tax:
                            row_total = 0
                            worksheet.set_row(row, 17.3)
                            #                     worksheet.row(row).height = 320
                            #                     worksheet.write(row, col, move.name, text)
                            #                     worksheet.write(row, col + 1, move.name, text)
                            #                     date_from = move.invoice_date.strftime("%d/%m/%Y")
                            #                     worksheet.write(row, col + 2, date_from, text)
                            #                     worksheet.write(row, col + 3, move.partner_id.name, text)
                            #                     worksheet.write(row, col + 4, move.partner_id.city, text)
                            #                     worksheet.write(row, col + 5, move.partner_id.vat, text)
                            written = False

                            for book in books:
                                if book.book_column == 'ë':
                                    written = True

                                    special = False
                                    line_sl = []
                                    if book.tax_id in zero_tax:
                                        special = True
                                        for linex in move.line_ids:
                                            for taxex in linex.tax_ids:
                                                if taxex == book.tax_id:
                                                    line_sl.append(linex)

                                    line = tax_lines.filtered(lambda x: x.tax_line_id == book.tax_id)
                                    line_amt = self.calc_amount_tax(line, book.value, sign, line_sl, special)
                                    col_e += line_amt
                                    worksheet.write(row, 7, line_amt, text_4)
                                    row_total += line_amt
                                    covered_sale.append(7)

                                elif book.book_column == 'f':
                                    written = True
                                    special = False
                                    line_sl = []
                                    if book.tax_id in zero_tax:
                                        special = True
                                        for linex in move.line_ids:
                                            for taxex in linex.tax_ids:
                                                if taxex == book.tax_id:
                                                    line_sl.append(linex)

                                    line = tax_lines.filtered(lambda x: x.tax_line_id == book.tax_id)
                                    line_amt = self.calc_amount_tax(line, book.value, sign, line_sl, special)
                                    col_f += line_amt
                                    worksheet.write(row, 8, line_amt, text_4)
                                    row_total += line_amt
                                    covered_sale.append(8)
                                elif book.book_column == 'g':
                                    written = True

                                    special = False
                                    line_sl = []
                                    if book.tax_id in zero_tax:
                                        special = True
                                        for linex in move.line_ids:
                                            for taxex in linex.tax_ids:
                                                if taxex == book.tax_id:
                                                    line_sl.append(linex)

                                    line = tax_lines.filtered(lambda x: x.tax_line_id == book.tax_id)
                                    line_amt = self.calc_amount_tax(line, book.value, sign, line_sl, special)
                                    col_g += line_amt
                                    worksheet.write(row, 9, line_amt, text_4)
                                    row_total += line_amt
                                    covered_sale.append(9)
                                elif book.book_column == 'gj':
                                    written = True

                                    special = False
                                    line_sl = []
                                    if book.tax_id in zero_tax:
                                        special = True
                                        for linex in move.line_ids:
                                            for taxex in linex.tax_ids:
                                                if taxex == book.tax_id:
                                                    line_sl.append(linex)

                                    line = tax_lines.filtered(lambda x: x.tax_line_id == book.tax_id)
                                    line_amt = self.calc_amount_tax(line, book.value, sign, line_sl, special)
                                    col_gj += line_amt
                                    worksheet.write(row, 10, line_amt, text_4)
                                    row_total += line_amt
                                    covered_sale.append(10)
                                elif book.book_column == 'h':
                                    written = True

                                    special = False
                                    line_sl = []
                                    if book.tax_id in zero_tax:
                                        special = True
                                        for linex in move.line_ids:
                                            for taxex in linex.tax_ids:
                                                if taxex in zero_tax:
                                                    line_sl.append(linex)

                                    line = tax_lines.filtered(lambda x: x.tax_line_id == book.tax_id)
                                    line_amt = self.calc_amount_tax(line, book.value, sign, line_sl, special)
                                    col_h += line_amt
                                    worksheet.write(row, 11, line_amt, text_4)
                                    row_total += line_amt
                                    covered_sale.append(11)
                                elif book.book_column == 'i':
                                    written = True

                                    special = False
                                    line_sl = []
                                    if book.tax_id in zero_tax:
                                        special = True
                                        for linex in move.line_ids:
                                            for taxex in linex.tax_ids:
                                                if taxex in zero_tax:
                                                    line_sl.append(linex)
                                    # if book.tax_id in zero_tax:
                                    #     special = True
                                    #     for linex in move.line_ids:
                                    #         for taxex in linex.tax_ids:
                                    #             if taxex in zero_tax:
                                    #                 line_sl.append(linex)

                                    line = tax_lines.filtered(lambda x: x.tax_line_id == book.tax_id)

                                    line_amt = self.calc_amount_tax(line, book.value, sign, line_sl, special)
                                    col_i += line_amt
                                    worksheet.write(row, 12, line_amt, text_4)
                                    row_total += line_amt
                                    covered_sale.append(12)
                                elif book.book_column == 'j':
                                    written = True

                                    special = False
                                    line_sl = []
                                    if book.tax_id in zero_tax:
                                        special = True
                                        for linex in move.line_ids:
                                            for taxex in linex.tax_ids:
                                                if taxex in zero_tax:
                                                    line_sl.append(linex)

                                    line = tax_lines.filtered(lambda x: x.tax_line_id == book.tax_id)
                                    line_amt = self.calc_amount_tax(line, book.value, sign, line_sl, special)
                                    col_j += line_amt
                                    worksheet.write(row, 13, line_amt, text_4)
                                    row_total += line_amt
                                    covered_sale.append(13)
                                elif book.book_column == 'k':
                                    written = True

                                    special = False
                                    line_sl = []
                                    if book.tax_id in zero_tax:
                                        special = True
                                        for linex in move.line_ids:
                                            for taxex in linex.tax_ids:
                                                if taxex in zero_tax:
                                                    line_sl.append(linex)

                                    line = tax_lines.filtered(lambda x: x.tax_line_id == book.tax_id)
                                    line_amt = self.calc_amount_tax(line, book.value, sign, line_sl, special)
                                    col_k += line_amt
                                    worksheet.write(row, 14, line_amt, text_4)
                                    row_total += line_amt
                                    covered_sale.append(14)
                                elif book.book_column == 'l':
                                    written = True

                                    special = False
                                    line_sl = []
                                    if book.tax_id in zero_tax:
                                        special = True
                                        for linex in move.line_ids:
                                            for taxex in linex.tax_ids:
                                                if taxex in zero_tax:
                                                    line_sl.append(linex)

                                    line = tax_lines.filtered(lambda x: x.tax_line_id == book.tax_id)
                                    line_amt = self.calc_amount_tax(line, book.value, sign, line_sl, special)
                                    col_l += line_amt
                                    worksheet.write(row, 15, line_amt, text_4)
                                    row_total += line_amt
                                    covered_sale.append(15)
                                elif book.book_column == 'll':
                                    written = True

                                    special = False
                                    line_sl = []
                                    if book.tax_id in zero_tax:
                                        special = True
                                        for linex in move.line_ids:
                                            for taxex in linex.tax_ids:
                                                if taxex in zero_tax:
                                                    line_sl.append(linex)

                                    line = tax_lines.filtered(lambda x: x.tax_line_id == book.tax_id)
                                    line_amt = self.calc_amount_tax(line, book.value, sign, line_sl, special)
                                    col_ll += line_amt
                                    worksheet.write(row, 16, line_amt, text_4)
                                    row_total += line_amt
                                    covered_sale.append(16)
                                elif book.book_column == 'm':
                                    written = True

                                    special = False
                                    line_sl = []
                                    if book.tax_id in zero_tax:
                                        special = True
                                        for linex in move.line_ids:
                                            for taxex in linex.tax_ids:
                                                if taxex in zero_tax:
                                                    line_sl.append(linex)

                                    line = tax_lines.filtered(lambda x: x.tax_line_id == book.tax_id)
                                    line_amt = self.calc_amount_tax(line, book.value, sign, line_sl, special)
                                    col_m += line_amt
                                    worksheet.write(row, 17, line_amt, text_4)
                                    row_total += line_amt
                                    covered_sale.append(17)
                                elif book.book_column == 'n':
                                    written = True

                                    special = False
                                    line_sl = []
                                    if book.tax_id in zero_tax:
                                        special = True
                                        for linex in move.line_ids:
                                            for taxex in linex.tax_ids:
                                                if taxex in zero_tax:
                                                    line_sl.append(linex)

                                    line = tax_lines.filtered(lambda x: x.tax_line_id == book.tax_id)
                                    line_amt = self.calc_amount_tax(line, book.value, sign, line_sl, special)
                                    col_n += line_amt
                                    worksheet.write(row, 18, line_amt, text_4)
                                    row_total += line_amt
                                    covered_sale.append(18)
                                elif book.book_column == 'nj':
                                    written = True

                                    special = False
                                    line_sl = []
                                    if book.tax_id in zero_tax:
                                        special = True
                                        for linex in move.line_ids:
                                            for taxex in linex.tax_ids:
                                                if taxex in zero_tax:
                                                    line_sl.append(linex)

                                    line = tax_lines.filtered(lambda x: x.tax_line_id == book.tax_id)
                                    line_amt = self.calc_amount_tax(line, book.value, sign, line_sl, special)
                                    col_nj += line_amt
                                    worksheet.write(row, 19, line_amt, text_4)
                                    row_total += line_amt
                                    covered_sale.append(19)
                                elif book.book_column == 'o':
                                    written = True
                                    special = False
                                    line_sl = []
                                    if book.tax_id in zero_tax:
                                        special = True
                                        for linex in move.line_ids:
                                            for taxex in linex.tax_ids:
                                                if taxex in zero_tax:
                                                    line_sl.append(linex)

                                    line = tax_lines.filtered(lambda x: x.tax_line_id == book.tax_id)
                                    line_amt = self.calc_amount_tax(line, book.value, sign, line_sl, special)
                                    col_o += line_amt
                                    worksheet.write(row, 20, line_amt, text_4)
                                    row_total += line_amt
                                    covered_sale.append(20)
                                elif book.book_column == 'p':
                                    written = True

                                    special = False
                                    line_sl = []
                                    if book.tax_id in zero_tax:
                                        special = True
                                        for linex in move.line_ids:
                                            for taxex in linex.tax_ids:
                                                if taxex in zero_tax:
                                                    line_sl.append(linex)

                                    line = tax_lines.filtered(lambda x: x.tax_line_id == book.tax_id)
                                    line_amt = self.calc_amount_tax(line, book.value, sign, line_sl, special)
                                    col_p += line_amt
                                    worksheet.write(row, 21, line_amt, text_4)
                                    row_total += line_amt
                                    covered_sale.append(21)
                                elif book.book_column == 'q':
                                    written = True

                                    special = False
                                    line_sl = []
                                    if book.tax_id in zero_tax:
                                        special = True
                                        for linex in move.line_ids:
                                            for taxex in linex.tax_ids:
                                                if taxex in zero_tax:
                                                    line_sl.append(linex)

                                    line = tax_lines.filtered(lambda x: x.tax_line_id == book.tax_id)
                                    line_amt = self.calc_amount_tax(line, book.value, sign, line_sl, special)
                                    col_q += line_amt
                                    worksheet.write(row, 22, line_amt, text_4)
                                    row_total += line_amt
                                    covered_sale.append(22)
                                for sale_cols in range(7, 23):
                                    if sale_cols not in covered_sale:
                                        worksheet.write(row, sale_cols, 0, text_4)
                            # if written:
                            #     worksheet.write(row, col, move.name, text)
                            #     worksheet.write(row, col + 1, move.name, text)
                            #     date_from = move.invoice_date.strftime("%d/%m/%Y")
                            #     worksheet.write(row, col + 2, date_from, text)
                            #     worksheet.write(row, col + 3, move.partner_id.name, text)
                            #     worksheet.write(row, col + 4, move.partner_id.city, text)
                            #     worksheet.write(row, col + 5, move.partner_id.vat, text)
                            if written:
                                worksheet.write(row, col, move.ref, text)
                                worksheet.write(row, col + 1, move.ref_2, text)
                                date_from = move.invoice_date.strftime("%d/%m/%Y")
                                worksheet.write(row, col + 2, date_from, text)
                                worksheet.write(row, col + 3, move.partner_id.name, text)
                                worksheet.write(row, col + 4, move.partner_id.city, text)
                                worksheet.write(row, col + 5, move.partner_id.vat, text)

                                worksheet.write(row, 6, row_total, text_4)
                                row += 1
                                col_total += row_total

            #     worksheet.row(row).height = 330
            worksheet.set_row(row, 16.4)
            worksheet.merge_range(row, 0, row, 5, "Shuma totale", sub_header_sub)
            worksheet.write(row, 6, col_total, sub_header_sub_1)
            #     worksheet.row(row + 1).height = 330
            worksheet.set_row(row + 1, 16.4)

            worksheet.merge_range(row + 1, 0, row + 1, 6, "Kutia sipas Formularit të Deklarimit dhe Pagesës së TVSH-së",
                                  text_3)
            worksheet.write(row, 7, col_e, sub_header_sub_1)
            worksheet.write(row + 1, 7, "kutia (9)", text_3)
            worksheet.write(row, 8, col_f, sub_header_sub_1)
            worksheet.write(row + 1, 8, "kutia (10)", text_3)
            worksheet.write(row, 9, col_g, sub_header_sub_1)
            worksheet.write(row + 1, 9, "kutia (11)", text_3)
            worksheet.write(row, 10, col_gj, sub_header_sub_1)
            worksheet.write(row + 1, 10, "kutia (12)", text_3)
            worksheet.write(row, 11, col_h, sub_header_sub_1)
            worksheet.write(row + 1, 11, "kutia (13)", text_3)
            worksheet.write(row, 12, col_i, sub_header_sub_1)
            worksheet.write(row + 1, 12, "kutia (14)", text_3)
            worksheet.write(row, 13, col_j, sub_header_sub_1)
            worksheet.write(row + 1, 13, "kutia (15)", text_3)
            worksheet.write(row, 14, col_k, sub_header_sub_1)
            worksheet.write(row + 1, 14, "kutia (16)", text_3)
            worksheet.write(row, 15, col_l, sub_header_sub_1)
            worksheet.write(row + 1, 15, "kutia (17)", text_3)
            worksheet.write(row, 16, col_ll, sub_header_sub_1)
            worksheet.write(row + 1, 16, "kutia (18)", text_3)
            worksheet.write(row, 17, col_m, sub_header_sub_1)
            worksheet.write(row + 1, 17, "kutia (19)", text_3)
            worksheet.write(row, 18, col_n, sub_header_sub_1)
            worksheet.write(row + 1, 18, "kutia (20)", text_3)
            worksheet.write(row, 19, col_n, sub_header_sub_1)
            worksheet.write(row + 1, 19, "kutia (21)", text_3)
            worksheet.write(row, 20, col_nj, sub_header_sub_1)
            worksheet.write(row + 1, 20, "kutia (22)", text_3)
            worksheet.write(row, 21, col_p, sub_header_sub_1)
            worksheet.write(row + 1, 21, "kutia (23)", text_3)
            worksheet.write(row, 22, col_q, sub_header_sub_1)
            worksheet.write(row + 1, 22, "kutia (24)", text_3)
            #     worksheet.row(row + 2).height = 320
            #     worksheet.row(row + 3).height = 320
            #     worksheet.row(row + 4).height = 320
            #     worksheet.row(row + 5).height = 320
            #     worksheet.row(row + 6).height = 320
            #     worksheet.row(row + 7).height = 320
            #     worksheet.row(row + 8).height = 320
            #     worksheet.row(row + 9).height = 320
            worksheet.set_row(row + 4, 16.4)

            worksheet.write(row + 4, 11, "Emri Mbiemri", text_6)
            worksheet.set_row(row + 7, 16.4)

            worksheet.write(row + 7, 0, "Shpjegim:", text_end)
            worksheet.set_row(row + 8, 16.4)

            worksheet.write(row + 8, 0,
                            "Në rastin kur ky libër do të printohet, për qëllime të ruajtjes/ mbajtjes së dokumentacionit, çdo faqe e printuar duhet të ketë në krye përmbajtjen / rreshtat nga 1 në 12. ",
                            text_end)
            worksheet.set_row(row + 9, 16.4)

            worksheet.write(row + 9, 0, "Nr i rreshtave mund të shtohet në përputhje me nr e transaksioneve.", text_end)

        # fp = io.BytesIO()
        # workbook.save(fp)
        # excel_file = base64.encodestring(fp.getvalue())
        workbook.close()
        xlsx_data = output.getvalue()
        return xlsx_data
