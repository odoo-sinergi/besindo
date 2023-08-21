from odoo import models, fields, api
from odoo.exceptions import ValidationError

class ProductTemplate(models.Model):
    _inherit="product.template"

    @api.constrains('default_code')
    def check_default_code(self):
        for rec in self:
            if rec.default_code != False:
                # products = self.env['product.template'].search([('default_code', '=', rec.default_code), ('id', '!=', rec.id)])
                sql_query = """select id from product_template where default_code=%s and id!=%s"""
                self._cr.execute(sql_query, (rec.default_code,rec.id))
                products = self._cr.dictfetchall()
                if products:
                    raise ValidationError(("Internal Reference '%s' Already Exists" % rec.default_code))

