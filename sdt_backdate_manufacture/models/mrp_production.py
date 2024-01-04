from odoo import api, models, fields,_
from datetime import datetime
import pytz
from  odoo.exceptions import UserError


class SdtMrpProduction(models.Model):
    _inherit = "mrp.production"

    mrp_date = fields.Datetime('Manufactured Date')

    def action_confirm(self):
        res = super(SdtMrpProduction, self).action_confirm()

        for data in self:
            if data.state == 'confirmed':
                if data.mrp_date:
                    data.move_raw_ids.write({'date': data.mrp_date})
        return res
    
    def _plan_workorders(self, replan=False):
        now = fields.Datetime.now
        today = datetime.today().strftime("%d, %m, %Y")
        date = self.date_planned_start.strftime('%d/%m/%Y')
        if date != today:
            self.ensure_one()

            if not self.workorder_ids:
                return
            # Schedule all work orders (new ones and those already created)
            qty_to_produce = max(self.product_qty - self.qty_produced, 0)
            qty_to_produce = self.product_uom_id._compute_quantity(qty_to_produce, self.product_id.uom_id)
            start_date = max(self.date_planned_start, self.date_planned_start)
            if replan:
                workorder_ids = self.workorder_ids.filtered(lambda wo: wo.state in ['ready', 'pending'])
                # We plan the manufacturing order according to its `date_planned_start`, but if
                # `date_planned_start` is in the past, we plan it as soon as possible.
                workorder_ids.leave_id.unlink()
            else:
                workorder_ids = self.workorder_ids.filtered(lambda wo: not wo.date_planned_start)
            for workorder in workorder_ids:
                workcenters = workorder.workcenter_id | workorder.workcenter_id.alternative_workcenter_ids

                best_finished_date = datetime.max
                vals = {}
                for workcenter in workcenters:
                    # compute theoretical duration
                    if workorder.workcenter_id == workcenter:
                        duration_expected = workorder.duration_expected
                    else:
                        duration_expected = workorder._get_duration_expected(alternative_workcenter=workcenter)

                    from_date, to_date = workcenter._get_first_available_slot(start_date, duration_expected)
                    # If the workcenter is unavailable, try planning on the next one
                    if not from_date:
                        continue
                    # Check if this workcenter is better than the previous ones
                    if to_date and to_date < best_finished_date:
                        best_start_date = start_date
                        best_finished_date = start_date
                        best_workcenter = workcenter
                        vals = {
                            'workcenter_id': workcenter.id,
                            'duration_expected': duration_expected,
                        }

                # If none of the workcenter are available, raise
                if best_finished_date == datetime.max:
                    raise UserError(_('Impossible to plan the workorder. Please check the workcenter availabilities.'))

                # Instantiate start_date for the next workorder planning
                # if workorder.next_work_order_id:
                #     start_date = best_finished_date

                # Create leave on chosen workcenter calendar
                leave = self.env['resource.calendar.leaves'].create({
                    'name': workorder.display_name,
                    'calendar_id': best_workcenter.resource_calendar_id.id,
                    'date_from': best_start_date,
                    'date_to': best_finished_date,
                    'resource_id': best_workcenter.resource_id.id,
                    'time_type': 'other'
                })
                vals['leave_id'] = leave.id
                workorder.write(vals)
            self.with_context(force_date=True).write({
                'date_planned_start': self.workorder_ids[0].date_planned_start,
                'date_planned_finished': self.workorder_ids[-1].date_planned_finished
            })

        else:
            return super(SdtMrpProduction, self)._plan_workorders()

    def button_mark_done(self):
        res = super(SdtMrpProduction, self).button_mark_done()

        for data in self:
            if isinstance(data.mrp_date, str) == True:
                        data.mrp_date = datetime.strptime(data.mrp_date, "%Y-%m-%d %H:%M:%S")
            user_tz = self.env.user.tz or pytz.utc
            local = pytz.timezone(user_tz)
            local_date = pytz.utc.localize(data.mrp_date).astimezone(local)
            user_date = local_date.replace(tzinfo=None)

            if data.move_finished_ids.account_move_ids:
                data.move_raw_ids.write({'date': data.mrp_date})
                data.move_raw_ids.move_line_ids.write({'date': data.mrp_date})
                
                for rec in data.move_raw_ids:
                    sql_query="""Update stock_valuation_layer set create_date=%s where stock_move_id=%s
                            """
                    self.env.cr.execute(sql_query,(data.mrp_date,rec.id))

                    if rec.account_move_ids:
                        name = rec.account_move_ids.name.split('/')
                        if name[0] == 'STJ' and name[1] != str(user_date.year):
                            query = """update account_move set name = %s , date = %s where id = %s"""
                            seq = self.env['ir.sequence'].search([('name', '=', 'STJ Sequence')])
                            old_sequence = self.env['ir.sequence.date_range'].search([('date_from', '=', datetime.strptime('%s-05-01'%name[1], "%Y-%m-%d")), ('sequence_id', '=', seq.id)])
                            new_sequence = seq.next_by_id(user_date)
                            self.env.cr.execute(query, (new_sequence, str(user_date), rec.account_move_ids.id))
                            old_sequence.number_next_actual = old_sequence.number_next_actual - 1
                        else:
                            rec.account_move_ids.write({'date': user_date})

                data.move_finished_ids.write({'date': data.mrp_date})
                data.finished_move_line_ids.write({'date': data.mrp_date})
                for move_finish in data.move_finished_ids:
                    sql_query="""Update stock_valuation_layer set create_date=%s where stock_move_id=%s
                            """
                    self.env.cr.execute(sql_query,(data.mrp_date,move_finish.id))

                    name = move_finish.account_move_ids.name.split('/')
                    if name[0] == 'STJ' and name[1] != str(user_date.year):
                        query = """update account_move set name = %s , create_date = %s, date = %s where id = %s"""
                        seq = self.env['ir.sequence'].search([('name', '=', 'STJ Sequence')])
                        old_sequence = self.env['ir.sequence.date_range'].search([('date_from', '=', datetime.strptime('%s-05-01'%name[1], "%Y-%m-%d")), ('sequence_id', '=', seq.id)])
                        new_sequence = seq.next_by_id(user_date)
                        self.env.cr.execute(query, (new_sequence, str(user_date), str(user_date), move_finish.account_move_ids.id))
                        old_sequence.number_next_actual = old_sequence.number_next_actual - 1
                    else:
                        move_finish.account_move_ids.write({'date': user_date})
                    # move_finish.account_move_ids.write({'date': user_date})
            else:
                return res
