odoo.define('auth_signup.signup', function (require) {
	'use strict';

	var publicWidget = require('web.public.widget');

	publicWidget.registry.LogInForm = publicWidget.Widget.extend({
		selector: '.oe_login_form',
		events: {
			'submit': '_onSubmit',
		},

		//--------------------------------------------------------------------------
		// Handlers
		//--------------------------------------------------------------------------

		/**
		 * @private
		 */
		_onSubmit: function () {
			var $btn = this.$('.oe_login_buttons > button[type="submit"]');
			$btn.attr('disabled', 'disabled');
			$btn.prepend('<i class="fa fa-refresh fa-spin"/> ');
		},
	});
});
