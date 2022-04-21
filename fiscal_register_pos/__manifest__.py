# -*- coding: utf-8 -*-
# This module and its content is copyright of Technaureus Info Solutions Pvt. Ltd.
# - © Technaureus Info Solutions Pvt. Ltd 2020. All rights reserved.

{
    'name': 'Fiscal Register POS for Point of Sale',
    'version': '14.0.2.6',
    'category': 'Point of Sale',
    'sequence': 1,
    'summary': 'Adding Fiscal printer and .txt templates for device types.',
    'description': """
        Adding Fiscal printer and .txt templates for device types.
    """,
    'website': 'http://www.technaureus.com/',
    'author': 'Technaureus Info Solutions Pvt. Ltd.',
    'depends': ['fiscal_device', 'point_of_sale'],
    'data': [
        'security/ir.model.access.csv',
        'views/pos_config_view.xml',
        'views/pos_payment_method_view.xml',
        'views/pos_template.xml',
    ],
    'qweb': [
        'static/src/xml/Screens/PaymentScreen/PaymentScreen.xml',
    ],
    'images': [],
    'installable': True,
    'auto_install': False,
    'application': True,
}
