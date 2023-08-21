from datetime import datetime
from datetime import date as datetime_date, timedelta
import pytz
from dateutil.relativedelta import relativedelta
from odoo import _, fields, models,api
from odoo.exceptions import UserError
import calendar


class IrSequence(models.Model):
    _inherit = "ir.sequence"
    
    records_to_add_line = fields.Integer(' Add Records', default=1)
    to_day = fields.Date(string='Start Date',)
    range_type = fields.Selection([('yearly','Yearly'),('monthly','monthly')], string='Range Type', default='yearly')
    

    def new_records(self):
        # temp_array = []
        # # Basic If Conditional
        # if self.name:
        #     temp_name = self.name
        # else:
        #     temp_name = 'Logitech'

        # # date_now = fields.datetime.now().date().strftime("%Y-%m-%d")
        # # self.to_day = fields.Date.context_today(self).strftime("%Y-%m-%d")
        # date_now = self.to_day
        # # date_from = datetime.strptime('2022-01-01','%Y-%m-%d')
        # # date_to = datetime.strptime('2022-12-31','%Y-%m-%d')
        # # date_to = calendar.monthrange(date_now.year, date_now.month)[1]
        # last_day = date_now + relativedelta(months=1) - relativedelta(days=date_now.day)

        # # if self.date_range_ids :
        # #     for i in range(0, self.records_to_add_line):
        # #         date_from = date_now + relativedelta(months=1)
        # #         date_from1 = date_from
        # #         date_to = last_day + relativedelta(months=1)
        # #         value = {
        # #             'sequence_id':(self.records_to_add_line, temp_name),
        # #             'number_next_actual' : 1,
        # #             'date_from' : date_from1,
        # #             'date_to' : date_to 
        # #         }
        # #         temp_array.append((0, 0, value))
        # # else :
        # #     for i in range(0,1):
        # #         value = {
        # #             'sequence_id':(self.records_to_add_line, temp_name),
        # #             'number_next_actual' : 1,
        # #             'date_from' : date_now,
        # #             'date_to' : last_day
        # #         }
        # #         temp_array.append((0, 0, value))
        # for i in range(0,1):
        #         value = {
        #             'sequence_id':(self.records_to_add_line, temp_name),
        #             'number_next_actual' : 1,
        #             'date_from' : date_now,
        #             'date_to' : last_day
        #         }
        #         temp_array.append((0, 0, value))
        # for i in range(0, (self.records_to_add_line-1)):
        #         date_now = date_now + relativedelta(months=1) - relativedelta(days=date_now.day) + relativedelta(days=1)
        #         last_day = date_now + relativedelta(months=1) - relativedelta(days=1)
        #         value = {
        #             'sequence_id':(self.records_to_add_line, temp_name),
        #             'number_next_actual' : 1,
        #             'date_from' : date_now,
        #             'date_to' : last_day 
        #         }
        #         temp_array.append((0, 0, value))
        # self.write({
        #     'date_range_ids' : temp_array,
        # })
        
        this_year = str(fields.Date.today().year)
        if self.range_type=='yearly':
            rg=self.records_to_add_line or 1
            date_range_ids = self.env['ir.sequence.date_range'].search([('sequence_id','=',self.id)],limit=1, order='date_to desc')
            if date_range_ids:
                date_from = date_range_ids.date_from + relativedelta(years=1)
                date_to = date_range_ids.date_to + relativedelta(years=1)
            else:
                date_from = datetime.strptime("%s-01-01"%this_year,"%Y-%m-%d")
                date_to = datetime.strptime('%s-12-31'%this_year,"%Y-%m-%d")
            self.generate_sequence(rg,date_from,date_to)
        else:
            rg=self.records_to_add_line or 12
            date_range_ids = self.env['ir.sequence.date_range'].search([('sequence_id','=',self.id)],limit=1, order='date_to desc')
            if date_range_ids:
                date_from = date_range_ids.date_from
                date_to = date_range_ids.date_to
                date_from = date_from + relativedelta(months=1) - relativedelta(days=date_from.day) + relativedelta(days=1)
                date_to = date_from + relativedelta(months=1) - relativedelta(days=1)
                            
            else:
                date_from = datetime.strptime('%s-01-01'%this_year,"%Y-%m-%d")
                date_to = datetime.strptime('%s-01-31'%this_year,"%Y-%m-%d")
            self.generate_sequence(rg,date_from,date_to)


    def generate_sequence(self,rg=1, date_from=False, date_to=False):
        temp_array=[]
        for i in range(0, (rg)):
            value = {
                'number_next_actual' : 1,
                'date_from' : date_from,
                'date_to' : date_to 
            }
            temp_array.append((0, 0, value))
            if self.range_type=='yearly':
                date_from = date_from + relativedelta(years=1)
                date_to = date_to + relativedelta(years=1)
            else:
                date_from = date_from + relativedelta(months=1) - relativedelta(days=date_from.day) + relativedelta(days=1)
                date_to = date_from + relativedelta(months=1) - relativedelta(days=1)
        self.write({
            'date_range_ids' : temp_array,
        })


    def action_seq_range(self):
        all_sequence = self.search([('use_date_range','=',True)])
        for seq in all_sequence:
            this_year = fields.datetime.now().date().strftime("%Y")
            if seq.range_type=='yearly':
                check_date = this_year
                sql_query = """
                    select id from ir_sequence_date_range where sequence_id=%s and to_char(date_to AT time zone 'UTC', 'YYYY')=%s
                """
                self.env.cr.execute(sql_query, (seq.id,check_date,))
                results = self.env.cr.dictfetchall()
                if not results:
                    date_range_ids = self.env['ir.sequence.date_range'].search([('sequence_id','=',seq.id)],limit=1, order='date_to desc')
                    if date_range_ids:
                        date_from = date_range_ids.date_from + relativedelta(years=1)
                        date_to = date_range_ids.date_to + relativedelta(years=1)
                        # rg=seq.records_to_add_line or 1
                        rg=1
                        seq.generate_sequence(rg,date_from,date_to)
                    else:
                        date_from = datetime.strptime("%s-01-01"%this_year,"%Y-%m-%d")
                        date_to = datetime.strptime('%s-12-31'%this_year,"%Y-%m-%d")
                        # rg=seq.records_to_add_line or 1
                        rg=1
                        seq.generate_sequence(rg,date_from,date_to)
                        this_year = str(fields.Date.today().year)
                        
            elif seq.range_type=='monthly':
                check_date = fields.datetime.now().date().strftime("%Y-%m")
                this_month = fields.datetime.now().date().strftime("%m")
                sql_query = """
                    select id from ir_sequence_date_range where sequence_id=%s and to_char(date_to AT time zone 'UTC', 'YYYY-MM')=%s
                """
                self.env.cr.execute(sql_query, (seq.id,check_date,))
                results = self.env.cr.dictfetchall()
                if not results:
                    date_range_ids = self.env['ir.sequence.date_range'].search([('sequence_id','=',seq.id)],limit=1, order='date_to desc')
                    if date_range_ids:
                        cur_month = date_range_ids.date_to.month
                        date_from = date_range_ids.date_from
                        date_to = date_range_ids.date_to
                        date_from = date_from + relativedelta(months=1) - relativedelta(days=date_from.day) + relativedelta(days=1)
                        date_to = date_from + relativedelta(months=1) - relativedelta(days=1)
                        rg=int(this_month)-int(cur_month) or 1
                        seq.generate_sequence(rg,date_from,date_to)        
                    else:
                        date_from = datetime.strptime('%s-01-01'%this_year,"%Y-%m-%d")
                        date_to = datetime.strptime('%s-01-31'%this_year,"%Y-%m-%d")
                        # rg=seq.records_to_add_line or 12
                        rg=1
                        seq.generate_sequence(rg,date_from,date_to)


    @api.onchange('range_type')
    def _onchange_range_type(self):
        if not self.range_type:
            return
        if self.range_type=='yearly':
            self.records_to_add_line=1
        else:
            self.records_to_add_line=12