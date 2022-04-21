# -*- coding: utf-8 -*-
# This module and its content is copyright of Technaureus Info Solutions Pvt. Ltd.
# - © Technaureus Info Solutions Pvt. Ltd 2020. All rights reserved.

{
    'name': 'Fiscal Device',
    'version': '14.0.0.2',
    'category': 'Point of Sale',
    'sequence': 1,
    'summary': 'Adding Fiscal printer and .txt templates for device types.',
    'description': """
        Adding Fiscal printer and .txt templates for device types.
    """,
    'website': 'http://www.technaureus.com/',
    'author': 'Technaureus Info Solutions Pvt. Ltd.',
    'depends': ['base', 'account'],
    'data': [
        'security/ir.model.access.csv',
        'views/fiscal_devices.xml',
    ],
    'images': [],
    'installable': True,
    'auto_install': False,
    'application': True,
}
