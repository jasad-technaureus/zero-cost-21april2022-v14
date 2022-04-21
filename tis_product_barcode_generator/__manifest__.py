# -*- coding: utf-8 -*-
# This module and its content is copyright of Technaureus Info Solutions Pvt. Ltd.
# - © Technaureus Info Solutions Pvt. Ltd 2020. All rights reserved.

{
    "name": 'Product barcode generator',
    "category": "Stock Management",
    "version": '14.0.0.4',
    "sequence": 1,
    'summary': 'EAN13 barcode generation for product variants',
    'website': 'http://www.technaureus.com/',
    'author': 'Technaureus Info Solutions Pvt. Ltd.',
    'currency': 'EUR',
    'license': 'Other proprietary',
    "depends": [
        'product',
    ],
    "demo": [],
    "data": [
        "security/ir.model.access.csv",
        "data/ean_sequence.xml",
        "views/res_company_view.xml",
        "views/product_view.xml",
        "views/sequence_view.xml",
        "wizard/product_barcode_wizard_view.xml",
    ],
    'images': ['images/barcode_screenshot.png'],
    'installable': True,
    'application': True,
    'auto_install': False,
    'live_test_url': 'https://www.youtube.com/watch?v=yEa9PHquQAE&t=20s'
}
