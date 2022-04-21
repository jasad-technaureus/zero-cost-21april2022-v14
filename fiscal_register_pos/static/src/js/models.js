odoo.define('fiscal_register_pos.models', function (require) {
  "use strict";

  var models = require('point_of_sale.models');

    models.load_fields('pos.payment.method', ['is_bank_payment']);

        models.load_models([
                 {
                   model: 'fiscal.devices',
                   fields: ['id', 'name', 'type', 'vat1', 'vat2', 'vat3', 'vat4', 'vat5', 'header', 'footer', 'prd_dynamic', 'file_name'],
                   loaded: function(self,fiscal_devices){
                      self.fiscal_devices = fiscal_devices;
                   },
                 }
             ]);
        models.load_models([
            {
              model: 'pos.order',
              fields: ['id', 'name','amount_paid'],
              loaded: function(self,pos_orders){
                 self.pos_orders = pos_orders;
              },
            }
        ]);
        models.load_models([
            {
              model: 'account.tax',
              fields: ['id', 'amount', 'price_include'],
              loaded: function(self,product_taxes){
                 self.product_taxes = product_taxes;
              },
            }
        ]);

        models.load_models([
            {
              model: 'account.move',
              fields: ['id', 'name', 'payment_reference'],
              loaded: function(self,invoices){
                 self.invoices = invoices;
              },
            }
        ]);
});
