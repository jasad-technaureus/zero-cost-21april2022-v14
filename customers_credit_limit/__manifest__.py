# -*- coding: utf-8 -*-
# This module and its content is copyright of Technaureus Info Solutions Pvt. Ltd.
# - © Technaureus Info Solutions Pvt. Ltd 2021. All rights reserved.

{
    'name': 'Customers Credit Limit',
    'version': '14.0.1.8',
    'category': 'Accounting',
    'sequence': 1,
    'summary': 'Manage customers credit limit with warning and blocking messages.',
    'description': """
       Manage customers credit limit with warning and blocking messages.
    """,
    'website': 'https://zero.com.al',
    'author': 'Zero | Odoo Partner',
    'depends': ['sale_management', 'account_accountant'],
    'data': [
        'security/ir.model.access.csv',
        'views/credit_limit.xml',
        'wizard/credit_limit_wizard.xml',
    ],
    'images': [],
    'installable': True,
    'auto_install': False,
    'application': True,
}
