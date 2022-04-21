# -*- coding: utf-8 -*-
# - © Technaureus Info Solutions Pvt. Ltd 2020. All rights reserved.
# This module and its content is copyright of Technaureus Info Solutions Pvt. Ltd.

{
    'name': 'e-Invoice Fiscalisation',
    'version': '14.0.4.5',
    'category': 'Point of Sale',
    'sequence': 1,
    'summary': 'e-Invoice Fiscalisation.',
    'description': """
        'e-Invoice Fiscalisation.
    """,
    'website': 'http://www.technaureus.com/',
    'author': 'Technaureus Info Solutions Pvt. Ltd.',
    'depends': ['account_debit_note', 'zero_currency_rate', 'base_ubl', 'base_ubl_payment', 'account_payment_partner'],
    'external_dependencies': {'python': ['signxml', 'xml', 'lxml', 'pyopenssl', 'qrcode', 'pytz', 'hashlib']},
    'data': [
        'security/ir.model.access.csv',
        'data/invoice_registration_request_template.xml',
        # 'data/invoice_e_invoice_register.xml',
        'views/res_company_view.xml',
        'views/account_move_views.xml',
        'views/res_users_views.xml',
        'views/res_partner_views.xml',
        'views/report_invoice.xml',
        'views/payment_methods_views.xml',
        'views/account_tax_views.xml',

        # 'views/res_config_settings.xml',

    ],
    'images': [],
    'installable': True,
    'auto_install': False,
    'application': True,
}
