# -*- coding: utf-8 -*-
# This module and its content is copyright of Technaureus Info Solutions Pvt. Ltd. - ©
# Technaureus Info Solutions Pvt. Ltd 2020. All rights reserved.
{
    'name': 'Sales, Purchase & Invoice Global Discount',
    'version': '14.0.1.3',
    'sequence': 1,
    'category': 'Accounting',
    'summary': 'Sales, Purchase and Invoice Global Discount ',
    'author': 'Technaureus Info Solutions Pvt. Ltd.',
    'website': 'http://www.technaureus.com/',
   
    'description': """
This module is for adding global discount to sales, purchase and invoice
        """,
    'price': 36,
    'currency': 'EUR',
    'license': 'Other proprietary',
    'depends': ['account', 'sale_management', 'sale_purchase'],
    'data': [
        'views/res_config_settings_views.xml',
        'views/sale_order_view.xml',
        'views/purchase_order_view.xml',
        'report/sale_report_templates.xml',
        'report/purchase_order_templates.xml',
        'views/account_invoice_view.xml',
        'report/report_invoice.xml',
    ],
    'images': ['images/main_screenshot.png'],
    'demo': [],
    'installable': True,
    'auto_install': False,
    'application': True,
}