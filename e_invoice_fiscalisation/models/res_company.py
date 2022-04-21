# -*- coding: utf-8 -*-
# This module and its content is copyright of Technaureus Info Solutions Pvt. Ltd.
# - © Technaureus Info Solutions Pvt. Ltd 2020. All rights reserved.

from odoo import api, fields, models


class Companies(models.Model):
    _inherit = 'res.company'

    is_issuer_in_vat = fields.Boolean(string='Is Issuer in VAT', default=True)
    software_code = fields.Char(string='Software Code')
    maintenance_software_code = fields.Char(string='Maintenance Software Code')
    webservice_url_fiscalisation = fields.Char(string='Webservice URL Fiscalisation')
    qr_code_check_portal_url = fields.Char(string='QR Code Check Portal URL')
    certificate = fields.Binary(string='Certificate')
    certificate_password = fields.Char(string='Certificate Password')
    id_type = fields.Selection([('nuis', 'NUIS'),
                                ('id', 'ID'),
                                ('pass', 'PASS '),
                                ('vat', 'VAT'),
                                ('tax', 'TAX'),
                                ('soc', 'SOC')], string='ID Type')
    country_fiscalisation_code = fields.Char(string='Country Fiscalisation Code', default='ALB')
# ##
#     xml_format_in_pdf_invoice = fields.Selection(
#         selection_add=[("ubl", "Universal Business Language (UBL)")], default="ubl"
#     )
    embed_pdf_in_ubl_xml_invoice = fields.Boolean(
        string="Embed PDF in UBL XML Invoice",
        help="If active, the standalone UBL Invoice XML file will include the "
             "PDF of the invoice in base64 under the node "
             "'AdditionalDocumentReference'. For example, to be compliant with the "
             "e-fff standard used in Belgium, you should activate this option.",
    )
    proxy_var = fields.Char(string='Proxy')

    einvoice_url = fields.Char(string='Webservice URL Electronic Invoice')
