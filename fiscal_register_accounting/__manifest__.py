# -*- coding: utf-8 -*-
# This module and its content is copyright of Technaureus Info Solutions Pvt. Ltd.
# - © Technaureus Info Solutions Pvt. Ltd 2020. All rights reserved.

{
    'name': 'Fiscal Register Accounting',
    'version': '14.0.2.6',
    'category': 'Accounting',
    'sequence': 1,
    'summary': 'Adding Fiscal printer and .txt templates for device types.',
    'description': """
        Adding Fiscal printer and .txt templates for device types.
    """,
    'website': 'http://www.technaureus.com/',
    'author': 'Technaureus Info Solutions Pvt. Ltd.',
    'depends': ['account', 'fiscal_device'],
    'data': [
        'security/ir.model.access.csv',
        'views/res_config_settings_view.xml',
        'views/move_views.xml'
    ],
    'images': [],
    'installable': True,
    'auto_install': False,
    'application': True,
}
