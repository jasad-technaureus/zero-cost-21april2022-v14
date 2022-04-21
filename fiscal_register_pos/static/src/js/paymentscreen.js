odoo.define('fiscal_register_pos.paymentscreen', function (require) {
"use strict";
    const PaymentScreen = require('point_of_sale.PaymentScreen');
    const Registries = require('point_of_sale.Registries');
    var core = require('web.core');
    var _t = core._t;

    const TestPaymentScreen = PaymentScreen =>
        class extends PaymentScreen {
            async click_validateOrder() {
                if (this.currentOrder.get_orderlines().length === 0) {
                    this.showPopup('ErrorPopup', {
                        title: this.env._t('Empty Order'),
                        body: this.env._t(
                            'There must be at least one product in your order before it can be validated'
                        ),
                    });
                    return false;
                }
                var order = this.currentOrder;
                if(this.env.pos.config.mxm_amount_invoice == 0){
                        if(this.currentOrder.is_paid()){
                            for (var k = 0; k < order.paymentlines.models.length; k++) {
                                if(order.paymentlines.models[k].payment_method.is_cash_count){
                                    var cash_checked = true;
                                }
                            }

                            for (var l = 0; l < order.paymentlines.models.length; l++) {
                                if(order.paymentlines.models[l].payment_method.is_bank_payment){
                                    var bank_payment = true;
                                }
                            }

                            if(bank_payment && !order.to_invoice){
                                await this.showPopup('ErrorPopup', {
                                    title : this.env._t("Bank Payment"),
                                    body  : this.env._t("You are not allowed to validate this order"),
                                });
                                return;
                            }
                            else if (bank_payment && order.to_invoice){
                                    await this.validateOrder();
                            }
                            else{
                                if (this.env.pos.config.max_amount == 0){
                                await this.validateOrder();
                                this.rpc = this.env.pos.get('rpc');
                                if(order.to_invoice){
                                    if(order.get_client()){
                                        if(this.env.pos.config.fiscal_device_id){
                                            if(order.to_invoice){
                                                var invoice_number = '';
                                                const invoice = await this.rpc({
                                                        model: 'pos.order',
                                                        method: 'get_invoice_number',
                                                        args: [1, order.name],
                                                });
                                                if(invoice){
                                                    invoice_number = invoice
                                                }
                                            }
                                            var invoice_line = '\r\n' + _.str.sprintf('inp num=%s, TERM=TSFATS', invoice_number);
                                            for (var i = 0; i < this.env.pos.fiscal_devices.length; i++) {
                                                if(this.env.pos.fiscal_devices[i].id == this.env.pos.config.fiscal_device_id[0]){
                                                    var fiscal_device = this.env.pos.fiscal_devices[i];
                                                }
                                            }
                                            var mid = ''
                                            for (var j = 0; j < order.orderlines.models.length; j++) {
                                                var rep =1;
                                                if(order.orderlines.models[j].product.taxes_id[0]){
                                                    var tax = order.orderlines.models[j].product.taxes_id[0];
                                                    if(tax==fiscal_device.vat1[0]){
                                                        rep = 1
                                                    }
                                                    else if(tax==fiscal_device.vat2[0]){
                                                        rep = 2
                                                    }
                                                    else if(tax==fiscal_device.vat3[0]){
                                                        rep = 3
                                                    }
                                                    else if(tax==fiscal_device.vat4[0]){
                                                        rep = 4
                                                    }
                                                    else if(tax==fiscal_device.vat5[0]){
                                                        rep = 5
                                                    }
                                                }

                                                var qty = order.orderlines.models[j].quantity;
                                                var unit_price = order.orderlines.models[j].get_unit_price();
                                                if(order.orderlines.models[j].product.taxes_id[0]){
                                                    for (var m = 0; m < this.env.pos.product_taxes.length; m++) {
                                                        if(this.env.pos.product_taxes[m].id==order.orderlines.models[j].product.taxes_id[0]){
                                                            if(this.env.pos.product_taxes[m].price_include){
                                                                var unit_price_tax = unit_price
                                                            }
                                                            else{
                                                                var tax_per = (this.env.pos.product_taxes[m].amount)/100
                                                                var price_tax = tax_per * unit_price
                                                                var unit_price_tax = unit_price + price_tax
                                                            }
                                                        }

                                                    }
                                                    var price = this.env.pos.format_currency_no_symbol(unit_price_tax);
                                                }
                                                else{
                                                    var price = this.env.pos.format_currency_no_symbol(unit_price);
                                                }
                                                var str_price = price.replace(/\,/g,"");
                                                var floatValue_price = +(str_price);
                                                var name = order.orderlines.models[j].product.display_name.slice(0,20);
                                                var orderline = order.orderlines.models[j].get_price_with_tax();
                                                var dynamic_fiscal_device_prd_dynamic = _.str.sprintf(fiscal_device.prd_dynamic, rep, qty, floatValue_price, name);
                                                dynamic_fiscal_device_prd_dynamic += '\r\n'
                                                if(order.orderlines.models[j].discount){
                                                    var prezzo_line = _.str.sprintf('PERCA ALIQ= %.1f', order.orderlines.models[j].discount);
                                                    dynamic_fiscal_device_prd_dynamic += prezzo_line + '\r\n';
                                                }
                                                mid = mid + dynamic_fiscal_device_prd_dynamic
                                            }
                                            var change = order.get_total_paid()


                                            if(change > 0){
                                                change = this.env.pos.format_currency_no_symbol(change);
                                                var str_change = change.replace(/\,/g,"");
                                                var floatValue_change = +(str_change);
                                                var change_line = _.str.sprintf('IMP=%f', floatValue_change);
                                                change_line=change_line+";"
                                                var lines = fiscal_device.footer.split("\n");
                                                for (var k = 0; k < lines.length; k++) {

                                                    var n = lines[k].includes("CHIU");
                                                    if(n){
                                                        lines[k] = lines[k] + ', ' + change_line
                                                    }
                                                }
                                                var rest = lines.join("\r\n");
                                                var imp_footer = rest
                                                if(this.env.pos.config.receipt_footer){
                                                    var footer = _.str.sprintf(imp_footer, this.env.pos.config.receipt_footer);
                                                }
                                                else{
                                                    var footer = imp_footer
                                                }
                                            }
                                            else{
                                                if(this.env.pos.config.receipt_footer){
                                                    var footer = _.str.sprintf(fiscal_device.footer, this.env.pos.config.receipt_footer);
                                                }
                                                else{
                                                    var footer = fiscal_device.footer
                                                }
                                            }
                                            var header_new = fiscal_device.header.split("\n");
                                            var headers = "";

                                             for (var k = 0; k < header_new.length; k++) {

                                                    headers = headers + (header_new[k] + '\r\n');

                                                }
                                            var footers_new = footer.split("\n");
                                            var footers_2 = "";

                                             for (var k = 0; k < footers_new.length; k++) {

                                                    footers_2 = footers_2 + (footers_new[k] + '\r\n');

                                                }


                                            if(order.to_invoice){
                                                var content = headers + invoice_line +'\r\n'+'\r\n'+ mid +'\r\n'+footers_2
                                            }
                                            else{
                                                var content = headers +'\r\n'+mid +'\r\n'+footers_2
                                            }
                                            var element = document.createElement('a');
                                            var filename = fiscal_device.file_name + ".txt";
                                            element.setAttribute('href', 'data:text/plain;charset=utf-8,' + encodeURIComponent(content));
                                            element.setAttribute('download', filename);
                                            element.style.display = 'none';
                                            document.body.appendChild(element);
                                            element.click();
                                            document.body.removeChild(element);
                                        }
                                        else{
                                                await this.showPopup('ErrorPopup', {
                                                title : this.env._t("No Fiscal Device is Selected"),
                                                body  : this.env._t("No Fiscal Device is Selected. Make sure it is given in the pos configuration"),
                                            });
                                            return;
                                        }

                                    }

                                }
                                else{
                                    if(this.env.pos.config.fiscal_device_id){
                                            if(order.to_invoice){
                                                var invoice_number = '';
                                                const invoice = await this.rpc({
                                                        model: 'pos.order',
                                                        method: 'get_invoice_number',
                                                        args: [1, order.name],
                                                });
                                                if(invoice){
                                                    invoice_number = invoice
                                                }
                                            }
                                            var invoice_line = '\r\n' + _.str.sprintf('inp num=%s, TERM=TSFATS', invoice_number);
                                            for (var i = 0; i < this.env.pos.fiscal_devices.length; i++) {
                                                if(this.env.pos.fiscal_devices[i].id == this.env.pos.config.fiscal_device_id[0]){
                                                    var fiscal_device = this.env.pos.fiscal_devices[i];
                                                }
                                            }
                                            var mid = ''
                                            for (var j = 0; j < order.orderlines.models.length; j++) {
                                                var rep =1;
                                                if(order.orderlines.models[j].product.taxes_id[0]){
                                                    var tax = order.orderlines.models[j].product.taxes_id[0];
                                                    if(tax==fiscal_device.vat1[0]){
                                                        rep = 1
                                                    }
                                                    else if(tax==fiscal_device.vat2[0]){
                                                        rep = 2
                                                    }
                                                    else if(tax==fiscal_device.vat3[0]){
                                                        rep = 3
                                                    }
                                                    else if(tax==fiscal_device.vat4[0]){
                                                        rep = 4
                                                    }
                                                    else if(tax==fiscal_device.vat5[0]){
                                                        rep = 5
                                                    }
                                                }

                                                var qty = order.orderlines.models[j].quantity;
                                                var unit_price = order.orderlines.models[j].get_unit_price();
                                                if(order.orderlines.models[j].product.taxes_id[0]){
                                                    for (var m = 0; m < this.env.pos.product_taxes.length; m++) {
                                                        if(this.env.pos.product_taxes[m].id==order.orderlines.models[j].product.taxes_id[0]){
                                                            if(this.env.pos.product_taxes[m].price_include){
                                                                var unit_price_tax = unit_price
                                                            }
                                                            else{
                                                                var tax_per = (this.env.pos.product_taxes[m].amount)/100
                                                                var price_tax = tax_per * unit_price
                                                                var unit_price_tax = unit_price + price_tax
                                                            }
                                                        }

                                                    }
                                                    var price = this.env.pos.format_currency_no_symbol(unit_price_tax);
                                                }
                                                else{
                                                    var price = this.env.pos.format_currency_no_symbol(unit_price);
                                                }
                                                var str_price = price.replace(/\,/g,"");
                                                var floatValue_price = +(str_price);
                                                var name = order.orderlines.models[j].product.display_name.slice(0,20);
                                                var orderline = order.orderlines.models[j].get_price_with_tax();
                                                var dynamic_fiscal_device_prd_dynamic = _.str.sprintf(fiscal_device.prd_dynamic, rep, qty, floatValue_price, name);
                                                dynamic_fiscal_device_prd_dynamic += '\n'
                                                if(order.orderlines.models[j].discount){
                                                    var prezzo_line = _.str.sprintf('PERCA ALIQ= %.1f', order.orderlines.models[j].discount);

                                                    dynamic_fiscal_device_prd_dynamic += prezzo_line + '\r\n';
                                                }
                                                mid = mid + dynamic_fiscal_device_prd_dynamic
                                            }
                                            var change = order.get_total_paid()


                                            if(change > 0){
                                                change = this.env.pos.format_currency_no_symbol(change);
                                                var str_change = change.replace(/\,/g,"");
                                                var floatValue_change = +(str_change);
                                                var change_line = _.str.sprintf('IMP=%f', floatValue_change);
                                                change_line=change_line+";"
                                                var lines = fiscal_device.footer.split("\n");
                                                for (var k = 0; k < lines.length; k++) {

                                                    var n = lines[k].includes("CHIU");
                                                    if(n){
                                                        lines[k] = lines[k] + ', ' + change_line
                                                    }
                                                }
                                                var rest = lines.join("\n");
                                                var imp_footer = rest
                                                if(this.env.pos.config.receipt_footer){
                                                    var footer = _.str.sprintf(imp_footer, this.env.pos.config.receipt_footer);
                                                }
                                                else{
                                                    var footer = imp_footer
                                                }
                                            }
                                            else{
                                                if(this.env.pos.config.receipt_footer){
                                                    var footer = _.str.sprintf(fiscal_device.footer, this.env.pos.config.receipt_footer);
                                                }
                                                else{
                                                    var footer = fiscal_device.footer
                                                }
                                            }
                                            var header_new = fiscal_device.header.split("\n");
                                            var headers = "";

                                             for (var k = 0; k < header_new.length; k++) {

                                                    headers = headers + (header_new[k] + '\r\n');

                                                }
                                            var footers_new = footer.split("\n");
                                            var footers_2 = "";

                                             for (var k = 0; k < footers_new.length; k++) {

                                                    footers_2 = footers_2 + (footers_new[k] + '\r\n');

                                                }



                                            if(order.to_invoice){
                                                var content = headers + invoice_line +'\r\n'+'\r\n'+ mid +'\r\n'+footers_2
                                            }
                                            else{
                                                var content = headers +'\r\n'+mid +'\r\n'+footers_2
                                            }
                                            var element = document.createElement('a');
                                            var filename = fiscal_device.file_name + ".txt";
                                            element.setAttribute('href', 'data:text/plain;charset=utf-8,' + encodeURIComponent(content));
                                            element.setAttribute('download', filename);
                                            element.style.display = 'none';
                                            document.body.appendChild(element);
                                            element.click();
                                            document.body.removeChild(element);
                                        }
                                    else{
                                            await this.showPopup('ErrorPopup', {
                                            title : this.env._t("No Fiscal Device is Selected"),
                                            body  : this.env._t("No Fiscal Device is Selected. Make sure it is given in the pos configuration"),
                                        });
                                        return;
                                    }

                                }
                            }
                                else if (order.get_total_with_tax() <= this.env.pos.config.max_amount)  {
                                await this.validateOrder();
                                this.rpc = this.env.pos.get('rpc');
                                if(order.to_invoice){
                                    if(order.get_client()){
                                        if(this.env.pos.config.fiscal_device_id){
                                            if(order.to_invoice){
                                                var invoice_number = '';
                                                const invoice = await this.rpc({
                                                        model: 'pos.order',
                                                        method: 'get_invoice_number',
                                                        args: [1, order.name],
                                                });
                                                if(invoice){
                                                    invoice_number = invoice
                                                }
                                            }
                                            var invoice_line = '\r\n' + _.str.sprintf('inp num=%s, TERM=TSFATS', invoice_number);
                                            for (var i = 0; i < this.env.pos.fiscal_devices.length; i++) {
                                                if(this.env.pos.fiscal_devices[i].id == this.env.pos.config.fiscal_device_id[0]){
                                                    var fiscal_device = this.env.pos.fiscal_devices[i];
                                                }
                                            }
                                            var mid = ''
                                            for (var j = 0; j < order.orderlines.models.length; j++) {
                                                var rep =1;
                                                if(order.orderlines.models[j].product.taxes_id[0]){
                                                    var tax = order.orderlines.models[j].product.taxes_id[0];
                                                    if(tax==fiscal_device.vat1[0]){
                                                        rep = 1
                                                    }
                                                    else if(tax==fiscal_device.vat2[0]){
                                                        rep = 2
                                                    }
                                                    else if(tax==fiscal_device.vat3[0]){
                                                        rep = 3
                                                    }
                                                    else if(tax==fiscal_device.vat4[0]){
                                                        rep = 4
                                                    }
                                                    else if(tax==fiscal_device.vat5[0]){
                                                        rep = 5
                                                    }
                                                }

                                                var qty = order.orderlines.models[j].quantity;
                                                var unit_price = order.orderlines.models[j].get_unit_price();
                                                if(order.orderlines.models[j].product.taxes_id[0]){
                                                    for (var m = 0; m < this.env.pos.product_taxes.length; m++) {
                                                        if(this.env.pos.product_taxes[m].id==order.orderlines.models[j].product.taxes_id[0]){
                                                            if(this.env.pos.product_taxes[m].price_include){
                                                                var unit_price_tax = unit_price
                                                            }
                                                            else{
                                                                var tax_per = (this.env.pos.product_taxes[m].amount)/100
                                                                var price_tax = tax_per * unit_price
                                                                var unit_price_tax = unit_price + price_tax
                                                            }
                                                        }

                                                    }
                                                    var price = this.env.pos.format_currency_no_symbol(unit_price_tax);
                                                }
                                                else{
                                                    var price = this.env.pos.format_currency_no_symbol(unit_price);
                                                }
                                                var str_price = price.replace(/\,/g,"");
                                                var floatValue_price = +(str_price);
                                                var name = order.orderlines.models[j].product.display_name.slice(0,20);
                                                var orderline = order.orderlines.models[j].get_price_with_tax();
                                                var dynamic_fiscal_device_prd_dynamic = _.str.sprintf(fiscal_device.prd_dynamic, rep, qty, floatValue_price, name);
                                                dynamic_fiscal_device_prd_dynamic += '\r\n'
                                                if(order.orderlines.models[j].discount){
                                                   var prezzo_line = _.str.sprintf('PERCA ALIQ= %.1f', order.orderlines.models[j].discount);

                                                    dynamic_fiscal_device_prd_dynamic += prezzo_line + '\r\n';
                                                }
                                                mid = mid + dynamic_fiscal_device_prd_dynamic
                                            }
                                            var change = order.get_total_paid()



                                            if(change > 0){
                                                change = this.env.pos.format_currency_no_symbol(change);
                                                var str_change = change.replace(/\,/g,"");
                                                var floatValue_change = +(str_change);
                                                var change_line = _.str.sprintf('IMP=%f', floatValue_change);
                                                change_line=change_line+";"
                                                var lines = fiscal_device.footer.split("\n");
                                                for (var k = 0; k < lines.length; k++) {

                                                    var n = lines[k].includes("CHIU");
                                                    if(n){
                                                        lines[k] = lines[k] + ', ' + change_line
                                                    }
                                                }
                                                var rest = lines.join("\r\n");
                                                var imp_footer = rest
                                                if(this.env.pos.config.receipt_footer){
                                                    var footer = _.str.sprintf(imp_footer, this.env.pos.config.receipt_footer);
                                                }
                                                else{
                                                    var footer = imp_footer
                                                }
                                            }
                                            else{
                                                if(this.env.pos.config.receipt_footer){
                                                    var footer = _.str.sprintf(fiscal_device.footer, this.env.pos.config.receipt_footer);
                                                }
                                                else{
                                                    var footer = fiscal_device.footer
                                                }
                                            }

                                            var footers_new = footer.split("\n");
                                            var footers_2 = "";

                                             for (var k = 0; k < footers_new.length; k++) {

                                                    footers_2 = footers_2 + (footers_new[k] + '\r\n');

                                                }


                                            var header_new = fiscal_device.header.split("\n");
                                            var headers = "";

                                             for (var k = 0; k < header_new.length; k++) {

                                                    headers = headers + (header_new[k] + '\r\n');

                                                }

                                            if(order.to_invoice){
                                                var content = headers + invoice_line +'\r\n'+'\r\n'+ mid +'\r\n'+footers_2
                                            }
                                            else{
                                                var content = headers +'\r\n'+mid +'\r\n'+footers_2
                                            }
                                            var element = document.createElement('a');
                                            var filename = fiscal_device.file_name + ".txt";
                                            element.setAttribute('href', 'data:text/plain;charset=utf-8,' + encodeURIComponent(content));
                                            element.setAttribute('download', filename);
                                            element.style.display = 'none';
                                            document.body.appendChild(element);
                                            element.click();
                                            document.body.removeChild(element);
                                        }
                                        else{
                                                await this.showPopup('ErrorPopup', {
                                                title : this.env._t("No Fiscal Device is Selected"),
                                                body  : this.env._t("No Fiscal Device is Selected. Make sure it is given in the pos configuration"),
                                            });
                                            return;
                                        }

                                    }

                                }
                                else{
                                    if(this.env.pos.config.fiscal_device_id){
                                            if(order.to_invoice){
                                                var invoice_number = '';
                                                const invoice = await this.rpc({
                                                        model: 'pos.order',
                                                        method: 'get_invoice_number',
                                                        args: [1, order.name],
                                                });
                                                if(invoice){
                                                    invoice_number = invoice
                                                }
                                            }
                                            var invoice_line = '\r\n' + _.str.sprintf('inp num=%s, TERM=TSFATS', invoice_number);
                                            for (var i = 0; i < this.env.pos.fiscal_devices.length; i++) {
                                                if(this.env.pos.fiscal_devices[i].id == this.env.pos.config.fiscal_device_id[0]){
                                                    var fiscal_device = this.env.pos.fiscal_devices[i];
                                                }
                                            }
                                            var mid = ''
                                            for (var j = 0; j < order.orderlines.models.length; j++) {
                                                var rep =1;
                                                if(order.orderlines.models[j].product.taxes_id[0]){
                                                    var tax = order.orderlines.models[j].product.taxes_id[0];
                                                    if(tax==fiscal_device.vat1[0]){
                                                        rep = 1
                                                    }
                                                    else if(tax==fiscal_device.vat2[0]){
                                                        rep = 2
                                                    }
                                                    else if(tax==fiscal_device.vat3[0]){
                                                        rep = 3
                                                    }
                                                    else if(tax==fiscal_device.vat4[0]){
                                                        rep = 4
                                                    }
                                                    else if(tax==fiscal_device.vat5[0]){
                                                        rep = 5
                                                    }
                                                }

                                                var qty = order.orderlines.models[j].quantity;
                                                var unit_price = order.orderlines.models[j].get_unit_price();
                                                if(order.orderlines.models[j].product.taxes_id[0]){
                                                    for (var m = 0; m < this.env.pos.product_taxes.length; m++) {
                                                        if(this.env.pos.product_taxes[m].id==order.orderlines.models[j].product.taxes_id[0]){
                                                            if(this.env.pos.product_taxes[m].price_include){
                                                                var unit_price_tax = unit_price
                                                            }
                                                            else{
                                                                var tax_per = (this.env.pos.product_taxes[m].amount)/100
                                                                var price_tax = tax_per * unit_price
                                                                var unit_price_tax = unit_price + price_tax
                                                            }
                                                        }

                                                    }
                                                    var price = this.env.pos.format_currency_no_symbol(unit_price_tax);
                                                }
                                                else{
                                                    var price = this.env.pos.format_currency_no_symbol(unit_price);
                                                }
                                                var str_price = price.replace(/\,/g,"");
                                                var floatValue_price = +(str_price);
                                                var name = order.orderlines.models[j].product.display_name.slice(0,20);
                                                var orderline = order.orderlines.models[j].get_price_with_tax();
                                                var dynamic_fiscal_device_prd_dynamic = _.str.sprintf(fiscal_device.prd_dynamic, rep, qty, floatValue_price, name);
                                                dynamic_fiscal_device_prd_dynamic += '\r\n'
                                                if(order.orderlines.models[j].discount){
                                                    var prezzo_line = _.str.sprintf('PERCA ALIQ= %.1f', order.orderlines.models[j].discount);

                                                    dynamic_fiscal_device_prd_dynamic += prezzo_line + '\r\n';
                                                }
                                                mid = mid + dynamic_fiscal_device_prd_dynamic
                                            }
                                            var change = order.get_total_paid()


                                            if(change > 0){
                                                change = this.env.pos.format_currency_no_symbol(change);
                                                var str_change = change.replace(/\,/g,"");
                                                var floatValue_change = +(str_change);
                                                var change_line = _.str.sprintf('IMP=%f', floatValue_change);
                                                change_line=change_line+";"
                                                var lines = fiscal_device.footer.split("\n");
                                                for (var k = 0; k < lines.length; k++) {

                                                    var n = lines[k].includes("CHIU");
                                                    if(n){
                                                        lines[k] = lines[k] + ', ' + change_line
                                                    }
                                                }
                                                var rest = lines.join("\r\n");
                                                var imp_footer = rest
                                                if(this.env.pos.config.receipt_footer){
                                                    var footer = _.str.sprintf(imp_footer, this.env.pos.config.receipt_footer);
                                                }
                                                else{
                                                    var footer = imp_footer
                                                }
                                            }
                                            else{
                                                if(this.env.pos.config.receipt_footer){
                                                    var footer = _.str.sprintf(fiscal_device.footer, this.env.pos.config.receipt_footer);
                                                }
                                                else{
                                                    var footer = fiscal_device.footer
                                                }
                                            }
                                            var header_new = fiscal_device.header.split("\n");
                                            var headers = "";

                                             for (var k = 0; k < header_new.length; k++) {

                                                    headers = headers + (header_new[k] + '\r\n');

                                                }

                                            var footers_new = footer.split("\n");
                                            var footers_2 = "";

                                             for (var k = 0; k < footers_new.length; k++) {

                                                    footers_2 = footers_2 + (footers_new[k] + '\r\n');

                                                }




                                            if(order.to_invoice){
                                                var content = headers + invoice_line +'\r\n'+'\r\n'+ mid +'\r\n'+footers_2
                                            }
                                            else{
                                                var content = headers +'\r\n'+mid +'\r\n'+footers_2
                                            }
                                            var element = document.createElement('a');
                                            var filename = fiscal_device.file_name + ".txt";
                                            element.setAttribute('href', 'data:text/plain;charset=utf-8,' + encodeURIComponent(content));
                                            element.setAttribute('download', filename);
                                            element.style.display = 'none';
                                            document.body.appendChild(element);
                                            element.click();
                                            document.body.removeChild(element);
                                        }
                                    else{
                                            await this.showPopup('ErrorPopup', {
                                            title : this.env._t("No Fiscal Device is Selected"),
                                            body  : this.env._t("No Fiscal Device is Selected. Make sure it is given in the pos configuration"),
                                        });
                                        return;
                                    }

                                }

                            }
                                else{
                                    if(cash_checked){
                                        await this.showPopup('ErrorPopup', {
                                            title : this.env._t("Maximum Amount Exceeded"),
                                            body  : this.env._t("You are not allowed to validate this order"),
                                        });
                                        return;
                                    }
                                    else{
                                        if(bank_payment && !order.to_invoice){
                                            await this.showPopup('ErrorPopup', {
                                                title : this.env._t("Maximum Amount Exceeded"),
                                                body  : this.env._t("You are not allowed to validate this order"),
                                            });
                                            return;
                                        }
                                        else{
                                            await this.validateOrder();
                                        }

                                    }
                            }
                            }

                        }
                }
                else if(order.get_total_with_tax() > this.env.pos.config.mxm_amount_invoice){
                    if(!order.to_invoice){
                        await this.showPopup('ErrorPopup', {
                             title : this.env._t("Maximum Amount Exceeded"),
                             body  : this.env._t("You are not allowed to validate this order"),
                         });
                         return;

                    }
                    else{

                        if(this.currentOrder.is_paid()){
                            for (var k = 0; k < order.paymentlines.models.length; k++) {
                                if(order.paymentlines.models[k].payment_method.is_cash_count){
                                    var cash_checked = true;
                                }
                            }

                            for (var l = 0; l < order.paymentlines.models.length; l++) {
                                if(order.paymentlines.models[l].payment_method.is_bank_payment){
                                    var bank_payment = true;
                                }
                            }

                            if(bank_payment && !order.to_invoice){
                                await this.showPopup('ErrorPopup', {
                                    title : this.env._t("Bank Payment"),
                                    body  : this.env._t("You are not allowed to validate this order"),
                                });
                                return;
                            }
                            else if (bank_payment && order.to_invoice){
                                    await this.validateOrder();
                            }
                            else{
                                if (this.env.pos.config.max_amount == 0){
                                await this.validateOrder();
                                this.rpc = this.env.pos.get('rpc');
                                if(order.to_invoice){
                                    if(order.get_client()){
                                        if(this.env.pos.config.fiscal_device_id){
                                            if(order.to_invoice){
                                                var invoice_number = '';
                                                const invoice = await this.rpc({
                                                        model: 'pos.order',
                                                        method: 'get_invoice_number',
                                                        args: [1, order.name],
                                                });
                                                if(invoice){
                                                    invoice_number = invoice
                                                }
                                            }
                                            var invoice_line = '\r\n' + _.str.sprintf('inp num=%s, TERM=TSFATS', invoice_number);
                                            for (var i = 0; i < this.env.pos.fiscal_devices.length; i++) {
                                                if(this.env.pos.fiscal_devices[i].id == this.env.pos.config.fiscal_device_id[0]){
                                                    var fiscal_device = this.env.pos.fiscal_devices[i];
                                                }
                                            }
                                            var mid = ''
                                            for (var j = 0; j < order.orderlines.models.length; j++) {
                                                var rep =1;
                                                if(order.orderlines.models[j].product.taxes_id[0]){
                                                    var tax = order.orderlines.models[j].product.taxes_id[0];
                                                    if(tax==fiscal_device.vat1[0]){
                                                        rep = 1
                                                    }
                                                    else if(tax==fiscal_device.vat2[0]){
                                                        rep = 2
                                                    }
                                                    else if(tax==fiscal_device.vat3[0]){
                                                        rep = 3
                                                    }
                                                    else if(tax==fiscal_device.vat4[0]){
                                                        rep = 4
                                                    }
                                                    else if(tax==fiscal_device.vat5[0]){
                                                        rep = 5
                                                    }
                                                }

                                                var qty = order.orderlines.models[j].quantity;
                                                var unit_price = order.orderlines.models[j].get_unit_price();
                                                if(order.orderlines.models[j].product.taxes_id[0]){
                                                    for (var m = 0; m < this.env.pos.product_taxes.length; m++) {
                                                        if(this.env.pos.product_taxes[m].id==order.orderlines.models[j].product.taxes_id[0]){
                                                            if(this.env.pos.product_taxes[m].price_include){
                                                                var unit_price_tax = unit_price
                                                            }
                                                            else{
                                                                var tax_per = (this.env.pos.product_taxes[m].amount)/100
                                                                var price_tax = tax_per * unit_price
                                                                var unit_price_tax = unit_price + price_tax
                                                            }
                                                        }

                                                    }
                                                    var price = this.env.pos.format_currency_no_symbol(unit_price_tax);
                                                }
                                                else{
                                                    var price = this.env.pos.format_currency_no_symbol(unit_price);
                                                }
                                                var str_price = price.replace(/\,/g,"");
                                                var floatValue_price = +(str_price);
                                                var name = order.orderlines.models[j].product.display_name.slice(0,20);
                                                var orderline = order.orderlines.models[j].get_price_with_tax();
                                                var dynamic_fiscal_device_prd_dynamic = _.str.sprintf(fiscal_device.prd_dynamic, rep, qty, floatValue_price, name);
                                                dynamic_fiscal_device_prd_dynamic += '\r\n'
                                                if(order.orderlines.models[j].discount){
                                                    var prezzo_line = _.str.sprintf('PERCA ALIQ= %.1f', order.orderlines.models[j].discount);

                                                    dynamic_fiscal_device_prd_dynamic += prezzo_line + '\r\n';
                                                }
                                                mid = mid + dynamic_fiscal_device_prd_dynamic
                                            }
                                            var change = order.get_total_paid()


                                            if(change > 0){
                                                change = this.env.pos.format_currency_no_symbol(change);
                                                var str_change = change.replace(/\,/g,"");
                                                var floatValue_change = +(str_change);
                                                var change_line = _.str.sprintf('IMP=%f', floatValue_change);
                                                change_line=change_line+";"
                                                var lines = fiscal_device.footer.split("\n");
                                                for (var k = 0; k < lines.length; k++) {

                                                    var n = lines[k].includes("CHIU");
                                                    if(n){
                                                        lines[k] = lines[k] + ', ' + change_line
                                                    }
                                                }
                                                var rest = lines.join("\r\n");
                                                var imp_footer = rest
                                                if(this.env.pos.config.receipt_footer){
                                                    var footer = _.str.sprintf(imp_footer, this.env.pos.config.receipt_footer);
                                                }
                                                else{
                                                    var footer = imp_footer
                                                }
                                            }
                                            else{
                                                if(this.env.pos.config.receipt_footer){
                                                    var footer = _.str.sprintf(fiscal_device.footer, this.env.pos.config.receipt_footer);
                                                }
                                                else{
                                                    var footer = fiscal_device.footer
                                                }
                                            }
                                            var header_new = fiscal_device.header.split("\n");
                                            var headers = "";

                                             for (var k = 0; k < header_new.length; k++) {

                                                    headers = headers + (header_new[k] + '\r\n');

                                                }
                                            var footers_new = footer.split("\n");
                                            var footers_2 = "";

                                             for (var k = 0; k < footers_new.length; k++) {

                                                    footers_2 = footers_2 + (footers_new[k] + '\r\n');

                                                }




                                            if(order.to_invoice){
                                                var content = headers + invoice_line +'\r\n'+ '\r\n'+mid +'\r\n'+footers_2
                                            }
                                            else{
                                                var content = headers +'\r\n'+mid +'\r\n'+footers_2
                                            }
                                            var element = document.createElement('a');
                                            var filename = fiscal_device.file_name + ".txt";
                                            element.setAttribute('href', 'data:text/plain;charset=utf-8,' + encodeURIComponent(content));
                                            element.setAttribute('download', filename);
                                            element.style.display = 'none';
                                            document.body.appendChild(element);
                                            element.click();
                                            document.body.removeChild(element);
                                        }
                                        else{
                                                await this.showPopup('ErrorPopup', {
                                                title : this.env._t("No Fiscal Device is Selected"),
                                                body  : this.env._t("No Fiscal Device is Selected. Make sure it is given in the pos configuration"),
                                            });
                                            return;
                                        }

                                    }

                                }
                                else{
                                    if(this.env.pos.config.fiscal_device_id){
                                            if(order.to_invoice){
                                                var invoice_number = '';
                                                const invoice = await this.rpc({
                                                        model: 'pos.order',
                                                        method: 'get_invoice_number',
                                                        args: [1, order.name],
                                                });
                                                if(invoice){
                                                    invoice_number = invoice
                                                }
                                            }
                                            var invoice_line = '\r\n' + _.str.sprintf('inp num=%s, TERM=TSFATS', invoice_number);
                                            for (var i = 0; i < this.env.pos.fiscal_devices.length; i++) {
                                                if(this.env.pos.fiscal_devices[i].id == this.env.pos.config.fiscal_device_id[0]){
                                                    var fiscal_device = this.env.pos.fiscal_devices[i];
                                                }
                                            }
                                            var mid = ''
                                            for (var j = 0; j < order.orderlines.models.length; j++) {
                                                var rep =1;
                                                if(order.orderlines.models[j].product.taxes_id[0]){
                                                    var tax = order.orderlines.models[j].product.taxes_id[0];
                                                    if(tax==fiscal_device.vat1[0]){
                                                        rep = 1
                                                    }
                                                    else if(tax==fiscal_device.vat2[0]){
                                                        rep = 2
                                                    }
                                                    else if(tax==fiscal_device.vat3[0]){
                                                        rep = 3
                                                    }
                                                    else if(tax==fiscal_device.vat4[0]){
                                                        rep = 4
                                                    }
                                                    else if(tax==fiscal_device.vat5[0]){
                                                        rep = 5
                                                    }
                                                }

                                                var qty = order.orderlines.models[j].quantity;
                                                var unit_price = order.orderlines.models[j].get_unit_price();
                                                if(order.orderlines.models[j].product.taxes_id[0]){
                                                    for (var m = 0; m < this.env.pos.product_taxes.length; m++) {
                                                        if(this.env.pos.product_taxes[m].id==order.orderlines.models[j].product.taxes_id[0]){
                                                            if(this.env.pos.product_taxes[m].price_include){
                                                                var unit_price_tax = unit_price
                                                            }
                                                            else{
                                                                var tax_per = (this.env.pos.product_taxes[m].amount)/100
                                                                var price_tax = tax_per * unit_price
                                                                var unit_price_tax = unit_price + price_tax
                                                            }
                                                        }

                                                    }
                                                    var price = this.env.pos.format_currency_no_symbol(unit_price_tax);
                                                }
                                                else{
                                                    var price = this.env.pos.format_currency_no_symbol(unit_price);
                                                }
                                                var str_price = price.replace(/\,/g,"");
                                                var floatValue_price = +(str_price);
                                                var name = order.orderlines.models[j].product.display_name.slice(0,20);
                                                var orderline = order.orderlines.models[j].get_price_with_tax();
                                                var dynamic_fiscal_device_prd_dynamic = _.str.sprintf(fiscal_device.prd_dynamic, rep, qty, floatValue_price, name);
                                                dynamic_fiscal_device_prd_dynamic += '\r\n'
                                                if(order.orderlines.models[j].discount){
                                                    var prezzo_line = _.str.sprintf('PERCA ALIQ= %.1f', order.orderlines.models[j].discount);

                                                    dynamic_fiscal_device_prd_dynamic += prezzo_line + '\r\n';
                                                }
                                                mid = mid + dynamic_fiscal_device_prd_dynamic
                                            }
                                            var change = order.get_total_paid()


                                            if(change > 0){
                                                change = this.env.pos.format_currency_no_symbol(change);
                                                var str_change = change.replace(/\,/g,"");
                                                var floatValue_change = +(str_change);
                                                var change_line = _.str.sprintf('IMP=%f', floatValue_change);
                                                change_line=change_line+";"
                                                var lines = fiscal_device.footer.split("\n");
                                                for (var k = 0; k < lines.length; k++) {

                                                    var n = lines[k].includes("CHIU");
                                                    if(n){
                                                        lines[k] = lines[k] + ', ' + change_line
                                                    }
                                                }
                                                var rest = lines.join("\r\n");
                                                var imp_footer = rest
                                                if(this.env.pos.config.receipt_footer){
                                                    var footer = _.str.sprintf(imp_footer, this.env.pos.config.receipt_footer);
                                                }
                                                else{
                                                    var footer = imp_footer
                                                }
                                            }
                                            else{
                                                if(this.env.pos.config.receipt_footer){
                                                    var footer = _.str.sprintf(fiscal_device.footer, this.env.pos.config.receipt_footer);
                                                }
                                                else{
                                                    var footer = fiscal_device.footer
                                                }
                                            }
                                            var header_new = fiscal_device.header.split("\n");
                                            var headers = "";

                                             for (var k = 0; k < header_new.length; k++) {

                                                    headers = headers + (header_new[k] + '\r\n');

                                                }
                                            var footers_new = footer.split("\n");
                                            var footers_2 = "";

                                             for (var k = 0; k < footers_new.length; k++) {

                                                    footers_2 = footers_2 + (footers_new[k] + '\r\n');

                                                }




                                            if(order.to_invoice){
                                                var content = headers + invoice_line +'\r\n'+'\r\n'+ mid +'\r\n'+footers_2
                                            }
                                            else{
                                                var content = headers +'\r\n'+mid +'\r\n'+footers_2
                                            }
                                            var element = document.createElement('a');
                                            var filename = fiscal_device.file_name + ".txt";
                                            element.setAttribute('href', 'data:text/plain;charset=utf-8,' + encodeURIComponent(content));
                                            element.setAttribute('download', filename);
                                            element.style.display = 'none';
                                            document.body.appendChild(element);
                                            element.click();
                                            document.body.removeChild(element);
                                        }
                                    else{
                                            await this.showPopup('ErrorPopup', {
                                            title : this.env._t("No Fiscal Device is Selected"),
                                            body  : this.env._t("No Fiscal Device is Selected. Make sure it is given in the pos configuration"),
                                        });
                                        return;
                                    }

                                }
                            }
                                else if (order.get_total_with_tax() <= this.env.pos.config.max_amount) {
                                await this.validateOrder();
                                this.rpc = this.env.pos.get('rpc');
                                if(order.to_invoice){
                                    if(order.get_client()){
                                        if(this.env.pos.config.fiscal_device_id){
                                            if(order.to_invoice){
                                                var invoice_number = '';
                                                const invoice = await this.rpc({
                                                        model: 'pos.order',
                                                        method: 'get_invoice_number',
                                                        args: [1, order.name],
                                                });
                                                if(invoice){
                                                    invoice_number = invoice
                                                }
                                            }
                                            var invoice_line = '\r\n' + _.str.sprintf('inp num=%s, TERM=TSFATS', invoice_number);
                                            for (var i = 0; i < this.env.pos.fiscal_devices.length; i++) {
                                                if(this.env.pos.fiscal_devices[i].id == this.env.pos.config.fiscal_device_id[0]){
                                                    var fiscal_device = this.env.pos.fiscal_devices[i];
                                                }
                                            }
                                            var mid = ''
                                            for (var j = 0; j < order.orderlines.models.length; j++) {
                                                var rep =1;
                                                if(order.orderlines.models[j].product.taxes_id[0]){
                                                    var tax = order.orderlines.models[j].product.taxes_id[0];
                                                    if(tax==fiscal_device.vat1[0]){
                                                        rep = 1
                                                    }
                                                    else if(tax==fiscal_device.vat2[0]){
                                                        rep = 2
                                                    }
                                                    else if(tax==fiscal_device.vat3[0]){
                                                        rep = 3
                                                    }
                                                    else if(tax==fiscal_device.vat4[0]){
                                                        rep = 4
                                                    }
                                                    else if(tax==fiscal_device.vat5[0]){
                                                        rep = 5
                                                    }
                                                }

                                                var qty = order.orderlines.models[j].quantity;
                                                var unit_price = order.orderlines.models[j].get_unit_price();
                                                if(order.orderlines.models[j].product.taxes_id[0]){
                                                    for (var m = 0; m < this.env.pos.product_taxes.length; m++) {
                                                        if(this.env.pos.product_taxes[m].id==order.orderlines.models[j].product.taxes_id[0]){
                                                            if(this.env.pos.product_taxes[m].price_include){
                                                                var unit_price_tax = unit_price
                                                            }
                                                            else{
                                                                var tax_per = (this.env.pos.product_taxes[m].amount)/100
                                                                var price_tax = tax_per * unit_price
                                                                var unit_price_tax = unit_price + price_tax
                                                            }
                                                        }

                                                    }
                                                    var price = this.env.pos.format_currency_no_symbol(unit_price_tax);
                                                }
                                                else{
                                                    var price = this.env.pos.format_currency_no_symbol(unit_price);
                                                }
                                                var str_price = price.replace(/\,/g,"");
                                                var floatValue_price = +(str_price);
                                                var name = order.orderlines.models[j].product.display_name.slice(0,20);
                                                var orderline = order.orderlines.models[j].get_price_with_tax();
                                                var dynamic_fiscal_device_prd_dynamic = _.str.sprintf(fiscal_device.prd_dynamic, rep, qty, floatValue_price, name);
                                                dynamic_fiscal_device_prd_dynamic += '\r\n'
                                                if(order.orderlines.models[j].discount){
                                                    var prezzo_line = _.str.sprintf('PERCA ALIQ= %.1f', order.orderlines.models[j].discount);

                                                    dynamic_fiscal_device_prd_dynamic += prezzo_line + '\r\n';
                                                }
                                                mid = mid + dynamic_fiscal_device_prd_dynamic
                                            }
                                            var change = order.get_total_paid()


                                            if(change > 0){
                                                change = this.env.pos.format_currency_no_symbol(change);
                                                var str_change = change.replace(/\,/g,"");
                                                var floatValue_change = +(str_change);
                                                var change_line = _.str.sprintf('IMP=%f', floatValue_change);
                                                change_line=change_line+";"
                                                var lines = fiscal_device.footer.split("\n");
                                                for (var k = 0; k < lines.length; k++) {

                                                    var n = lines[k].includes("CHIU");
                                                    if(n){
                                                        lines[k] = lines[k] + ', ' + change_line
                                                    }
                                                }
                                                var rest = lines.join("\r\n");
                                                var imp_footer = rest
                                                if(this.env.pos.config.receipt_footer){
                                                    var footer = _.str.sprintf(imp_footer, this.env.pos.config.receipt_footer);
                                                }
                                                else{
                                                    var footer = imp_footer
                                                }
                                            }
                                            else{
                                                if(this.env.pos.config.receipt_footer){
                                                    var footer = _.str.sprintf(fiscal_device.footer, this.env.pos.config.receipt_footer);
                                                }
                                                else{
                                                    var footer = fiscal_device.footer
                                                }
                                            }
                                            var footers_new = footer.split("\n");
                                            var footers_2 = "";

                                             for (var k = 0; k < footers_new.length; k++) {

                                                    footers_2 = footers_2 + (footers_new[k] + '\r\n');

                                                }


                                            var headers = "";
                                            var header_new = fiscal_device.header.split("\n");


                                            for (var k = 0; k < header_new.length; k++) {

                                                    headers = headers + (header_new[k] + '\r\n');

                                                }


                                            if(order.to_invoice){
                                                var content = headers + invoice_line +'\r\n'+'\r\n'+ mid +'\r\n'+footers_2
                                            }
                                            else{
                                                var content = headers +'\r\n'+mid +'\r\n'+footers_2
                                            }
                                            var element = document.createElement('a');
                                            var filename = fiscal_device.file_name + ".txt";
                                            element.setAttribute('href', 'data:text/plain;charset=utf-8,' + encodeURIComponent(content));
                                            element.setAttribute('download', filename);
                                            element.style.display = 'none';
                                            document.body.appendChild(element);
                                            element.click();
                                            document.body.removeChild(element);
                                        }
                                        else{
                                                await this.showPopup('ErrorPopup', {
                                                title : this.env._t("No Fiscal Device is Selected"),
                                                body  : this.env._t("No Fiscal Device is Selected. Make sure it is given in the pos configuration"),
                                            });
                                            return;
                                        }

                                    }

                                }
                                else{
                                    if(this.env.pos.config.fiscal_device_id){
                                            if(order.to_invoice){
                                                var invoice_number = '';
                                                const invoice = await this.rpc({
                                                        model: 'pos.order',
                                                        method: 'get_invoice_number',
                                                        args: [1, order.name],
                                                });
                                                if(invoice){
                                                    invoice_number = invoice
                                                }
                                            }
                                            var invoice_line = '\r\n' + _.str.sprintf('inp num=%s, TERM=TSFATS', invoice_number);
                                            for (var i = 0; i < this.env.pos.fiscal_devices.length; i++) {
                                                if(this.env.pos.fiscal_devices[i].id == this.env.pos.config.fiscal_device_id[0]){
                                                    var fiscal_device = this.env.pos.fiscal_devices[i];
                                                }
                                            }
                                            var mid = ''
                                            for (var j = 0; j < order.orderlines.models.length; j++) {
                                                var rep =1;
                                                if(order.orderlines.models[j].product.taxes_id[0]){
                                                    var tax = order.orderlines.models[j].product.taxes_id[0];
                                                    if(tax==fiscal_device.vat1[0]){
                                                        rep = 1
                                                    }
                                                    else if(tax==fiscal_device.vat2[0]){
                                                        rep = 2
                                                    }
                                                    else if(tax==fiscal_device.vat3[0]){
                                                        rep = 3
                                                    }
                                                    else if(tax==fiscal_device.vat4[0]){
                                                        rep = 4
                                                    }
                                                    else if(tax==fiscal_device.vat5[0]){
                                                        rep = 5
                                                    }
                                                }

                                                var qty = order.orderlines.models[j].quantity;
                                                var unit_price = order.orderlines.models[j].get_unit_price();
                                                if(order.orderlines.models[j].product.taxes_id[0]){
                                                    for (var m = 0; m < this.env.pos.product_taxes.length; m++) {
                                                        if(this.env.pos.product_taxes[m].id==order.orderlines.models[j].product.taxes_id[0]){
                                                            if(this.env.pos.product_taxes[m].price_include){
                                                                var unit_price_tax = unit_price
                                                            }
                                                            else{
                                                                var tax_per = (this.env.pos.product_taxes[m].amount)/100
                                                                var price_tax = tax_per * unit_price
                                                                var unit_price_tax = unit_price + price_tax
                                                            }
                                                        }

                                                    }
                                                    var price = this.env.pos.format_currency_no_symbol(unit_price_tax);
                                                }
                                                else{
                                                    var price = this.env.pos.format_currency_no_symbol(unit_price);
                                                }
                                                var str_price = price.replace(/\,/g,"");
                                                var floatValue_price = +(str_price);
                                                var name = order.orderlines.models[j].product.display_name.slice(0,20);
                                                var orderline = order.orderlines.models[j].get_price_with_tax();
                                                var dynamic_fiscal_device_prd_dynamic = _.str.sprintf(fiscal_device.prd_dynamic, rep, qty, floatValue_price, name);
                                                dynamic_fiscal_device_prd_dynamic += '\r\n'
                                                if(order.orderlines.models[j].discount){
                                                    var prezzo_line = _.str.sprintf('PERCA ALIQ= %.1f', order.orderlines.models[j].discount);

                                                    dynamic_fiscal_device_prd_dynamic += prezzo_line + '\r\n';
                                                }
                                                mid = mid + dynamic_fiscal_device_prd_dynamic
                                            }
                                            var change = order.get_total_paid()


                                            if(change > 0){
                                                change = this.env.pos.format_currency_no_symbol(change);
                                                var str_change = change.replace(/\,/g,"");
                                                var floatValue_change = +(str_change);
                                                var change_line = _.str.sprintf('IMP=%f', floatValue_change);
                                                change_line=change_line+";"
                                                var lines = fiscal_device.footer.split("\n");
                                                for (var k = 0; k < lines.length; k++) {

                                                    var n = lines[k].includes("CHIU");
                                                    if(n){
                                                        lines[k] = lines[k] + ', ' + change_line
                                                    }
                                                }
                                                var rest = lines.join("\r\n");
                                                var imp_footer = rest
                                                if(this.env.pos.config.receipt_footer){
                                                    var footer = _.str.sprintf(imp_footer, this.env.pos.config.receipt_footer);
                                                }
                                                else{
                                                    var footer = imp_footer
                                                }
                                            }
                                            else{
                                                if(this.env.pos.config.receipt_footer){
                                                    var footer = _.str.sprintf(fiscal_device.footer, this.env.pos.config.receipt_footer);
                                                }
                                                else{
                                                    var footer = fiscal_device.footer
                                                }
                                            }
                                            var headers = "";
                                            var header_new = fiscal_device.header.split("\n");


                                             for (var k = 0; k < header_new.length; k++) {

                                                    headers = headers + (header_new[k] + '\r\n');

                                                }
                                            var footers_new = footer.split("\n");
                                            var footers_2 = "";

                                             for (var k = 0; k < footers_new.length; k++) {

                                                    footers_2 = footers_2 + (footers_new[k] + '\r\n');

                                                }




                                            if(order.to_invoice){
                                                var content = headers + invoice_line +'\r\n'+ '\r\n'+mid +'\r\n'+footers_2
                                            }
                                            else{
                                                var content = headers +'\r\n'+mid +'\r\n'+footers_2
                                            }
                                            var element = document.createElement('a');
                                            var filename = fiscal_device.file_name + ".txt";
                                            element.setAttribute('href', 'data:text/plain;charset=utf-8,' + encodeURIComponent(content));
                                            element.setAttribute('download', filename);
                                            element.style.display = 'none';
                                            document.body.appendChild(element);
                                            element.click();
                                            document.body.removeChild(element);
                                        }
                                    else{
                                            await this.showPopup('ErrorPopup', {
                                            title : this.env._t("No Fiscal Device is Selected"),
                                            body  : this.env._t("No Fiscal Device is Selected. Make sure it is given in the pos configuration"),
                                        });
                                        return;
                                    }

                                }

                            }
                                else{
                                    if(cash_checked){
                                        await this.showPopup('ErrorPopup', {
                                            title : this.env._t("Maximum Amount Exceeded"),
                                            body  : this.env._t("You are not allowed to validate this order"),
                                        });
                                        return;
                                    }
                                    else{
                                        if(bank_payment && !order.to_invoice){
                                            await this.showPopup('ErrorPopup', {
                                                title : this.env._t("Maximum Amount Exceeded"),
                                                body  : this.env._t("You are not allowed to validate this order"),
                                            });
                                            return;
                                        }
                                        else{
                                            await this.validateOrder();
                                        }

                                    }
                            }
                            }


                        }

                    }

                }
                else{
                    if(this.currentOrder.is_paid()){
                            for (var k = 0; k < order.paymentlines.models.length; k++) {
                                if(order.paymentlines.models[k].payment_method.is_cash_count){
                                    var cash_checked = true;
                                }
                            }

                            for (var l = 0; l < order.paymentlines.models.length; l++) {
                                if(order.paymentlines.models[l].payment_method.is_bank_payment){
                                    var bank_payment = true;
                                }
                            }

                            if(bank_payment && !order.to_invoice){
                                await this.showPopup('ErrorPopup', {
                                    title : this.env._t("Bank Payment"),
                                    body  : this.env._t("You are not allowed to validate this order"),
                                });
                                return;
                            }
                            else if (bank_payment && order.to_invoice){
                                    await this.validateOrder();
                            }
                            else{
                                if (this.env.pos.config.max_amount == 0){
                                await this.validateOrder();
                                this.rpc = this.env.pos.get('rpc');
                                if(order.to_invoice){
                                    if(order.get_client()){
                                        if(this.env.pos.config.fiscal_device_id){
                                            if(order.to_invoice){
                                                var invoice_number = '';
                                                const invoice = await this.rpc({
                                                        model: 'pos.order',
                                                        method: 'get_invoice_number',
                                                        args: [1, order.name],
                                                });
                                                if(invoice){
                                                    invoice_number = invoice
                                                }
                                            }
                                            var invoice_line = '\r\n' + _.str.sprintf('inp num=%s, TERM=TSFATS', invoice_number);
                                            for (var i = 0; i < this.env.pos.fiscal_devices.length; i++) {
                                                if(this.env.pos.fiscal_devices[i].id == this.env.pos.config.fiscal_device_id[0]){
                                                    var fiscal_device = this.env.pos.fiscal_devices[i];
                                                }
                                            }
                                            var mid = ''
                                            for (var j = 0; j < order.orderlines.models.length; j++) {
                                                var rep =1;
                                                if(order.orderlines.models[j].product.taxes_id[0]){
                                                    var tax = order.orderlines.models[j].product.taxes_id[0];
                                                    if(tax==fiscal_device.vat1[0]){
                                                        rep = 1
                                                    }
                                                    else if(tax==fiscal_device.vat2[0]){
                                                        rep = 2
                                                    }
                                                    else if(tax==fiscal_device.vat3[0]){
                                                        rep = 3
                                                    }
                                                    else if(tax==fiscal_device.vat4[0]){
                                                        rep = 4
                                                    }
                                                    else if(tax==fiscal_device.vat5[0]){
                                                        rep = 5
                                                    }
                                                }

                                                var qty = order.orderlines.models[j].quantity;
                                                var unit_price = order.orderlines.models[j].get_unit_price();
                                                if(order.orderlines.models[j].product.taxes_id[0]){
                                                    for (var m = 0; m < this.env.pos.product_taxes.length; m++) {
                                                        if(this.env.pos.product_taxes[m].id==order.orderlines.models[j].product.taxes_id[0]){
                                                            if(this.env.pos.product_taxes[m].price_include){
                                                                var unit_price_tax = unit_price
                                                            }
                                                            else{
                                                                var tax_per = (this.env.pos.product_taxes[m].amount)/100
                                                                var price_tax = tax_per * unit_price
                                                                var unit_price_tax = unit_price + price_tax
                                                            }
                                                        }

                                                    }
                                                    var price = this.env.pos.format_currency_no_symbol(unit_price_tax);
                                                }
                                                else{
                                                    var price = this.env.pos.format_currency_no_symbol(unit_price);
                                                }
                                                var str_price = price.replace(/\,/g,"");
                                                var floatValue_price = +(str_price);
                                                var name = order.orderlines.models[j].product.display_name.slice(0,20);
                                                var orderline = order.orderlines.models[j].get_price_with_tax();
                                                var dynamic_fiscal_device_prd_dynamic = _.str.sprintf(fiscal_device.prd_dynamic, rep, qty, floatValue_price, name);
                                                dynamic_fiscal_device_prd_dynamic += '\r\n'
                                                if(order.orderlines.models[j].discount){
                                                    var prezzo_line = _.str.sprintf('PERCA ALIQ= %.1f', order.orderlines.models[j].discount);

                                                    dynamic_fiscal_device_prd_dynamic += prezzo_line + '\r\n';
                                                }
                                                mid = mid + dynamic_fiscal_device_prd_dynamic
                                            }
                                            var change = order.get_total_paid()


                                            if(change > 0){
                                                change = this.env.pos.format_currency_no_symbol(change);
                                                var str_change = change.replace(/\,/g,"");
                                                var floatValue_change = +(str_change);
                                                var change_line = _.str.sprintf('IMP=%f', floatValue_change);
                                                change_line=change_line+";"
                                                var lines = fiscal_device.footer.split("\n");
                                                for (var k = 0; k < lines.length; k++) {

                                                    var n = lines[k].includes("CHIU");
                                                    if(n){
                                                        lines[k] = lines[k] + ', ' + change_line
                                                    }
                                                }
                                                var rest = lines.join("\r\n");
                                                var imp_footer = rest
                                                if(this.env.pos.config.receipt_footer){
                                                    var footer = _.str.sprintf(imp_footer, this.env.pos.config.receipt_footer);
                                                }
                                                else{
                                                    var footer = imp_footer
                                                }
                                            }
                                            else{
                                                if(this.env.pos.config.receipt_footer){
                                                    var footer = _.str.sprintf(fiscal_device.footer, this.env.pos.config.receipt_footer);
                                                }
                                                else{
                                                    var footer = fiscal_device.footer
                                                }
                                            }
                                            var headers = "";
                                            var header_new = fiscal_device.header.split("\n");


                                             for (var k = 0; k < header_new.length; k++) {

                                                    headers = headers + (header_new[k] + '\r\n');

                                                }
                                             var footers_new = footer.split("\n");
                                            var footers_2 = "";

                                             for (var k = 0; k < footers_new.length; k++) {

                                                    footers_2 = footers_2 + (footers_new[k] + '\r\n');

                                                }




                                            if(order.to_invoice){
                                                var content = headers + invoice_line +'\r\n'+'\r\n'+ mid +'\r\n'+footers_2
                                            }
                                            else{
                                                var content = headers +'\r\n'+mid +'\r\n'+footers_2
                                            }
                                            var element = document.createElement('a');
                                            var filename = fiscal_device.file_name + ".txt";
                                            element.setAttribute('href', 'data:text/plain;charset=utf-8,' + encodeURIComponent(content));
                                            element.setAttribute('download', filename);
                                            element.style.display = 'none';
                                            document.body.appendChild(element);
                                            element.click();
                                            document.body.removeChild(element);
                                        }
                                        else{
                                                await this.showPopup('ErrorPopup', {
                                                title : this.env._t("No Fiscal Device is Selected"),
                                                body  : this.env._t("No Fiscal Device is Selected. Make sure it is given in the pos configuration"),
                                            });
                                            return;
                                        }

                                    }

                                }
                                else{
                                    if(this.env.pos.config.fiscal_device_id){
                                            if(order.to_invoice){
                                                var invoice_number = '';
                                                const invoice = await this.rpc({
                                                        model: 'pos.order',
                                                        method: 'get_invoice_number',
                                                        args: [1, order.name],
                                                });
                                                if(invoice){
                                                    invoice_number = invoice
                                                }
                                            }
                                            var invoice_line = '\r\n' + _.str.sprintf('inp num=%s, TERM=TSFATS', invoice_number);
                                            for (var i = 0; i < this.env.pos.fiscal_devices.length; i++) {
                                                if(this.env.pos.fiscal_devices[i].id == this.env.pos.config.fiscal_device_id[0]){
                                                    var fiscal_device = this.env.pos.fiscal_devices[i];
                                                }
                                            }
                                            var mid = ''
                                            for (var j = 0; j < order.orderlines.models.length; j++) {
                                                var rep =1;
                                                if(order.orderlines.models[j].product.taxes_id[0]){
                                                    var tax = order.orderlines.models[j].product.taxes_id[0];
                                                    if(tax==fiscal_device.vat1[0]){
                                                        rep = 1
                                                    }
                                                    else if(tax==fiscal_device.vat2[0]){
                                                        rep = 2
                                                    }
                                                    else if(tax==fiscal_device.vat3[0]){
                                                        rep = 3
                                                    }
                                                    else if(tax==fiscal_device.vat4[0]){
                                                        rep = 4
                                                    }
                                                    else if(tax==fiscal_device.vat5[0]){
                                                        rep = 5
                                                    }
                                                }

                                                var qty = order.orderlines.models[j].quantity;
                                                var unit_price = order.orderlines.models[j].get_unit_price();
                                                if(order.orderlines.models[j].product.taxes_id[0]){
                                                    for (var m = 0; m < this.env.pos.product_taxes.length; m++) {
                                                        if(this.env.pos.product_taxes[m].id==order.orderlines.models[j].product.taxes_id[0]){
                                                            if(this.env.pos.product_taxes[m].price_include){
                                                                var unit_price_tax = unit_price
                                                            }
                                                            else{
                                                                var tax_per = (this.env.pos.product_taxes[m].amount)/100
                                                                var price_tax = tax_per * unit_price
                                                                var unit_price_tax = unit_price + price_tax
                                                            }
                                                        }

                                                    }
                                                    var price = this.env.pos.format_currency_no_symbol(unit_price_tax);
                                                }
                                                else{
                                                    var price = this.env.pos.format_currency_no_symbol(unit_price);
                                                }
                                                var str_price = price.replace(/\,/g,"");
                                                var floatValue_price = +(str_price);
                                                var name = order.orderlines.models[j].product.display_name.slice(0,20);
                                                var orderline = order.orderlines.models[j].get_price_with_tax();
                                                var dynamic_fiscal_device_prd_dynamic = _.str.sprintf(fiscal_device.prd_dynamic, rep, qty, floatValue_price, name);
                                                dynamic_fiscal_device_prd_dynamic += '\r\n'
                                                if(order.orderlines.models[j].discount){
                                                    var prezzo_line = _.str.sprintf('PERCA ALIQ= %.1f', order.orderlines.models[j].discount);

                                                    dynamic_fiscal_device_prd_dynamic += prezzo_line + '\r\n';
                                                }
                                                mid = mid + dynamic_fiscal_device_prd_dynamic
                                            }
                                            var change = order.get_total_paid()


                                            if(change > 0){
                                                change = this.env.pos.format_currency_no_symbol(change);
                                                var str_change = change.replace(/\,/g,"");
                                                var floatValue_change = +(str_change);
                                                var change_line = _.str.sprintf('IMP=%f', floatValue_change);
                                                change_line=change_line+";"
                                                var lines = fiscal_device.footer.split("\n");
                                                for (var k = 0; k < lines.length; k++) {

                                                    var n = lines[k].includes("CHIU");
                                                    if(n){
                                                        lines[k] = lines[k] + ', ' + change_line
                                                    }
                                                }
                                                var rest = lines.join("\r\n");
                                                var imp_footer = rest
                                                if(this.env.pos.config.receipt_footer){
                                                    var footer = _.str.sprintf(imp_footer, this.env.pos.config.receipt_footer);
                                                }
                                                else{
                                                    var footer = imp_footer
                                                }
                                            }
                                            else{
                                                if(this.env.pos.config.receipt_footer){
                                                    var footer = _.str.sprintf(fiscal_device.footer, this.env.pos.config.receipt_footer);
                                                }
                                                else{
                                                    var footer = fiscal_device.footer
                                                }
                                            }
                                            var headers = "";
                                            var header_new = fiscal_device.header.split("\n");


                                             for (var k = 0; k < header_new.length; k++) {

                                                    headers = headers + (header_new[k] + '\r\n');

                                                }
                                            var footers_new = footer.split("\n");
                                            var footers_2 = "";

                                             for (var k = 0; k < footers_new.length; k++) {

                                                    footers_2 = footers_2 + (footers_new[k] + '\r\n');

                                                }




                                            if(order.to_invoice){
                                                var content = headers + invoice_line +'\r\n'+'\r\n'+ mid +'\r\n'+footers_2
                                            }
                                            else{
                                                var content = headers +'\r\n'+mid +'\r\n'+footers_2
                                            }
                                            var element = document.createElement('a');
                                            var filename = fiscal_device.file_name + ".txt";
                                            element.setAttribute('href', 'data:text/plain;charset=utf-8,' + encodeURIComponent(content));
                                            element.setAttribute('download', filename);
                                            element.style.display = 'none';
                                            document.body.appendChild(element);
                                            element.click();
                                            document.body.removeChild(element);
                                        }
                                    else{
                                            await this.showPopup('ErrorPopup', {
                                            title : this.env._t("No Fiscal Device is Selected"),
                                            body  : this.env._t("No Fiscal Device is Selected. Make sure it is given in the pos configuration"),
                                        });
                                        return;
                                    }

                                }
                            }
                                else if (order.get_total_with_tax() <= this.env.pos.config.max_amount) {
                                await this.validateOrder();
                                this.rpc = this.env.pos.get('rpc');
                                if(order.to_invoice){
                                    if(order.get_client()){
                                        if(this.env.pos.config.fiscal_device_id){
                                            if(order.to_invoice){
                                                var invoice_number = '';
                                                const invoice = await this.rpc({
                                                        model: 'pos.order',
                                                        method: 'get_invoice_number',
                                                        args: [1, order.name],
                                                });
                                                if(invoice){
                                                    invoice_number = invoice
                                                }
                                            }
                                            var invoice_line = '\r\n' + _.str.sprintf('inp num=%s, TERM=TSFATS', invoice_number);
                                            for (var i = 0; i < this.env.pos.fiscal_devices.length; i++) {
                                                if(this.env.pos.fiscal_devices[i].id == this.env.pos.config.fiscal_device_id[0]){
                                                    var fiscal_device = this.env.pos.fiscal_devices[i];
                                                }
                                            }
                                            var mid = ''
                                            for (var j = 0; j < order.orderlines.models.length; j++) {
                                                var rep =1;
                                                if(order.orderlines.models[j].product.taxes_id[0]){
                                                    var tax = order.orderlines.models[j].product.taxes_id[0];
                                                    if(tax==fiscal_device.vat1[0]){
                                                        rep = 1
                                                    }
                                                    else if(tax==fiscal_device.vat2[0]){
                                                        rep = 2
                                                    }
                                                    else if(tax==fiscal_device.vat3[0]){
                                                        rep = 3
                                                    }
                                                    else if(tax==fiscal_device.vat4[0]){
                                                        rep = 4
                                                    }
                                                    else if(tax==fiscal_device.vat5[0]){
                                                        rep = 5
                                                    }
                                                }

                                                var qty = order.orderlines.models[j].quantity;
                                                var unit_price = order.orderlines.models[j].get_unit_price();
                                                if(order.orderlines.models[j].product.taxes_id[0]){
                                                    for (var m = 0; m < this.env.pos.product_taxes.length; m++) {
                                                        if(this.env.pos.product_taxes[m].id==order.orderlines.models[j].product.taxes_id[0]){
                                                            if(this.env.pos.product_taxes[m].price_include){
                                                                var unit_price_tax = unit_price
                                                            }
                                                            else{
                                                                var tax_per = (this.env.pos.product_taxes[m].amount)/100
                                                                var price_tax = tax_per * unit_price
                                                                var unit_price_tax = unit_price + price_tax
                                                            }
                                                        }

                                                    }
                                                    var price = this.env.pos.format_currency_no_symbol(unit_price_tax);
                                                }
                                                else{
                                                    var price = this.env.pos.format_currency_no_symbol(unit_price);
                                                }
                                                var str_price = price.replace(/\,/g,"");
                                                var floatValue_price = +(str_price);
                                                var name = order.orderlines.models[j].product.display_name.slice(0,20);
                                                var orderline = order.orderlines.models[j].get_price_with_tax();
                                                var dynamic_fiscal_device_prd_dynamic = _.str.sprintf(fiscal_device.prd_dynamic, rep, qty, floatValue_price, name);
                                                dynamic_fiscal_device_prd_dynamic += '\r\n'
                                                if(order.orderlines.models[j].discount){
                                                    var prezzo_line = _.str.sprintf('PERCA ALIQ= %.1f', order.orderlines.models[j].discount);

                                                    dynamic_fiscal_device_prd_dynamic += prezzo_line + '\r\n';
                                                }
                                                mid = mid + dynamic_fiscal_device_prd_dynamic
                                            }
                                            var change = order.get_total_paid()


                                            if(change > 0){
                                                change = this.env.pos.format_currency_no_symbol(change);
                                                var str_change = change.replace(/\,/g,"");
                                                var floatValue_change = +(str_change);
                                                var change_line = _.str.sprintf('IMP=%f', floatValue_change);
                                                change_line=change_line+";"
                                                var lines = fiscal_device.footer.split("\n");
                                                for (var k = 0; k < lines.length; k++) {

                                                    var n = lines[k].includes("CHIU");
                                                    if(n){
                                                        lines[k] = lines[k] + ', ' + change_line
                                                    }
                                                }
                                                var rest = lines.join("\r\n");
                                                var imp_footer = rest
                                                if(this.env.pos.config.receipt_footer){
                                                    var footer = _.str.sprintf(imp_footer, this.env.pos.config.receipt_footer);
                                                }
                                                else{
                                                    var footer = imp_footer
                                                }
                                            }
                                            else{
                                                if(this.env.pos.config.receipt_footer){
                                                    var footer = _.str.sprintf(fiscal_device.footer, this.env.pos.config.receipt_footer);
                                                }
                                                else{
                                                    var footer = fiscal_device.footer
                                                }
                                            }
                                             var headers = "";
                                             var header_new = fiscal_device.header.split("\n");


                                             for (var k = 0; k < header_new.length; k++) {

                                                    headers = headers + (header_new[k] + '\r\n');

                                                }
                                            var footers_new = footer.split("\n");
                                            var footers_2 = "";

                                             for (var k = 0; k < footers_new.length; k++) {

                                                    footers_2 = footers_2 + (footers_new[k] + '\r\n');

                                                }




                                            if(order.to_invoice){
                                                var content = headers + invoice_line +'\r\n'+'\r\n'+ mid +'\r\n'+footers_2
                                            }
                                            else{
                                                var content = headers +'\r\n'+mid +'\r\n'+footers_2
                                            }
                                            var element = document.createElement('a');
                                            var filename = fiscal_device.file_name + ".txt";
                                            element.setAttribute('href', 'data:text/plain;charset=utf-8,' + encodeURIComponent(content));
                                            element.setAttribute('download', filename);
                                            element.style.display = 'none';
                                            document.body.appendChild(element);
                                            element.click();
                                            document.body.removeChild(element);
                                        }
                                        else{
                                                await this.showPopup('ErrorPopup', {
                                                title : this.env._t("No Fiscal Device is Selected"),
                                                body  : this.env._t("No Fiscal Device is Selected. Make sure it is given in the pos configuration"),
                                            });
                                            return;
                                        }

                                    }

                                }
                                else{
                                    if(this.env.pos.config.fiscal_device_id){
                                            if(order.to_invoice){
                                                var invoice_number = '';
                                                const invoice = await this.rpc({
                                                        model: 'pos.order',
                                                        method: 'get_invoice_number',
                                                        args: [1, order.name],
                                                });
                                                if(invoice){
                                                    invoice_number = invoice
                                                }
                                            }
                                            var invoice_line = '\r\n' + _.str.sprintf('inp num=%s, TERM=TSFATS', invoice_number);
                                            for (var i = 0; i < this.env.pos.fiscal_devices.length; i++) {
                                                if(this.env.pos.fiscal_devices[i].id == this.env.pos.config.fiscal_device_id[0]){
                                                    var fiscal_device = this.env.pos.fiscal_devices[i];
                                                }
                                            }
                                            var mid = ''
                                            for (var j = 0; j < order.orderlines.models.length; j++) {
                                                var rep =1;
                                                if(order.orderlines.models[j].product.taxes_id[0]){
                                                    var tax = order.orderlines.models[j].product.taxes_id[0];
                                                    if(tax==fiscal_device.vat1[0]){
                                                        rep = 1
                                                    }
                                                    else if(tax==fiscal_device.vat2[0]){
                                                        rep = 2
                                                    }
                                                    else if(tax==fiscal_device.vat3[0]){
                                                        rep = 3
                                                    }
                                                    else if(tax==fiscal_device.vat4[0]){
                                                        rep = 4
                                                    }
                                                    else if(tax==fiscal_device.vat5[0]){
                                                        rep = 5
                                                    }
                                                }

                                                var qty = order.orderlines.models[j].quantity;
                                                var unit_price = order.orderlines.models[j].get_unit_price();
                                                if(order.orderlines.models[j].product.taxes_id[0]){
                                                    for (var m = 0; m < this.env.pos.product_taxes.length; m++) {
                                                        if(this.env.pos.product_taxes[m].id==order.orderlines.models[j].product.taxes_id[0]){
                                                            if(this.env.pos.product_taxes[m].price_include){
                                                                var unit_price_tax = unit_price
                                                            }
                                                            else{
                                                                var tax_per = (this.env.pos.product_taxes[m].amount)/100
                                                                var price_tax = tax_per * unit_price
                                                                var unit_price_tax = unit_price + price_tax
                                                            }
                                                        }

                                                    }
                                                    var price = this.env.pos.format_currency_no_symbol(unit_price_tax);
                                                }
                                                else{
                                                    var price = this.env.pos.format_currency_no_symbol(unit_price);
                                                }
                                                var str_price = price.replace(/\,/g,"");
                                                var floatValue_price = +(str_price);
                                                var name = order.orderlines.models[j].product.display_name.slice(0,20);
                                                var orderline = order.orderlines.models[j].get_price_with_tax();
                                                var dynamic_fiscal_device_prd_dynamic = _.str.sprintf(fiscal_device.prd_dynamic, rep, qty, floatValue_price, name);
                                                dynamic_fiscal_device_prd_dynamic += '\r\n'
                                                if(order.orderlines.models[j].discount){
                                                    var prezzo_line = _.str.sprintf('PERCA ALIQ= %.1f', order.orderlines.models[j].discount);

                                                    dynamic_fiscal_device_prd_dynamic += prezzo_line + '\r\n';
                                                }
                                                mid = mid + dynamic_fiscal_device_prd_dynamic
                                            }
                                            var change = order.get_total_paid()



                                            if(change > 0){
                                                change = this.env.pos.format_currency_no_symbol(change);
                                                var str_change = change.replace(/\,/g,"");
                                                var floatValue_change = +(str_change);
                                                var change_line = _.str.sprintf('IMP=%f', floatValue_change);
                                                change_line=change_line+";"
                                                var lines = fiscal_device.footer.split("\n");

                                                for (var k = 0; k < lines.length; k++) {

                                                    var n = lines[k].includes("CHIU");
                                                    if(n){
                                                        lines[k] = lines[k] + ', ' + change_line
                                                    }
                                                }

                                                var rest = lines.join("\r\n");
                                                var imp_footer = rest
                                                if(this.env.pos.config.receipt_footer){
                                                    var footer = _.str.sprintf(imp_footer, this.env.pos.config.receipt_footer);
                                                }
                                                else{
                                                    var footer = imp_footer
                                                }
                                            }
                                            else{
                                                if(this.env.pos.config.receipt_footer){
                                                    var footer = _.str.sprintf(fiscal_device.footer, this.env.pos.config.receipt_footer);
                                                }
                                                else{
                                                    var footer = fiscal_device.footer
                                                }
                                            }
                                            var headers = "";
                                            var header_new = fiscal_device.header.split("\n");


                                             for (var k = 0; k < header_new.length; k++) {

                                                    headers = headers + (header_new[k] + '\r\n');

                                                }
                                            var footers_new = footer.split("\n");
                                            var footers_2 = "";

                                             for (var k = 0; k < footers_new.length; k++) {

                                                    footers_2 = footers_2 + (footers_new[k] + '\r\n');

                                                }




                                            if(order.to_invoice){
                                                var content = headers + invoice_line +'\r\n'+'\r\n'+ mid +'\r\n'+footers_2
                                            }
                                            else{
                                                var content = headers +'\r\n'+mid +'\r\n'+footers_2
                                            }
                                            var element = document.createElement('a');
                                            var filename = fiscal_device.file_name + ".txt";
                                            element.setAttribute('href', 'data:text/plain;charset=utf-8,' + encodeURIComponent(content));
                                            element.setAttribute('download', filename);
                                            element.style.display = 'none';
                                            document.body.appendChild(element);
                                            element.click();
                                            document.body.removeChild(element);
                                        }
                                    else{
                                            await this.showPopup('ErrorPopup', {
                                            title : this.env._t("No Fiscal Device is Selected"),
                                            body  : this.env._t("No Fiscal Device is Selected. Make sure it is given in the pos configuration"),
                                        });
                                        return;
                                    }

                                }


                            }
                                else{
                                    if(cash_checked){
                                        await this.showPopup('ErrorPopup', {
                                            title : this.env._t("Maximum Amount Exceeded"),
                                            body  : this.env._t("You are not allowed to validate this order"),
                                        });
                                        return;
                                    }
                                    else{
                                        if(bank_payment && !order.to_invoice){
                                            await this.showPopup('ErrorPopup', {
                                                title : this.env._t("Maximum Amount Exceeded"),
                                                body  : this.env._t("You are not allowed to validate this order"),
                                            });
                                            return;
                                        }
                                        else{
                                            await this.validateOrder();
                                        }

                                    }
                            }
                            }


                        }

                }

            }
    };

    Registries.Component.extend(PaymentScreen, TestPaymentScreen);

    return PaymentScreen;

});



