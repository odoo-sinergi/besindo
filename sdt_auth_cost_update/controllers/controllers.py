# -*- coding: utf-8 -*-
from odoo import http

# class ProductionBatch(http.Controller):
#     @http.route('/nw_batch/nw_batch/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/nw_batch/nw_batch/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('nw_batch.listing', {
#             'root': '/nw_batch/nw_batch',
#             'objects': http.request.env['nw_batch.nw_batch'].search([]),
#         })

#     @http.route('/nw_batch/nw_batch/objects/<model("nw_batch.nw_batch"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('nw_batch.object', {
#             'object': obj
#         })