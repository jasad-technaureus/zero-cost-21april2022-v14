# -*- coding: utf-8 -*-
# This module and its content is copyright of Technaureus Info Solutions Pvt. Ltd.
# - © Technaureus Info Solutions Pvt. Ltd 2021. All rights reserved.

{
    'name': 'Auto Deliveries, Receipts and Payments',
    'version': '14.0.4.2',
    'author': 'Zero | Odoo Partner',
    'website': 'zero.com.al',
    'category': 'Accounting',
    'summary': 'Create Delivery Orders from Customer Invoices and Receipts from Vendor Bills',
    'sequence': 1,
    'depends': ['stock_account', 'zero_currency_rate', 'sale'],
    'data': [
        'views/journal_view.xml',
        'views/account_move.xml',
        'views/stock_view.xml'
    ],
    'images': [],
    'installable': True,
    'auto_install': False,
    'application': False,
}
