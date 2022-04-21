# -*- coding: utf-8 -*-
# This module and its content is copyright of Technaureus Info Solutions Pvt. Ltd.
# - © Technaureus Info Solutions Pvt. Ltd 2021. All rights reserved.

{
    'name': 'Zero Invoice',
    'version': '14.0.0.7',
    'category': 'Accounting',
    'sequence': 1,
    'summary': 'Customised Invoice Format',
    'description': """
        Customised Invoice Format
    """,
    'website': 'http://www.technaureus.com/',
    'author': 'Technaureus Info Solutions Pvt. Ltd.',
    'depends': ['zero_currency_rate'],
    'data': [
        'views/zero_invoice_report_template.xml',
        'views/zero_invoice_view.xml',
    ],
    'images': [],
    'installable': True,
    'auto_install': False,
    'application': True,
}