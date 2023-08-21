from odoo import fields, models, api, _


class AccountMoveLine(models.Model):
    _inherit='account.move.line'


    analytic_product_id = fields.Many2one('account.analytic.account', string='Analytic Product', domain="[('plan_id.name','=','Product')]")
    analytic_project_id = fields.Many2one('account.analytic.account', string='Analytic Project', domain="[('plan_id.name','=','Project')]")
    analytic_section_id = fields.Many2one('account.analytic.account', string='Analytic Section', domain="[('plan_id.name','=','Section')]")
    analytic_departement_id = fields.Many2one('account.analytic.account', string='Analytic Departement', domain="[('plan_id.name','=','Departement')]")
    
   
    
    


    


    
    

    
