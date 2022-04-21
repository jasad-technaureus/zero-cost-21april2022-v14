# -*- coding: utf-8 -*-
# This module and its content is copyright of Technaureus Info Solutions Pvt. Ltd.
# - © Technaureus Info Solutions Pvt. Ltd 2020. All rights reserved.

{
    'name': 'Zero Currency rate',
    'version': '14.0.1.7',
    'category': 'Accounting',
    'sequence': 1,
    'summary': 'Managing currency rate for main currency and foreign currencies.',
    'description': """
        Managing currency rate for main currency and foreign currencies.
    """,
    'website': 'http://www.technaureus.com/',
    'author': 'Technaureus Info Solutions Pvt. Ltd.',
    'depends': ['account'],
    'data': [
        'views/res_config_settings_view.xml',
        'views/currency_rate_view.xml',
        'views/account_move_view.xml',
        'views/account_payment_view.xml',
    ],
    'post_init_hook': 'post_init_check_main_currency',
    'images': [],
    'installable': True,
    'auto_install': False,
    'application': True,
}
