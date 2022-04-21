# -*- coding: utf-8 -*-
# This module and its content is copyright of Technaureus Info Solutions Pvt. Ltd.
# - © Technaureus Info Solutions Pvt. Ltd 2020. All rights reserved.

{
    'name': 'Field Service – Location Tracking',
    'version': '14.0.2.1',
    'category': 'Services',
    'sequence': 1,
    'summary': 'Track the Location from Field Service Tasks.',
    'description': """
        Track the Location from Field Service Tasks.
    """,
    'website': 'https://zero.com.al',
    'author': 'Zero | Odoo Partner',
    'depends': ['industry_fsm'],
    'data': [
        'security/fsm_track_location_group.xml',
        'views/res_config_settings_views.xml',
        'views/field_service_form_view.xml',
        'views/assets.xml',

    ],
    'images': [],
    'installable': True,
    'auto_install': False,
    'application': True,
}
