# -*- coding: utf-8 -*-
# from odoo import http


# class SubscriptionTekniq(http.Controller):
#     @http.route('/subscription_tekniq/subscription_tekniq', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/subscription_tekniq/subscription_tekniq/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('subscription_tekniq.listing', {
#             'root': '/subscription_tekniq/subscription_tekniq',
#             'objects': http.request.env['subscription_tekniq.subscription_tekniq'].search([]),
#         })

#     @http.route('/subscription_tekniq/subscription_tekniq/objects/<model("subscription_tekniq.subscription_tekniq"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('subscription_tekniq.object', {
#             'object': obj
#         })

