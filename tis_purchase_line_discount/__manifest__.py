# -*- coding: utf-8 -*-
# This module and its content is copyright of Technaureus Info Solutions Pvt. Ltd.
# - © Technaureus Info Solutions Pvt. Ltd 2020. All rights reserved.

{
    'name': 'Purchase order lines with discounts',
    'sequence': 1,
    'version': '14.0.0.1',
    'category': 'Purchases',
    'summary': 'Display Purchase order lines with discounts',
    'description': """
This module allows you to display purchase order lines with discounts.
    """,
    'author': 'Technaureus Info Solutions Pvt. Ltd.',
    'company': 'Technaureus Info Solutions Pvt. Ltd.',
    'website': 'https://www.technaureus.com',
    'depends': ['purchase_stock'],
    'price': 7.99,
    'currency': 'EUR',
    'license': 'Other proprietary',
    'data': [
    ],
    'demo': [
        'security/purchase_security.xml',
        'views/res_config_settings_views.xml',
        'views/purchase_discount_view.xml',
        'views/report_purchaseorder.xml',
        'views/account_move_views.xml',

    ],
    'css': [],
    'installable': True,
    'auto_install': False,
    'images': ['images/main_screenshot.png'],
    'live_test_url': 'https://www.youtube.com/watch?v=XTjH4nxnqvw'
}
