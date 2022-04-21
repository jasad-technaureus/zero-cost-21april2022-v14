# -*- coding: utf-8 -*-
# This module and its content is copyright of Technaureus Info Solutions Pvt. Ltd.
# - © Technaureus Info Solutions Pvt. Ltd 2020. All rights reserved.

{
    'name': 'Pos Session Invoice',
    'version': '14.0.1.1',
    'category': 'Point of Sale',
    'sequence': 1,
    'summary': 'Adding Invoice when pos session closing time',
    'description': """
        Adding Invoice on pos session.
    """,
    'website': 'http://www.technaureus.com/',
    'author': 'Technaureus Info Solutions Pvt. Ltd.',
    'depends': ['point_of_sale'],
    'data': [
        'views/pos_config_view.xml',
    ],
    'images': [],
    'installable': True,
    'auto_install': False,
    'application': True,
}
