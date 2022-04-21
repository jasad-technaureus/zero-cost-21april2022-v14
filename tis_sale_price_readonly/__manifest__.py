# -*- coding: utf-8 -*-
# This module and its content is copyright of Technaureus Info Solutions Pvt. Ltd.
# - © Technaureus Info Solutions Pvt. Ltd 2020. All rights reserved.

{
    'name': 'Sale Price Readonly',
    'version': '14.0.0.0.0',
    'category': 'Sales',
    'sequence': 1,
    'author': 'Technaureus Info Solutions Pvt. Ltd.',
    'summary': 'Sale Price Readonly for Specific Group of User',
    'description': """
Sale Price Readonly
================================
Sale Price Readonly for Specific Group of User.
    """,
    'website': 'http://www.technaureus.com',
    'price': 10,
    'currency': 'EUR',
    'license': 'Other proprietary',
    'depends': ['sale_management'],
    'data': [
        'security/security.xml',
        'views/sale_views.xml',
    ],
    'images': ['images/main_screenshot.png'],
    'installable': True,
    'application': True,
}
