# -*- coding: utf-8 -*-
#################################################################################
# Author      : Webkul Software Pvt. Ltd. (<https://webkul.com/>)
# Copyright(c): 2015-Present Webkul Software Pvt. Ltd.
# All Rights Reserved.
#
#
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
#
# You should have received a copy of the License along with this program.
# If not, see <https://store.webkul.com/license.html/>
#################################################################################
{
  "name"                 :  "Odoo User Login Security",
  "summary"              :  """Secure your Odoo from Intruders with User Login Security""",
  "category"             :  "Extra Tools",
  "version"              :  "1.0.2",
  "sequence"             :  1,
  "author"               :  "Webkul Software Pvt. Ltd.",
  "license"              :  "Other proprietary",
  "website"              :  "https://store.webkul.com/Odoo-User-Login-Security.html",
  "description"          :  """""",
  "live_test_url"        :  "http://odoo.webkul.com:8009/web?db=loginsecurity",
  "depends"              :  ['auth_signup'],
  "data"                 :  [
                             'security/security.xml',
                             'security/ir.model.access.csv',
                             'views/dashboard.xml',
                             'views/res_users.xml',
                             'views/session.xml',
                             'views/res_config_settings.xml',
                             'templates/web.xml',
                             'templates/mail.xml',
                             'data/ir_actions_server.xml',
                             'data/ir_cron.xml',
                             'data/ir_config_parameter.xml',
                            ],
  "demo"                 :  [
                             'demo/security.xml',
                             'demo/session.session.csv',
                            ],
  "qweb"                 :  ['static/src/xml/dashboard.xml'],
  "images"               :  ['static/description/banner.png'],
  "application"          :  True,
  "price"                :  99,
  "currency"             :  "USD",
  "pre_init_hook"        :  "pre_init_check",
}
