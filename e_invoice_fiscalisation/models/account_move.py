# -*- coding: utf-8 -*-
# This module and its content is copyright of Technaureus Info Solutions Pvt. Ltd.
# - © Technaureus Info Solutions Pvt. Ltd 2020. All rights reserved.

import requests
from OpenSSL.crypto import sign

from dateutil import tz
from dateutil.relativedelta import relativedelta
# from psycopg2 import tz

from odoo import api, fields, models, _
from datetime import datetime, timedelta

import qrcode

from io import BytesIO
import pytz
import hashlib
from hashlib import sha256

from OpenSSL import crypto

from Crypto.Signature import PKCS1_v1_5
from Crypto.Hash import SHA256
from Crypto.PublicKey import RSA
import base64
from odoo.exceptions import UserError
import ssl
import requests
import re
from base64 import (
    b64encode,
    b64decode,
)
import xml
import xml.dom.minidom

from lxml import etree
from lxml import etree as lxml_ET
from xml.etree import ElementTree as ET

import signxml
from signxml import XMLSigner, XMLVerifier, InvalidCertificate
# pip3 install signxml

from xml.dom import minidom
from odoo import tools

from odoo.tools import float_is_zero, float_round

import logging

logger = logging.getLogger(__name__)

from . import soap_methods_fiskalizim


class AccountMove(models.Model):
    _name = 'account.move'
    _inherit = ['account.move', 'base.ubl']

    xml_request_sent = fields.Boolean(string='XML Request Sent', copy=False)
    fiscalised = fields.Boolean(string='Fiscalised', copy=False)
    is_subsequent_delivery = fields.Boolean(string='Is Subsequent Delivery', readonly=True, copy=False)
    subseq_deliv_type = fields.Selection([('no_internet', 'NOINTERNET'),
                                          ('bound_book', 'BOUNDBOOK'),
                                          ('service', 'SERVICE'),
                                          ('technical_error', 'TECHNICALERROR')],
                                         string='Subsequent Delivery Type', default='technical_error', copy=False)

    xml_request_file = fields.Many2one('ir.attachment', attachment=True, store=True, copy=False)
    xml_response_file = fields.Many2one('ir.attachment', attachment=True, store=True, copy=False)

    qr_code = fields.Binary("QR Code", attachment=True, store=True, copy=False)
    invoice_date_time = fields.Char(string="Invoice Date Time", copy=False)

    type_of_inv = fields.Char(string='Invoice Type', default=lambda self: self.env.user.invoice_type, copy=False)
    is_self_issued_invoice = fields.Boolean(string='Is self Issued Invoice', copy=False)
    type_of_self_iss = fields.Selection([('agreement', 'AGREEMENT'),
                                         ('domestic', 'DOMESTIC'),
                                         ('abroad', 'ABROAD'),
                                         ('self', 'SELF'),
                                         ('other', 'OTHER')], string='Self Issuing Type', copy=False)
    is_simplified_inv = fields.Boolean(default=False, string='Is Simplified Invoice ?', copy=False)
    issue_date_time = fields.Char(string='Issue Date Time', related='invoice_date_time', copy=False)
    inv_num = fields.Char(string='Invoice Fiscalisation Number', copy=False)
    is_issuer_in_vat = fields.Boolean(string='Is Issure In VAT?', related='company_id.is_issuer_in_vat', copy=False)
    iic = fields.Char(string='IIC', copy=False)
    # iic_signature = fields.Char(string='IIC Signature', copy=False)
    iic_signature = fields.Char(string='IIC Signature', copy=False)
    is_reverse_charge = fields.Boolean(string='Is Reverse Charge?', copy=False)
    iic_ref = fields.Char(string='Corrective IIC Ref', copy=False)
    corrective_issue_date_time = fields.Char(string='Corrective Issue DateTime', copy=False)
    corrective_type = fields.Selection([('corrective', 'CORRECTIVE'),
                                        ('debit', 'DEBIT'),
                                        ('credit', 'CREDIT'),
                                        ], string='Corrective Type', copy=False)
    is_bad_debt = fields.Boolean(string='Is Bad Debt?', copy=False)
    bad_debt_invoice_id = fields.Many2one('account.move', string='Bad Debt Invoice', copy=False)
    bad_debt_iic_ref = fields.Char(string='Bad Debt IIC Ref', copy=False)
    bad_debt_issue_date_time = fields.Char(string='Bad Debt Issue DateTime', copy=False)
    supply_start_date = fields.Date(string='Supply Start Date', copy=False)
    supply_end_date = fields.Date(string='Supply End Date', copy=False)
    payment_type_id = fields.Many2one('payment.methods', string='Payment Type', copy=False)
    payment_types = fields.Selection([('banknote', 'BANKNOTE'),
                                      ('card', 'CARD'),
                                      ('check', 'CHECK'),
                                      ('svoucher', 'SVOUCHER'),
                                      ('company', 'COMPANY'),
                                      ('oder', 'ORDER'),
                                      ('account', 'ACCOUNT'),
                                      ('factoring', 'FACTORING'),
                                      ('compensation', 'COMPENSATION'),
                                      ('transfer', 'TRANSFER'),
                                      ('waiver', 'WAIVER'),
                                      ('kind', 'KIND'),
                                      ('other', 'OTHER')], string='Type', related='payment_type_id.type',
                                     default='banknote', store=True, copy=False)
    comp_card = fields.Char(string='Comp Card', copy=False)
    rebate_reducing_base_price = fields.Boolean(string='Rebate reducing BP', copy=False)
    fiscalised_msg = fields.Char(string='Fiscalisation Message', copy=False)
    fiscal_error_msg = fields.Char(string='Fiscalisation Error Message', copy=False)
    fic = fields.Char(string='FIC', copy=False)
    to_modify = fields.Boolean(string='To Modify', copy=False)
    corrective_invoice_id = fields.Many2one('account.move', string='Corrective Invoice')
    print_qr_code = fields.Boolean(string='QR Code In Invoice', default=True)
    is_e_invoice = fields.Boolean(string='Is E Invoice')
    eic = fields.Char(string='EIC', copy=False)

    def action_post(self):
        res = super(AccountMove, self).action_post()
        self.issue_date = datetime.now().date()
        if not self.payment_type_id:
            raise UserError(_('Please enter Payment Type in the Fiscalisation tab.'))
        if self.user_id.tz:
            date_time = datetime.now()
            normal_invoice_date = date_time.strftime("%Y-%m-%d %H:%M:%S")
            normal_invoice_date1 = datetime.strptime(normal_invoice_date, "%Y-%m-%d %H:%M:%S")
            inv_date_time = normal_invoice_date1.astimezone(pytz.timezone(self.user_id.tz)).isoformat()
            self.invoice_date_time = inv_date_time
        else:
            raise UserError(_('Please add Timezone in User settings.'))
        return res

    def button_fiscalise(self):

        context = self._context.copy()
        context.update({'main_currency_rate': self.main_curr_rate, 'main_curr': self.currency_id.id})
        self.env.context = context
        if self.is_e_invoice and self.eic:
            raise UserError(_('The E-Invoice has been fiscalised successfully. You don’t need to fiscalise again.'))

        if self.fiscalised and self.is_e_invoice and not self.eic:
            return self.generate_e_invoice_request()
        if self.fiscalised:
            raise UserError(_('The Invoice has been fiscalised successfully. You don’t need to fiscalise again.'))
        else:
            if not self.company_id.webservice_url_fiscalisation:
                raise UserError(_('Need to configure "Webservice URL Fiscalisation" in the Company settings'))

            if self.corrective_type == 'credit' and (not self.iic_ref or not self.corrective_issue_date_time):
                raise UserError(_(
                    'Corrective type "Credit" must contain "Corrective IIC Ref" and "Corrective Issue Date" '
                    'to Fiscalise.'))
            if self.user_id.tz:

                date_time = datetime.now()
                normal_invoice_date = date_time.strftime("%Y-%m-%d %H:%M:%S")
                normal_invoice_date1 = datetime.strptime(normal_invoice_date, "%Y-%m-%d %H:%M:%S")
                send_date_time = normal_invoice_date1.astimezone(pytz.timezone(self.user_id.tz)).isoformat()
                if not self.invoice_date_time:
                    self.invoice_date_time = send_date_time
            else:
                raise UserError(_('Please add Timezone in User settings.'))

            # file opening and taking private key
            if not self.company_id.certificate_password or not self.company_id.certificate:
                raise UserError(_('Certificate and Password of the Certificate must be given.'))
            try:
                p12 = crypto.load_pkcs12(base64.b64decode(self.company_id.certificate),
                                         self.company_id.certificate_password)
            except Exception as error:
                raise UserError(error)
            certificate = p12.get_certificate()
            ca = p12.get_ca_certificates()
            cer_pem = crypto.dump_certificate(crypto.FILETYPE_PEM, certificate)

            private_key = crypto.dump_privatekey(crypto.FILETYPE_PEM, p12.get_privatekey())
            for to_del in ['\n', ssl.PEM_HEADER, ssl.PEM_FOOTER]:
                cer_pem = cer_pem.replace(to_del.encode('UTF-8'), b'')

            certificate_pem = cer_pem.decode('utf-8')

            for to_del in ['\n', ssl.PEM_HEADER, ssl.PEM_FOOTER]:
                private_key1 = private_key.replace(to_del.encode('UTF-8'), b'')

            private_key_2 = private_key1.decode('utf-8')

            if not self.company_id.vat or not self.user_id.business_unit_code or not self.company_id.software_code:
                raise UserError(_('Please check the fields Company VAT, Business Unit Code and Software Code'))

            concatenated = "|" + self.company_id.vat + "|" + self.invoice_date_time + "|" + self.name + "|" \
                           + self.user_id.business_unit_code + "|" + self.company_id.software_code + "|" \
                           + str(self.amount_total)

            h = SHA256.new(concatenated.encode())
            hashed = h.hexdigest()
            rsa = RSA.importKey(private_key_2)
            signer = PKCS1_v1_5.new(rsa)
            signatures = signer.sign(h)
            result = signatures.hex()

            result_signature_value = base64.b64encode(signatures).decode('utf-8')
            self.iic_signature = result
            # Hashing and creating MD5
            hash_object = hashlib.md5(result.encode())
            md5_hash = hash_object.hexdigest()
            self.iic = md5_hash

            con_items = ""

            for product in self.invoice_line_ids:
                tax_percentage = 0
                main_price_unit = product.price_unit
                for amt in product.tax_ids:
                    tax_percentage = tax_percentage + amt.amount
                    if amt.price_include:
                        product.unit_price_with_vat = product.price_unit
                        if product.quantity != 0:
                            main_price_unit = product.price_unit - (product.vat_amount / product.quantity)
                    else:
                        product.unit_price_with_vat = (product.price_unit * tax_percentage) / 100 + product.price_unit

                price_tot = product.price_total
                price_sub_tot = product.price_subtotal
                vat_amt = product.vat_amount
                quantity = product.quantity
                if self.corrective_type != 'credit':
                    price_tot = product.price_total
                    price_sub_tot = product.price_subtotal
                    vat_amt = product.vat_amount
                    quantity = product.quantity

                if self.is_bad_debt or self.corrective_type == 'credit' or (
                        self.corrective_type == 'corrective' and self.reversed_entry_id):
                    price_tot = -1 * product.price_total
                    price_sub_tot = -1 * product.price_subtotal
                    vat_amt = -1 * product.vat_amount
                    quantity = -1 * product.quantity

                upa = product.unit_price_with_vat

                vat_amt = self.currency_id._convert(vat_amt, self.company_currency_id,
                                                    self.company_id,
                                                    self.invoice_date or fields.Date.context_today(self))

                price_tot = self.currency_id._convert(price_tot, self.company_currency_id,
                                                      self.company_id,
                                                      self.invoice_date or fields.Date.context_today(self))

                price_sub_tot = self.currency_id._convert(price_sub_tot, self.company_currency_id,
                                                          self.company_id,
                                                          self.invoice_date or fields.Date.context_today(self))

                upa = self.currency_id._convert(upa, self.company_currency_id,
                                                self.company_id,
                                                self.invoice_date or fields.Date.context_today(self))

                main_price_unit = self.currency_id._convert(main_price_unit, self.company_currency_id,
                                                            self.company_id,
                                                            self.invoice_date or fields.Date.context_today(self))

                items = """ <I C="%s" N="%s" PA="%s" PB="%s" Q="%s" R="%s" RR="%s"
                                                    U="%s" UPB="%s" UPA="%s" VA="%s" VR="%s"/> """ % (
                    product.product_id.default_code,
                    product.product_id.name,
                    ('%.2f' % price_tot),
                    ('%.2f' % price_sub_tot),
                    quantity,
                    int(product.discount),
                    str(self.rebate_reducing_base_price).lower(),
                    product.product_uom_id.name,
                    ('%.2f' % main_price_unit),
                    ('%.2f' % upa),
                    ('%.2f' % vat_amt),
                    ('%.2f' % tax_percentage))

                con_items += '\n' + items

            same_tax_dic = {}
            for tax in self.invoice_line_ids:
                for t in tax.tax_ids:
                    if t.amount not in same_tax_dic:
                        same_tax_dic[t.amount] = [tax.quantity, tax.price_subtotal, round(tax.vat_amount, 2), t.amount]
                    elif t.amount in same_tax_dic:
                        same_tax_dic[t.amount][0] += tax.quantity
                        same_tax_dic[t.amount][1] += tax.price_subtotal
                        same_tax_dic[t.amount][2] += round(tax.vat_amount, 2)
                        same_tax_dic[t.amount][3] = t.amount

            con_same_taxes = ""
            same_1 = 0
            for same in same_tax_dic.values():
                if self.corrective_type != 'credit':
                    same_1 = same[1]

                if self.is_bad_debt or self.corrective_type == 'credit' or (
                        self.corrective_type == 'corrective' and self.reversed_entry_id):
                    same_1 = -1 * same[1]

                same_2 = same[2]
                same_2 = self.currency_id._convert(same_2, self.company_currency_id,
                                                   self.company_id,
                                                   self.invoice_date or fields.Date.context_today(self))

                same_1 = self.currency_id._convert(same_1, self.company_currency_id,
                                                   self.company_id,
                                                   self.invoice_date or fields.Date.context_today(self))

                same_taxes = """ <SameTax NumOfItems="%s" PriceBefVAT="%s" VATAmt="%s" VATRate="%s"/> """ % (
                    int(same[0]),
                    ('%.2f' % same_1),
                    ('%.2f' % same_2),
                    ('%.2f' % same[
                        3]),)

                con_same_taxes += '\n' + same_taxes

            tot_vat_amt = 0
            if self.amount_tax_signed:
                tot_vat_amt = self.amount_tax_signed

            corrective_inv = ''
            if self.corrective_type == 'credit' or self.corrective_type == 'debit' or self.corrective_type == 'corrective':
                corrective_inv = """ <CorrectiveInv IICRef="%s" IssueDateTime="%s" Type="%s"/> """ % (
                    self.iic_ref, self.corrective_issue_date_time, self.corrective_type.upper())
            bad_debt_inv = False
            if self.is_bad_debt or self.corrective_type == 'credit':
                bad_debt_inv = """ <BadDebtInv IICRef="%s" IssueDateTime="%s"/> """ % (
                    self.bad_debt_iic_ref, self.bad_debt_issue_date_time)

            if not self.company_id.id_type:
                raise UserError(_("Please set 'ID Type' field in Company Settings"))
            if not self.type_of_inv:
                raise UserError(_("Please set 'Invoice Type field in User Settings'"))

            header = """<Header SendDateTime="%s" UUID="8d216f9a-55bb-445a-be32-30137f11b964"/>""" % send_date_time
            sub_del_type = ''
            if self.is_subsequent_delivery:
                if self.subseq_deliv_type == 'technical_error':
                    sub_del_type = 'TECHNICALERROR'
                elif self.subseq_deliv_type == 'no_internet':
                    sub_del_type = 'NOINTERNET'
                elif self.subseq_deliv_type == 'bound_book':
                    sub_del_type = 'BOUNDBOOK'
                elif self.subseq_deliv_type == 'service':
                    sub_del_type = 'SERVICE'

                header = """<Header SendDateTime='%s' UUID="8d216f9a-55bb-445a-be32-30137f11b964" 
                SubseqDelivType='%s'/>""" \
                         % (send_date_time, sub_del_type)

            currency = ''
            buyer = ''
            if self.currency_id != self.company_currency_id:
                currency = """<Currency Code='%s' ExRate="%s"/>""" % (self.currency_id.name, self.main_curr_rate)

            if self.is_self_issued_invoice or self.is_reverse_charge or self.type_of_inv == 'noncash':
                if not self.partner_id.id_type or not self.partner_id.vat:
                    raise UserError(_('ID Type or ID Num is not configured in the partner form'))
                else:
                    buyer = """<Buyer IDType='%s' IDNum="%s" Name="%s" Address="%s" Town="%s" Country="%s"/>""" % \
                            (self.partner_id.id_type.upper(),
                             self.partner_id.vat,
                             self.partner_id.name,
                             self.partner_id.street,
                             self.partner_id.city,
                             self.company_id.country_fiscalisation_code)

            invoice_name = self.name
            invoice_number = invoice_name.split('/')[3].lstrip('0')
            invoice_year = invoice_name.split('/')[1]
            self.inv_num = invoice_number + '/' + invoice_year

            # amt_tot = self.amount_total
            amt_tot = self.amount_total_signed
            # amt_untax = self.amount_untaxed
            amt_untax = self.amount_untaxed_signed

            if self.corrective_type != 'credit':
                # amt_tot = self.amount_total
                amt_tot = self.amount_total_signed
                # amt_untax = self.amount_untaxed
                amt_untax = self.amount_untaxed_signed
                tot_vat_amt = tot_vat_amt

            if self.is_bad_debt and not self.reversed_entry_id:
                # amt_tot = -1 * self.amount_total
                amt_tot = -1 * self.amount_total_signed
                # amt_untax = -1 * self.amount_untaxed
                amt_untax = -1 * self.amount_untaxed_signed
                tot_vat_amt = -1 * tot_vat_amt

            if self.corrective_type == 'credit' or (
                    self.corrective_type == 'corrective' and self.reversed_entry_id) or (
                    self.is_bad_debt and self.reversed_entry_id):
                # amt_tot = self.amount_total
                amt_tot = self.amount_total_signed
                # amt_untax = self.amount_untaxed
                amt_untax = self.amount_untaxed_signed
                tot_vat_amt = tot_vat_amt

            invoice = """<Invoice BusinUnitCode = "%s" IssueDateTime = "%s" IIC = "%s" IICSignature = "%s"
                                                    InvNum = "%s" InvOrdNum = "%s" IsIssuerInVAT = "%s" IsReverseCharge = "%s"
                                                    IsSimplifiedInv = "%s" OperatorCode = "%s" SoftCode = "%s" TotPrice = "%s"
                                                    TotPriceWoVAT = "%s" TotVATAmt = "%s" TypeOfInv = "%s"
                                                    IsEinvoice = "%s" >""" % \
                      (self.user_id.business_unit_code,
                       self.issue_date_time,
                       self.iic,
                       self.iic_signature,
                       self.inv_num,
                       invoice_number,
                       str(self.is_issuer_in_vat).lower(),
                       str(self.is_reverse_charge).lower(),
                       str(self.is_simplified_inv).lower(),
                       self.user_id.operator_code,
                       self.company_id.software_code,
                       ('%.2f' % amt_tot),
                       ('%.2f' % amt_untax),
                       ('%.2f' % tot_vat_amt),
                       self.type_of_inv.upper(),
                       str(self.is_e_invoice).lower())

            if self.is_self_issued_invoice:
                invoice = """<Invoice BusinUnitCode = "%s" IssueDateTime = "%s" IIC = "%s" IICSignature = "%s"
                                        InvNum = "%s" InvOrdNum = "%s" IsIssuerInVAT = "%s" IsReverseCharge = "%s"
                                        IsSimplifiedInv = "%s" OperatorCode = "%s" SoftCode = "%s" TotPrice = "%s"
                                        TotPriceWoVAT = "%s" TotVATAmt = "%s" TypeOfInv = "%s" TypeOfSelfIss = "%s" 
                                        IsEinvoice = "%s" >""" % \
                          (self.user_id.business_unit_code,
                           self.issue_date_time,
                           self.iic,
                           self.iic_signature,
                           self.inv_num,
                           invoice_number,
                           str(self.is_issuer_in_vat).lower(),
                           str(self.is_reverse_charge).lower(),
                           str(self.is_simplified_inv).lower(),
                           self.user_id.operator_code,
                           self.company_id.software_code,
                           ('%.2f' % amt_tot),
                           ('%.2f' % amt_untax),
                           ('%.2f' % tot_vat_amt),
                           self.type_of_inv.upper(),
                           self.type_of_self_iss.upper(),
                           str(self.is_e_invoice).lower())
            invoice_close = """ </Invoice> """

            # input_data = "https://efiskalizimi-app-test.tatime.gov.al/invoice-check/#/verify?iic=%s&tin=%s&crtd=%s&ord=%s&bu=%s&sw=%s&prc=%.2f" % (
            #     self.iic, self.company_id.vat,
            #     self.invoice_date_time, invoice_number,
            #     self.user_id.business_unit_code,
            #     self.company_id.software_code,
            #     amt_tot)

            input_data = str(
                self.company_id.qr_code_check_portal_url) + "iic=%s&tin=%s&crtd=%s&ord=%s&bu=%s&sw=%s&prc=%.2f" % (
                             self.iic, self.company_id.vat,
                             self.invoice_date_time, invoice_number,
                             self.user_id.business_unit_code,
                             self.company_id.software_code,
                             amt_tot)

            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(input_data)
            qr.make(fit=True)
            img = qr.make_image()
            temp = BytesIO()
            img.save(temp, format="PNG")
            qr_image = base64.b64encode(temp.getvalue())
            self.qr_code = qr_image

            xml_content = self.env.ref('e_invoice_fiscalisation.invoice_register_template')._render({
            }).decode().format(invoice=invoice,
                               amount_total=('%.2f' % amt_tot),
                               payment_type=self.payment_types.upper(),
                               street=self.company_id.street,
                               country_fiscalisation_code=self.company_id.country_fiscalisation_code,
                               vat=self.company_id.vat,
                               id_type=self.company_id.id_type.upper(),
                               comp_name=self.company_id.name,
                               city=self.company_id.city,
                               con_items=con_items, con_same_taxes=con_same_taxes,
                               header=header,
                               corrective_inv=corrective_inv if self.corrective_type == 'credit' or self.corrective_type == 'debit' or self.corrective_type == 'corrective' else '',
                               bad_debt_inv=bad_debt_inv if self.is_bad_debt else '',
                               currency=currency if self.currency_id != self.company_currency_id else '',
                               buyer=buyer if self.is_self_issued_invoice or self.is_reverse_charge or self.type_of_inv == 'noncash' else '',
                               invoice_close=invoice_close)

            dom = xml.dom.minidom.parseString(xml_content)
            nodelist = dom.getElementsByTagName("RegisterInvoiceRequest")
            for node in nodelist:
                data = ET.fromstring(node.toxml())

                signed_root = XMLSigner(signature_algorithm="rsa-sha256", digest_algorithm="sha256",
                                        c14n_algorithm="http://www.w3.org/2001/10/xml-exc-c14n#").sign(data,
                                                                                                       key=private_key_2,
                                                                                                       cert=crypto.dump_certificate(
                                                                                                           crypto.FILETYPE_PEM,
                                                                                                           certificate))

                data_serialized = lxml_ET.tostring(signed_root)

                # url = "https://eFiskalizimi-test.tatime.gov.al/FiscalizationService-v3/FiscalizationService.wsdl"
                url = self.company_id.webservice_url_fiscalisation

                headers = {"content-type": 'text/xml; charset=utf-8'}
                body = data_serialized.decode('utf-8')

                envp = """
                    <SOAP-ENV:Envelope xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/">
                    <SOAP-ENV:Header/>
                    <SOAP-ENV:Body>
                    
                """ + body + """
                    </SOAP-ENV:Body>
                    </SOAP-ENV:Envelope>
                """

                request_attachment = self.env['ir.attachment'].create({
                    'name': self.name + '_xml_request.xml',
                    'datas': base64.encodebytes(envp.encode(encoding="utf-8")),
                    'mimetype': 'application/xml',
                })
                self.xml_request_file = request_attachment
                # self.xml_request_sent = True

                try:
                    response = requests.post(url, data=envp, headers=headers, verify=False)
                    self.xml_request_sent = True
                    response_content = response.content

                    verified_data = XMLVerifier().verify(data_serialized, x509_cert=certificate_pem)
                    response_content = xml.dom.minidom.parseString(response_content)

                    if response_content.getElementsByTagName("faultcode"):
                        self.is_subsequent_delivery = True

                        attachment = self.env['ir.attachment'].create({
                            'name': self.name + '_xml_response.xml',
                            'datas': base64.encodebytes(response.content),
                            'mimetype': 'application/xml',
                            'store_fname': 'xml_response.xml',
                            'res_model': self._name,
                            'res_id': self.id,
                        })
                    elif response_content.getElementsByTagName("FIC"):
                        attachment = self.env['ir.attachment'].create({
                            'name': self.name + '_xml_response.xml',
                            'datas': base64.encodebytes(response.content),
                            'mimetype': 'application/xml',
                        })

                        self.xml_response_file = attachment

                    if response_content.getElementsByTagName("FIC"):
                        self.fiscalised = True
                        self.fic = response_content.getElementsByTagName("FIC")[0].firstChild.nodeValue

                        self.fiscalised_msg = 'The invoice has been fiscalised successfully'
                    if self.is_subsequent_delivery and not self.fiscalised:
                        self.fiscal_error_msg = 'The invoice has not been fiscalised. Check the error in the XML response.'

                except Exception as error:
                    raise UserError(_(error))
        if self.fic and self.is_e_invoice:
            self.generate_e_invoice_request()

    @api.onchange('bad_debt_invoice_id')
    def onchange_bad_invoice(self):
        if self.bad_debt_invoice_id:
            self.bad_debt_iic_ref = self.bad_debt_invoice_id.iic
            self.bad_debt_issue_date_time = self.bad_debt_invoice_id.issue_date_time

    @api.onchange('corrective_invoice_id')
    def onchange_corrective_invoice(self):
        if self.corrective_invoice_id:
            self.iic_ref = self.corrective_invoice_id.iic
            self.corrective_issue_date_time = self.corrective_invoice_id.issue_date_time
            # self.corrective_type = 'corrective'

    #
    proces_type = fields.Selection([('P1', 'P1-Invoicing the supply of goods and services ordered on a contract basis'),
                                    ('P2', 'P2-Periodic invoicing of contract-based delivery'),
                                    ('P3', 'P3-Invoicing delivery over unforeseen orders'),
                                    ('P4', 'P4-Advance Payment'),
                                    ('P5', 'P5-Spot payment'),
                                    ('P6', 'P6-Payment before delivery on the based on a purchase order'),
                                    ('P7', 'P7-Invoices with reference to a dispatch note'),
                                    ('P8', 'P8-Invoices with reference to dispatch and receipt'),
                                    ('P9', 'P9-Approval or Negative Invoicing'),
                                    ('P10', 'P10-Corrective Invoicing'),
                                    ('P11', 'P11-Partial and final invoicing'),
                                    ('P12', 'P12-Self-invoicing')], string='Type of process', default='P1')

    document_type = fields.Selection([('82', '82-Invoice for Measured Services'),
                                      ('325', '325-Pre-invoice'),
                                      ('326', '326-Partial invoice'),
                                      ('380', '380-Commercial invoice'),
                                      ('381', '381-Approval'),
                                      ('383', '383-Debit'),
                                      ('384', '384-Corrective invoice'),
                                      ('385', '385-Fature permbledhese'),
                                      ('386', '386-Advance payment invoice'),
                                      ('389', '389-Vetefaturim'),
                                      ('394', '394-Leasing invoice')
                                      ], string='Invoice Type Code', default='380')
    # invoice_id_ref = fields.Many2one('account.invoice', 'Invoice reference') #corrective_invoice_id
    # correction = fields.Boolean('Correction') korrigjim #to_modify
    # invoice_ids = fields.Many2many('account.move', 'account_invoice_permbledhese_rel',
    #                                'invoice_permbledhese_id',
    #                                'move_id', string="Bills", copy=False)
    period_start_date = fields.Date(string='Billing start date ')
    period_end_date = fields.Date(string='Billing end date')
    issue_date = fields.Date(string='Issue Date')
    signed_ubl_xml_file = fields.Many2one('ir.attachment', attachment=True, store=True, copy=False)
    eic_xml_request_file = fields.Many2one('ir.attachment', attachment=True, store=True, copy=False)
    eic_xml_response_file = fields.Many2one('ir.attachment', attachment=True, store=True, copy=False)

    e_fiscal_error_msg = fields.Char(string='E-Fiscalisation Message', copy=False)
    e_fiscalised = fields.Boolean(string='E-Fiscalised', copy=False)

    @api.model
    def _default_fiskalizim(self):
        # inv_type = self._context.get('type', 'out_invoice')
        # if inv_type in ('out_invoice','out_refund'):
        #     return True
        # else:
        #     return False
        return False

    def _get_date_default(self):
        from_zone = tz.gettz('UTC')
        date_now = datetime.now(tz=from_zone)
        return date_now

    # @api.multi
    def generate_invoice_ubl_xml_etree_sign(self, version='2.1'):
        # if not self.korrigjim:
        nsmap, ns = self.env['base.ubl']._ubl_get_nsmap_namespace('Invoice-2', version=version)
        xml_root = etree.Element('Invoice', nsmap=nsmap)
        # else:
        #     nsmap, ns = self._ubl_get_nsmap_namespace('CreditNote-2', version=version)
        #     xml_root = etree.Element('CreditNote', nsmap=nsmap)
        self._ubl_add_header_sign(xml_root, ns, version=version)
        self._add_ubl_billing_reference(xml_root, ns, version=version)

        if not self.bad_debt_invoice_id and not self.corrective_invoice_id:
            self._ubl_add_order_reference(xml_root, ns, version=version)
        self._ubl_add_contract_document_reference(
            xml_root, ns, version=version)
        self._ubl_add_attachments(xml_root, ns, version=version)
        self._ubl_add_supplier_party(
            False, self.company_id, 'AccountingSupplierParty', xml_root, ns,
            version=version)
        self._ubl_add_customer_party(
            self.partner_id, False, 'AccountingCustomerParty', xml_root, ns,
            version=version)
        # the field 'partner_shipping_id' is defined in the 'sale' module
        if hasattr(self, 'partner_shipping_id') and self.partner_shipping_id:
            self._ubl_add_delivery(self.partner_shipping_id, xml_root, ns)
        # Put paymentmeans block even when invoice is paid ?
        payment_identifier = self.get_payment_identifier()
        # errrrrrrrrrrrrr
        self._ubl_add_payment_means(
            self.partner_bank_id, self.payment_mode_id, self.invoice_date_due,
            xml_root, ns, payment_identifier=payment_identifier,
            version=version)
        if self.invoice_payment_term_id:
            self._ubl_add_payment_terms(
                self.invoice_payment_term_id, xml_root, ns, version=version)
        self._ubl_add_tax_total(xml_root, ns, version=version)
        self._ubl_add_legal_monetary_total(xml_root, ns, version=version)

        line_number = 0
        for iline in self.invoice_line_ids:
            line_number += 1
            self._ubl_add_invoice_line(
                xml_root, iline, line_number, ns, version=version)
        return xml_root

    ###@@@
    # nsmap, ns = self._ubl_get_nsmap_namespace('Invoice-2', version=version)
    # # print('nsmap __', nsmap)
    # # print('ns __', ns)
    # # print('ns __', lxml_ET.tostring(ns))
    # # else:
    # #     nsmap, ns = self._ubl_get_nsmap_namespace('CreditNote-2', version=version)
    #
    # xml_signed = self.sign_UBL(self.company_id.certificate,
    #                            self.company_id.certificate_password,
    #                                               xml_root, ns)
    # # print('xml_signed __', lxml_ET.tostring(xml_signed))
    #
    # xml_string_signed = etree.tostring(xml_signed, encoding='UTF-8', xml_declaration=False, pretty_print=False)
    # # print('xml_string_signed __', xml_string_signed)
    # print('', xml_string_signed.decode('utf-8'))
    #
    # # if not self.korrigjim:
    # self._ubl_check_xml_schema(xml_string_signed, 'Invoice', version=version)
    # decoded_ubl = xml_string_signed.decode('utf-8')
    # print('xml decoded_ubl type', type(decoded_ubl))
    # print('xml rqst type', type(xml_string_signed))
    # # errordds
    # request_attachment = self.env['ir.attachment'].create({
    #     'name': self.name + '_ubl_xml_file.xml',
    #     'datas': base64.encodebytes(str(decoded_ubl).encode(encoding="utf-8")),
    #     'mimetype': 'application/xml',
    # })
    # self.signed_ubl_xml_file = request_attachment
    # return base64.b64encode(xml_string_signed).decode('utf-8')

    def _ubl_add_header_sign(self, parent_node, ns, version='2.1'):
        customization_id = etree.SubElement(
            parent_node, ns['cbc'] + 'CustomizationID')
        customization_id.text = 'urn:cen.eu:en16931:2017'
        profile = etree.SubElement(
            parent_node, ns['cbc'] + 'ProfileID')
        profile.text = self.proces_type
        # ubl_version = etree.SubElement(
        #     parent_node, ns['cbc'] + 'UBLVersionID')
        # ubl_version.text = version
        doc_id = etree.SubElement(parent_node, ns['cbc'] + 'ID')
        # doc_id.text = self.invoice_number
        doc_id.text = self.inv_num
        issue_date = etree.SubElement(parent_node, ns['cbc'] + 'IssueDate')
        # issue_date.text = self.date_invoice
        # issue_date.text = str(self.invoice_date)
        # issue_date1 = datetime.strptime(self.issue_date_time, "%Y-%m-%d")
        issue_date1 = self.issue_date.strftime("%Y-%m-%d")
        issue_date.text = issue_date1
        # if self.date_due and not self.korrigjim:
        due_date = etree.SubElement(parent_node, ns['cbc'] + 'DueDate')
        # due_date.text = self.date_due

        # date_time = datetime.now()
        invoice_date_due = self.invoice_date_due.strftime("%Y-%m-%d")
        # invoice_date_due1 = datetime.strptime(invoice_date_due, "%Y-%m-%d")
        # inv_date_time = invoice_date_due1.astimezone(pytz.timezone(self.user_id.tz)).isoformat()
        due_date.text = invoice_date_due

        # if self.type == 'out_invoice' and not self.korrigjim:
        type_code = etree.SubElement(
            parent_node, ns['cbc'] + 'InvoiceTypeCode')
        # elif self.type == 'out_invoice' and self.korrigjim:
        #     type_code = etree.SubElement(
        #         parent_node, ns['cbc'] + 'CreditNoteTypeCode')
        # if self.type == 'out_invoice':
        #     type_code.text = '380'
        # elif self.type == 'out_refund':
        #     type_code.text = '381'
        type_code.text = self.document_type
        note = etree.SubElement(parent_node, ns['cbc'] + 'Note')
        # note.text = 'IIC=' + self.nslf + '#AAI#'
        note.text = 'IIC=' + self.iic + '#AAI#'
        note2 = etree.SubElement(parent_node, ns['cbc'] + 'Note')
        note2.text = 'IICSignature=' + self.iic_signature + '#AAI#'
        note3 = etree.SubElement(parent_node, ns['cbc'] + 'Note')
        # note3.text = 'FIC=' + self.nivf + '#AAI#'
        note3.text = 'FIC=' + self.fic + '#AAI#'
        note4 = etree.SubElement(parent_node, ns['cbc'] + 'Note')
        # note4.text = 'IssueDateTime=' + self.get_isodate(self.date_fiskalizimi) + '#AAI#'
        note4.text = 'IssueDateTime=' + self.issue_date_time + '#AAI#'
        note5 = etree.SubElement(parent_node, ns['cbc'] + 'Note')
        note5.text = 'OperatorCode=' + self.user_id.operator_code + '#AAI#'
        note6 = etree.SubElement(parent_node, ns['cbc'] + 'Note')
        # note6.text = 'BusinessUnitCode=' + self.arka_id.area_code + '#AAI#'
        note6.text = 'BusinessUnitCode=' + self.user_id.business_unit_code + '#AAI#'
        note7 = etree.SubElement(parent_node, ns['cbc'] + 'Note')
        # note7.text = 'SoftwareCode=' + self.company_id.certification_code + '#AAI#'
        note7.text = 'SoftwareCode=' + self.company_id.software_code + '#AAI#'
        note8 = etree.SubElement(parent_node, ns['cbc'] + 'Note')
        # note8.text = 'IsBadDebtInv=false#AAI#' if not self.borxh else 'IsBadDebtInv=true#AAI#'
        note8.text = 'IsBadDebtInv=false#AAI#' if not self.is_bad_debt else 'IsBadDebtInv=true#AAI#'
        if self.currency_id != self.company_id.currency_id:
            note9 = etree.SubElement(parent_node, ns['cbc'] + 'Note')
            note9.text = 'ExRate=' + str(self.rate) + '#AAI#'
        doc_currency = etree.SubElement(
            parent_node, ns['cbc'] + 'DocumentCurrencyCode')
        doc_currency.text = self.currency_id.name
        tax_currency = etree.SubElement(
            parent_node, ns['cbc'] + 'TaxCurrencyCode')
        tax_currency.text = self.company_id.currency_id.name

        # price_currency = etree.SubElement(
        #     parent_node, ns['cbc'] + 'PricingCurrencyCode')
        # price_currency.text = self.company_id.currency_id.name

        # payment_currency = etree.SubElement(
        #     parent_node, ns['cbc'] + 'PaymentCurrencyCode')
        # payment_currency.text = self.currency_id.name

        # payment_alt_currency = etree.SubElement(
        #     parent_node, ns['cbc'] + 'PaymentAlternativeCurrencyCode')
        # payment_alt_currency.text = self.company_id.currency_id.name

        # accounting_currency = etree.SubElement(
        #     parent_node, ns['cbc'] + 'AccountingCostCode')
        # accounting_currency.text = self.company_id.currency_id.name

    def _add_ubl_billing_reference(self, parent_node, ns, version='2.1'):
        if self.bad_debt_invoice_id or self.corrective_invoice_id:
            # if not self.invoice_ids:
            billing_ref = etree.SubElement(parent_node, ns['cac'] + 'BillingReference')
            invoice_ref = etree.SubElement(billing_ref, ns['cac'] + 'InvoiceDocumentReference')
            ref_id = etree.SubElement(invoice_ref, ns['cbc'] + 'ID')
            # if self.borxh:
            if self.is_bad_debt:
                ref_id.text = self.bad_debt_invoice_id.iic

            if self.to_modify:
                ref_id.text = self.corrective_invoice_id.iic
            # else:
            #     for invoice in self.invoice_ids:
            #         billing_ref = etree.SubElement(parent_node, ns['cac'] + 'BillingReference')
            #         invoice_ref = etree.SubElement(billing_ref, ns['cac'] + 'InvoiceDocumentReference')
            #         ref_id = etree.SubElement(invoice_ref, ns['cbc'] + 'ID')
            #         ref_id.text = invoice.nslf

    def _ubl_add_order_reference(self, parent_node, ns, version='2.1'):
        self.ensure_one()
        if self.name:
            order_ref = etree.SubElement(
                parent_node, ns['cac'] + 'OrderReference')
            order_ref_id = etree.SubElement(
                order_ref, ns['cbc'] + 'ID')
            order_ref_id.text = self.name

    def _ubl_add_contract_document_reference(
            self, parent_node, ns, version='2.1'):
        self.ensure_one()
        cdr_dict = self._ubl_get_contract_document_reference_dict()
        for doc_type_code, doc_id in cdr_dict.items():
            cdr = etree.SubElement(
                parent_node, ns['cac'] + 'ContractDocumentReference')
            cdr_id = etree.SubElement(cdr, ns['cbc'] + 'ID')
            cdr_id.text = doc_id
            cdr_type_code = etree.SubElement(
                cdr, ns['cbc'] + 'DocumentTypeCode')
            cdr_type_code.text = doc_type_code

    def _ubl_get_contract_document_reference_dict(self):
        '''Result: dict with key = Doc Type Code, value = ID'''
        self.ensure_one()
        return {}

    def _ubl_add_attachments(self, parent_node, ns, version='2.1'):
        if (
                self.company_id.embed_pdf_in_ubl_xml_invoice and
                not self._context.get('no_embedded_pdf')):
            docu_reference = etree.SubElement(
                parent_node, ns['cac'] + 'AdditionalDocumentReference')
            docu_reference_id = etree.SubElement(
                docu_reference, ns['cbc'] + 'ID')
            # docu_reference_id.text = 'Invoice-' + self.number + '.pdf'
            docu_reference_id.text = 'Invoice-' + self.name + '.pdf'
            attach_node = etree.SubElement(
                docu_reference, ns['cac'] + 'Attachment')
            binary_node = etree.SubElement(
                attach_node, ns['cbc'] + 'EmbeddedDocumentBinaryObject',
                mimeCode="application/pdf")
            ctx = dict()
            ctx['no_embedded_ubl_xml'] = True
            pdf_inv = self.with_context(ctx).env.ref(
                'account.account_invoices')._render_qweb_pdf(self.ids)[0]
            binary_node.text = base64.b64encode(pdf_inv)

    def get_payment_identifier(self):
        """This method is designed to be inherited in localization modules"""
        self.ensure_one()
        return None

    def _ubl_add_tax_total(self, xml_root, ns, version="2.1"):
        self.ensure_one()
        cur_name = self.currency_id.name
        tax_total_node = etree.SubElement(xml_root, ns["cac"] + "TaxTotal")
        tax_amount_node = etree.SubElement(
            tax_total_node, ns["cbc"] + "TaxAmount", currencyID=cur_name
        )
        prec = self.currency_id.decimal_places
        tax_amount_node.text = "%0.*f" % (prec, self.amount_tax)
        if not float_is_zero(self.amount_tax, precision_digits=prec):
            tax_lines = self.line_ids.filtered(lambda line: line.tax_line_id)
            res = {}
            # There are as many tax line as there are repartition lines
            done_taxes = set()
            for line in tax_lines:
                res.setdefault(
                    line.tax_line_id.tax_group_id,
                    {"base": 0.0, "amount": 0.0, "tax": False},
                )
                res[line.tax_line_id.tax_group_id]["amount"] += line.price_subtotal
                tax_key_add_base = tuple(self._get_tax_key_for_group_add_base(line))
                if tax_key_add_base not in done_taxes:
                    res[line.tax_line_id.tax_group_id]["base"] += line.tax_base_amount
                    res[line.tax_line_id.tax_group_id]["tax"] = line.tax_line_id
                    done_taxes.add(tax_key_add_base)
            res = sorted(res.items(), key=lambda l: l[0].sequence)
            for _group, amounts in res:
                self._ubl_add_tax_subtotal(
                    amounts["base"],
                    amounts["amount"],
                    amounts["tax"],
                    cur_name,
                    tax_total_node,
                    ns,
                    version=version,
                )

    def _ubl_add_legal_monetary_total(self, parent_node, ns, version='2.1'):
        monetary_total = etree.SubElement(
            parent_node, ns['cac'] + 'LegalMonetaryTotal')
        cur_name = self.currency_id.name
        prec = self.currency_id.decimal_places
        line_total = etree.SubElement(
            monetary_total, ns['cbc'] + 'LineExtensionAmount',
            currencyID=cur_name)
        line_total.text = '%0.*f' % (prec, self.amount_untaxed)
        tax_excl_total = etree.SubElement(
            monetary_total, ns['cbc'] + 'TaxExclusiveAmount',
            currencyID=cur_name)
        tax_excl_total.text = '%0.*f' % (prec, self.amount_untaxed)
        tax_incl_total = etree.SubElement(
            monetary_total, ns['cbc'] + 'TaxInclusiveAmount',
            currencyID=cur_name)
        tax_incl_total.text = '%0.*f' % (prec, self.amount_total)
        prepaid_amount = etree.SubElement(
            monetary_total, ns['cbc'] + 'PrepaidAmount',
            currencyID=cur_name)
        prepaid_value = self.amount_total - self.amount_residual
        prepaid_amount.text = '%0.*f' % (prec, prepaid_value)
        if self.invoice_date_due:
            payable_amount = etree.SubElement(
                monetary_total, ns['cbc'] + 'PayableAmount',
                currencyID=cur_name)
            payable_amount.text = '%0.*f' % (prec, self.amount_residual)

    def _ubl_add_invoice_line(
            self, parent_node, iline, line_number, ns, version='2.1'):
        cur_name = self.currency_id.name
        # if not self.korrigjim:
        line_root = etree.SubElement(
            parent_node, ns['cac'] + 'InvoiceLine')
        # else:
        #     line_root = etree.SubElement(
        #         parent_node, ns['cac'] + 'CreditNoteLine')
        dpo = self.env['decimal.precision']
        qty_precision = dpo.precision_get('Product Unit of Measure')
        price_precision = dpo.precision_get('Product Price')
        account_precision = self.currency_id.decimal_places
        line_id = etree.SubElement(line_root, ns['cbc'] + 'ID')
        line_id.text = str(line_number)
        uom_unece_code = False
        # uom_id is not a required field on account.invoice.line
        if iline.product_uom_id and iline.product_uom_id.unece_code:
            uom_unece_code = iline.product_uom_id.unece_code

        inv_quantity_node = 'InvoicedQuantity'  # if not self.korrigjim else 'CreditedQuantity'
        if uom_unece_code:
            quantity = etree.SubElement(
                line_root, ns['cbc'] + inv_quantity_node,
                unitCode=uom_unece_code)
        else:
            quantity = etree.SubElement(
                line_root, ns['cbc'] + inv_quantity_node)
        qty = iline.quantity
        quantity.text = '%0.*f' % (qty_precision, qty)
        line_amount = etree.SubElement(
            line_root, ns['cbc'] + 'LineExtensionAmount',
            currencyID=cur_name)
        line_amount.text = '%0.*f' % (account_precision, iline.price_subtotal)
        # self._ubl_add_invoice_line_tax_total(
        #     iline, line_root, ns, version=version)
        if self.period_start_date and self.period_end_date:
            inv_period_el = etree.SubElement(line_root, ns['cac'] + 'InvoicePeriod')
            start_date = etree.SubElement(inv_period_el, ns['cbc'] + 'StartDate')
            start_date1 = self.period_start_date.strftime("%Y-%m-%d")
            start_date.text = start_date1

            end_date = etree.SubElement(inv_period_el, ns['cbc'] + 'EndDate')
            end_date1 = self.period_end_date.strftime("%Y-%m-%d")
            end_date.text = end_date1
        self._ubl_add_item(
            iline.name, iline.product_id, line_root, ns, 'sale',
            version=version)
        price_node = etree.SubElement(line_root, ns['cac'] + 'Price')
        price_amount = etree.SubElement(
            price_node, ns['cbc'] + 'PriceAmount', currencyID=cur_name)
        price_unit = 0.0
        # Use price_subtotal/qty to compute price_unit to be sure
        # to get a *tax_excluded* price unit
        if not float_is_zero(qty, precision_digits=qty_precision):
            price_unit = float_round(
                iline.price_subtotal / float(qty),
                precision_digits=price_precision)
        price_amount.text = '%0.*f' % (price_precision, price_unit)
        if uom_unece_code:
            base_qty = etree.SubElement(
                price_node, ns['cbc'] + 'BaseQuantity',
                unitCode=uom_unece_code)
        else:
            base_qty = etree.SubElement(price_node, ns['cbc'] + 'BaseQuantity')
        base_qty.text = '%0.*f' % (qty_precision, qty)

    def sign_UBL(self, certificate, password, root, ns):
        extensions = etree.Element(ns['ext'] + 'UBLExtensions')
        # extensions = etree.Element('UBLExtensions')
        extension = etree.SubElement(extensions, ns['ext'] + 'UBLExtension')
        # extension = etree.SubElement(extensions, 'UBLExtension')
        extension_content = etree.SubElement(extension, ns['ext'] + 'ExtensionContent')
        # extension_content = etree.SubElement(extension, 'ExtensionContent')
        ubl_doc_signature = etree.SubElement(extension_content, ns['sig'] + 'UBLDocumentSignatures')
        # ubl_doc_signature = etree.SubElement(extension_content, 'UBLDocumentSignatures')
        sign_info = etree.SubElement(ubl_doc_signature, ns['sac'] + 'SignatureInformation')
        # sign_info = etree.SubElement(ubl_doc_signature, 'SignatureInformation')
        sign_info.text = ''
        root.insert(0, extensions)

        p12 = crypto.load_pkcs12(base64.b64decode(certificate), bytes(password, 'utf-8'))
        cert = crypto.dump_certificate(crypto.FILETYPE_PEM, p12.get_certificate())
        private_key = crypto.dump_privatekey(crypto.FILETYPE_PEM, p12.get_privatekey())

        signed_root = XMLSigner(method=signxml.methods.enveloped, signature_algorithm='rsa-sha256',
                                digest_algorithm='sha256',
                                c14n_algorithm='http://www.w3.org/2001/10/xml-exc-c14n#').sign(root, key=private_key,
                                                                                               cert=cert,
                                                                                               id_attribute='Request')
        signature = XMLVerifier().verify(signed_root, x509_cert=cert).signature_xml
        sign_info.insert(1, signature)
        return root

    def generate_e_invoice_request(self):

        # if not self.company_id.certificate_password or not self.company_id.certificate:
        #     raise UserError(_('Certificate and Password of the Certificate must be given.'))
        if not self.company_id.einvoice_url:
            raise UserError(_('Need to configure "Webservice URL Electronic Invoice" in the Company settings'))

        try:
            p12 = crypto.load_pkcs12(base64.b64decode(self.company_id.certificate),
                                     self.company_id.certificate_password)
        except Exception as error:
            raise UserError(error)
        certificate = p12.get_certificate()
        # ca = p12.get_ca_certificates()
        cer_pem = crypto.dump_certificate(crypto.FILETYPE_PEM, certificate)
        private_key = crypto.dump_privatekey(crypto.FILETYPE_PEM, p12.get_privatekey())
        for to_del in ['\n', ssl.PEM_HEADER, ssl.PEM_FOOTER]:
            cer_pem = cer_pem.replace(to_del.encode('UTF-8'), b'')

        certificate_pem = cer_pem.decode('utf-8')

        for to_del in ['\n', ssl.PEM_HEADER, ssl.PEM_FOOTER]:
            private_key1 = private_key.replace(to_del.encode('UTF-8'), b'')

        private_key_2 = private_key1.decode('utf-8')

        # signed_ubl = self.generate_invoice_ubl_xml_etree_sign(version='2.1')
        date_time = datetime.now()
        normal_invoice_date = date_time.strftime("%Y-%m-%d %H:%M:%S")
        normal_invoice_date1 = datetime.strptime(normal_invoice_date, "%Y-%m-%d %H:%M:%S")
        send_date_time = normal_invoice_date1.astimezone(pytz.timezone(self.user_id.tz)).isoformat()

        uuid_nr = "8d216f9a-55bb-445a-be32-30137f11b964"
        header_data = soap_methods_fiskalizim.get_header_data(send_date_time, uuid_nr)
        version = self.get_ubl_version()
        xml_root = self.generate_invoice_ubl_xml_etree_sign(version=version)
        nsmap, ns = self._ubl_get_nsmap_namespace('Invoice-2', version=version)
        xml_signed = self.sign_UBL(self.company_id.certificate, self.company_id.certificate_password,
                                   xml_root, ns)

        xml_string_signed = etree.tostring(xml_signed, encoding='UTF-8', xml_declaration=False, pretty_print=False)
        self._ubl_check_xml_schema(xml_string_signed, 'Invoice', version=version)
        decoded_ubl = xml_string_signed.decode('utf-8')

        request_attachment = self.env['ir.attachment'].create({
            'name': self.name + '_ubl_xml_file.xml',
            'datas': base64.encodebytes(str(decoded_ubl).encode(encoding="utf-8")),
            'mimetype': 'application/xml',
        })
        self.signed_ubl_xml_file = request_attachment

        invoice_data = {
            '2__@UblInvoice': base64.b64encode(xml_string_signed).decode('utf-8')
        }

        RegisterEInvoiceRequest = soap_methods_fiskalizim.get_einvoice_data()
        RegisterEInvoiceRequest['4__Header'] = header_data
        RegisterEInvoiceRequest['5__EinvoiceEnvelope'] = {'1__UblInvoice': [invoice_data]}

        proxy_url = self.company_id.proxy_var or False
        # einvoice_url = "https://einvoice-test.tatime.gov.al/EinvoiceService-v1/EinvoiceService.wsdl"
        einvoice_url = self.company_id.einvoice_url
        if einvoice_url:
            try:
                invoice_response = self.register_Request(einvoice_url,
                                                         self.company_id.certificate,
                                                         self.company_id.certificate_password,
                                                         RegisterEInvoiceRequest, 'RegisterEinvoiceRequest',
                                                         ubl=True, proxy_var=proxy_url)
                # final_response = lxml_ET.tostring(invoice_response).decode('utf-8')
                # response_attachment = self.env['ir.attachment'].create({
                #     'name': self.name + '_eic_response_xml_file.xml',
                #     'datas': base64.encodebytes(str(final_response).encode(encoding="utf-8")),
                #     'mimetype': 'application/xml',
                # })
                # self.eic_xml_response_file = response_attachment
            except Exception as error:
                print('HERE')
                raise UserError(_(error))

    ###@@###
    # header = """<Header SendDateTime="%s" UUID="8d216f9a-55bb-445a-be32-30137f11b964"/>""" % send_date_time
    # ubl = signed_ubl
    #
    # xml_content = self.env.ref('e_invoice_fiscalisation.e_invoice_register_template')._render({
    # }).decode().format(e_header=header,
    #                    ubl=ubl)
    # # print('xml_content', xml_content)
    #
    # dom = xml.dom.minidom.parseString(xml_content)
    # nodelist = dom.getElementsByTagName("RegisterEinvoiceRequest")
    # for node in nodelist:
    #     data = ET.fromstring(node.toxml())
    #
    #     signed_root = XMLSigner(signature_algorithm="rsa-sha256", digest_algorithm="sha256",
    #                             c14n_algorithm="http://www.w3.org/2001/10/xml-exc-c14n#").sign(data,
    #                                                   key=private_key_2,
    #                                                   cert=crypto.dump_certificate(
    #                                                       crypto.FILETYPE_PEM,
    #                                                     certificate))
    #     data_serialized = lxml_ET.tostring(signed_root)
    #
    #     url = "https://einvoice-test.tatime.gov.al/EinvoiceService-v1/EinvoiceService.wsdl"
    #     headers = {"content-type": 'text/xml; charset=utf-8'}
    #     body = data_serialized.decode('utf-8')
    #
    #     envp = """<S:Envelope xmlns:S="http://schemas.xmlsoap.org/soap/envelope/">
    #                        <S:Header/>
    #                        <S:Body>
    #                           """ + body + """
    #                        </S:Body>
    #                     </S:Envelope>"""
    #     request_attachment = self.env['ir.attachment'].create({
    #         'name': self.name + '_eic_xml_request.xml',
    #         'datas': base64.encodebytes(envp.encode(encoding="utf-8")),
    #         'mimetype': 'application/xml',
    #     })
    #     self.eic_xml_request_file = request_attachment
    #
    #     response = requests.post(url, data=envp, headers=headers, verify=False)
    #     response_content = response.content
    #     print('response_content', response_content)
    #
    #     attachment = self.env['ir.attachment'].create({
    #         'name': self.name + '_eic_xml_response.xml',
    #         'datas': base64.encodebytes(response.content),
    #         'mimetype': 'application/xml',
    #     })
    #
    #     self.eic_xml_response_file = attachment
    #
    #     verified_data = XMLVerifier().verify(data_serialized, x509_cert=certificate_pem)
    #     response_content = xml.dom.minidom.parseString(response_content)
    #     # print('response_content', response_content)

    def register_Request(self, url, certificate_file, password, dict_data, request_type, ubl=False, proxy_var=False):

        xml_data = self.dict2xml(dict_data, request_type)
        xml_signed = self.sign_XML(xml_data, certificate_file, password)
        response = self.make_request(xml_signed, url, ubl=ubl, proxy_var=proxy_var)
        respones_content = response.content
        response_content = xml.dom.minidom.parseString(respones_content)
        if response_content.getElementsByTagName("faultcode"):
            self.fiscal_error_msg = 'The E-invoice has not been fiscalised. Check the error in the XML response.'

            # self.is_subsequent_delivery = True

            attachment = self.env['ir.attachment'].create({
                'name': self.name + 'e_invoice_xml_response.xml',
                'datas': base64.encodebytes(response.content),
                'mimetype': 'application/xml',
                'store_fname': 'xml_response.xml',
                'res_model': self._name,
                'res_id': self.id,
            })
        if response_content.getElementsByTagName("ns2:EIC"):
            self.eic = response_content.getElementsByTagName("ns2:EIC")[0].firstChild.nodeValue
            self.fiscalised_msg = 'The E-invoice has been fiscalised successfully'
            self.e_fiscalised = True

            print("response $$", response.content)

            final_response = response.content.decode('utf-8')
            print("final_response@@@", final_response)
            # tttttttttttttttttttttt
            response_attachment = self.env['ir.attachment'].create({
                'name': self.name + '_eic_response_xml_file.xml',
                'datas': base64.encodebytes(str(final_response).encode(encoding="utf-8")),
                'mimetype': 'application/xml',
            })
            self.eic_xml_response_file = response_attachment
        if self.is_e_invoice and not response_content.getElementsByTagName("ns2:EIC"):
            self.e_fiscal_error_msg = 'The E-invoice has not been fiscalised. Check the error in the XML response.'

        xml_response = etree.fromstring(response.content)

        return xml_response

    def dict2xml(self, d, root_node=None):
        wrap = False if root_node is None or isinstance(d, list) else True
        root = 'objects' if root_node is None else root_node
        root_singular = root[:-1] if 's' == root[-1] and root_node is None else root
        xml = ''
        children = []
        end_tag_element = False

        if isinstance(d, dict):
            d_sorted = sorted(d.items(), key=(lambda key_value: self._dict_sort_key(key_value)))
            for key, value in d_sorted:
                key2 = self._remove_order_id(key)
                end_tag_element = False
                if isinstance(value, dict):
                    children.append(self.dict2xml(value, key))
                elif isinstance(value, list):
                    children.append(self.dict2xml(value, key))
                else:
                    if '@' not in key:
                        xml = xml + ' ' + key2 + '="' + str(value) + '"'
                    else:
                        xml = xml + '>' + str(value) + '</' + key2[1:]
                        end_tag_element = True
        else:
            for value in d:
                children.append(self.dict2xml(value, root_singular))

        end_tag = '>' if 0 < len(children) or end_tag_element else '/>'

        if wrap or isinstance(d, dict):
            xml = '<' + self._remove_order_id(root) + xml + end_tag

        if 0 < len(children):
            for child in children:
                xml = xml + child

            if wrap or isinstance(d, dict):
                xml = xml + '</' + self._remove_order_id(root) + '>'

        return xml

    def _dict_sort_key(self, key_value):
        key = key_value[0]
        match = re.match('(\d+)__.*', key)
        return match and int(match.groups()[0]) or key

    def _remove_order_id(self, key):
        match = re.match('\d+__(.*)', key)
        return match and match.groups()[0] or key

    def sign_XML(self, request_to_sign, certificate, password):
        # base64.b64decode(certificate)
        root = etree.fromstring(request_to_sign)
        p12 = crypto.load_pkcs12(base64.b64decode(certificate), bytes(password, 'utf-8'))
        cert = crypto.dump_certificate(crypto.FILETYPE_PEM, p12.get_certificate())
        private_key = crypto.dump_privatekey(crypto.FILETYPE_PEM, p12.get_privatekey())

        signed_root = XMLSigner(method=signxml.methods.enveloped, signature_algorithm='rsa-sha256',
                                digest_algorithm='sha256',
                                c14n_algorithm='http://www.w3.org/2001/10/xml-exc-c14n#').sign(root, key=private_key,
                                                                                               cert=cert,
                                                                                               id_attribute='Request')
        # signature = XMLVerifier().verify(signed_root, x509_cert=cert).signature_xml
        signed_root_str = etree.tostring(signed_root).decode('utf-8')
        # print('signed_root_str', signed_root_str)
        return signed_root_str

    def make_request(self, xml_data, url, ubl=False, proxy_var=False):
        # thisisnotanerror
        if not ubl:
            request_data = """<SOAP-ENV:Envelope xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:ns0="http://schemas.xmlsoap.org/soap/envelope/" xmlns:ns1="https://eFiskalizimi.tatime.gov.al/FiscalizationService/schema">
               <SOAP-ENV:Header/>
               <ns0:Body>
                  {}
               </ns0:Body>
            </SOAP-ENV:Envelope>""".format(xml_data)
        else:
            request_data = """<S:Envelope xmlns:S="http://schemas.xmlsoap.org/soap/envelope/">
                       <S:Header/>
                       <S:Body>
                          {}
                       </S:Body>
                    </S:Envelope>""".format(xml_data)

        headers = {"Content-Type": "text/xml; charset=UTF-8", "Content-Length": str(len(request_data))}

        proxies = False
        if proxy_var:
            proxies = {'https': proxy_var}

        print('REQUEST_DATA', request_data)
        request_attachment = self.env['ir.attachment'].create({
            'name': self.name + '_eic_request_xml_file.xml',
            'datas': base64.encodebytes(str(request_data).encode(encoding="utf-8")),
            'mimetype': 'application/xml',
        })
        self.eic_xml_request_file = request_attachment

        response = requests.post(url=url, headers=headers, data=request_data, verify=False, proxies=proxies)
        return response

    def get_ubl_version(self):
        version = self._context.get('ubl_version') or '2.1'
        return version


class AccountDebitNote(models.TransientModel):
    _inherit = 'account.debit.note'

    def _prepare_default_values(self, move):
        res = super(AccountDebitNote, self)._prepare_default_values(move=move)
        res['iic_ref'] = move.iic
        res['corrective_issue_date_time'] = move.issue_date_time
        res['corrective_type'] = 'debit'

        return res


class AccountMoveReversal(models.TransientModel):
    _inherit = 'account.move.reversal'

    def _prepare_default_reversal(self, move):
        res = super(AccountMoveReversal, self)._prepare_default_reversal(move=move)
        res['iic_ref'] = move.iic
        res['corrective_issue_date_time'] = move.issue_date_time
        res['corrective_type'] = 'credit'
        res['payment_type_id'] = move.payment_type_id.id

        if self.refund_method == 'cancel':
            res['corrective_type'] = 'corrective'
            res['to_modify'] = True
            res['corrective_invoice_id'] = move.id

        if self.refund_method == 'modify':
            res['corrective_type'] = 'corrective'

        return res

    def reverse_moves(self):
        res = super(AccountMoveReversal, self).reverse_moves()
        context = self.env.context

        for new_move in self.new_move_ids:
            if self.refund_method == 'modify':
                new_move.corrective_type = 'corrective'
            if new_move.move_type == 'out_invoice':
                new_move.to_modify = True
                new_move.corrective_invoice_id = context.get('active_id')
                new_move.iic_ref = new_move.corrective_invoice_id.iic
                new_move.corrective_issue_date_time = new_move.corrective_invoice_id.issue_date_time

        return res
