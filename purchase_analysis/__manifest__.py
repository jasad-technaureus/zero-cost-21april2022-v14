# -*- coding: utf-8 -*-
# This module and its content is copyright of Technaureus Info Solutions Pvt. Ltd.
# - © Technaureus Info Solutions Pvt. Ltd 2020. All rights reserved.

{
    'name': 'Purchase Analysis',
    'sequence': 1,
    'version': '14.0.1.3',
    'author': 'Zero | Odoo Partner',
    'website': 'zero.com.al',
    'category': 'Purchase',
    'summary': 'Analyze your purchasing needs',
    'description': """
               Analyze your purchasing needs.
    """,
    'depends': ['purchase', 'sale_management', 'sale_purchase', 'stock', 'product_margin'],
    'license': 'Other proprietary',
    'data': [
        'security/ir.model.access.csv',
        'wizard/purchase_analysis_view.xml',
        'wizard/rfq_create_view.xml',
        'views/product_view.xml',
    ],
    'demo': [],
    'css': [],
    'installable': True,
    'auto_install': False,
    'application': False,
}
