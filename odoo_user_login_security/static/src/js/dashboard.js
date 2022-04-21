odoo.define('odoo_user_login_security.backend.dashboard',function (require) {
	'use strict';

	var AbstractAction = require('web.AbstractAction');
	var ajax = require('web.ajax');
	var core = require('web.core');

	var Dashboard = AbstractAction.extend({
		template: 'session_dashboard_template',
		jsLibs: [
			'/web/static/lib/Chart/Chart.js',
		],
		events: {
			'click .dashboard_action': 'on_dashboard_action',
		},

		init (parent,context) {
			this._super(parent,context);
		},

		willStart () {
			var self = this;
			return $.when(
				ajax.loadLibs(this),
				this._super(),
			).then(function () {
				return self.fetch_data();
			})
		},

		on_attach_callback () {
			this.render_graph();
			var owl = $('.owl-carousel')
			owl.owlCarousel({
				autoplay          : true,
				autoplayHoverPause: true,
				autoplayTimeout   : 2500,
				dots              : false,
				loop              : true,
				nav               : false,
				responsive        : {
					0   : {items: 1},
					600 : {items: 2},
					960 : {items: 3},
					1200: {items: 4},
				}
			});
			owl.on('mousewheel','.owl-stage',function (e) {
				if (e.deltaY>0) {
					owl.trigger('next.owl');
				} else {
					owl.trigger('prev.owl');
				}
				e.preventDefault();
			});
		},

		fetch_data () {
			var self = this;
			return this._rpc({
				route: '/session/fetch_dashboard_data',
				params: {
					tz: Intl.DateTimeFormat().resolvedOptions().timeZone,
				}
			}).then(function(result) {
				self.browser_sessions = result.browser_sessions
				self.recent_sessions  = result.recent_sessions
				self.state_counts     = result.state_counts
			});
		},

		render_graph () {
			var self = this;
			self.chart = new Chart('dashboard_pi_chart',{
				type: 'pie',
				data: {
					labels: self.state_counts.map(self => self.status),
					datasets: [{
						data: self.state_counts.map(self => self.count),
						backgroundColor: ['#17a2b8','#28a745','#6c757d','#dc3545','#232528',],
					}],
				},
				options: {
					maintainAspectRatio: false,
					legend: {
						position: 'top',
						labels: {usePointStyle: true},
					},
					onClick (e,i){
						if (i.length) {
							var state = i[0]['_view']['label']
							state = self.state_counts.filter(a => a['status'] === state)[0]['state']
							self.do_action({
								name     : 'Sessions',
								type     : 'ir.actions.act_window',
								res_model: 'session.session',
								views    : [[false,'list'],[false,'form']],
								domain   : [['state','=',state]],
								context  : {'active_test': false},
							});
						}
					},
				},
			});
		},

		on_dashboard_action (e) {
			e.preventDefault();
			var action = $(e.currentTarget);
			var act_window = {
				name     : 'Sessions',
				type     : 'ir.actions.act_window',
				res_model: 'session.session',
				views    : [[false,'list'],[false,'form']],
				domain   : [],
			};

			var id = action.data('id')
			if (id) {
				act_window.res_id = id;
				act_window.views = [[false,'form']];
			}

			var browser = action.data('browser');
			if (browser) {
				act_window.domain.push(['browser','=',browser]);
			}

			var inactive = action.data('inactive');
			if (inactive) {
				act_window.context = {active_test: false};
			}

			this.do_action(act_window);
		},
	});

	core.action_registry.add('session_dashboard',Dashboard);
	return Dashboard;
});
