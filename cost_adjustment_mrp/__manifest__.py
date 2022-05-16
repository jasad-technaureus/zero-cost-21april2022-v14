# -*- coding: utf-8 -*-
# This module and its content is copyright of Technaureus Info Solutions Pvt. Ltd.
# - © Technaureus Info Solutions Pvt. Ltd 2022. All rights reserved.

{
    'name': 'Cost Adjustment MRP',
    'version': '14.0.1.6',
    'category': 'Accounting',
    'sequence': 1,
    'summary': 'Cost Adjustments for MRP',
    'description': """
      Cost Adjustments for MRP
    """,
    'website': 'https://zero.com.al',
    'author': 'Zero | Odoo Partner',
    'depends': ['cost_adjustments', 'mrp', 'mrp_account'],
    'data': [
        'views/mrp_production_views.xml'
    ],
    'images': [],
    'installable': True,
    'auto_install': False,
    'application': True,
}
