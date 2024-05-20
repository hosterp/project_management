from openerp import fields, models, api
from datetime import datetime
from openerp.exceptions import Warning as UserError
from openerp.osv import osv
from openerp.tools.translate import _
from dateutil import relativedelta
from openerp.exceptions import except_orm, ValidationError

class PartnerDailyStatementLine(models.Model):
    _name = 'partner.daily.statement.line'


    @api.multi
    @api.depends('quantity','rate')
    def compute_qty(self):
        for rec in self:
            rec.total = rec.quantity * rec.rate

    date = fields.Date("Date",default=lambda self: fields.datetime.now())
    quantity = fields.Float('Quantity')
    total = fields.Float('Total',compute='compute_qty',stroe=True)
    item = fields.Selection([('skilled',"Skilled Labour"),
                             ('unskilled',"Unskilled Labour"),
                             ('survey',"Survey Labour"),
                             ('union',"Union Labour")],"Item")
    rate = fields.Float('Rate')
    unit_id = fields.Many2one('product.uom',"Unit")
    vr_no = fields.Char(String="VR NO")
    payment = fields.Float('Payment')
    remarks = fields.Text('Remarks')
    project_id = fields.Many2one('project.project',"Project")
    report_id = fields.Many2one('partner.daily.statement', 'Report')

class PartnerDailyStatement(models.Model):
    _name = 'partner.daily.statement'
    _order = 'date desc'


    @api.model
    def default_get(self, default_fields):
        vals = super(PartnerDailyStatement, self).default_get(default_fields)
        user = self.env['res.users'].search([('id', '=', self.env.user.id)])
        if user:
            if user.employee_id:
                vals.update({'employee_id': user.employee_id.id,

                             })
            if not user.employee_id and user.id != 1:
                raise osv.except_osv(_('Error!'), _("User and Employee is not linked."))
        return vals

    @api.onchange('project_id')
    def onchange_project_id(self):
        self.location_ids = self.project_id.location_id
        values_list = []
        for cost in self.project_id.general_expense_details_ids:
            values_list.append((0,0,{'item':cost.item,
                                     'quantity':1,
            'rate':cost.rate}))
        self.expense_line_ids = values_list



    name = fields.Char('Name')
    date = fields.Date('Date', default=lambda self: fields.datetime.now())
    employee_id = fields.Many2one('hr.employee', 'Supervisor')

    location_ids = fields.Many2one('stock.location', 'Site', domain=[('usage', '=', 'internal')])
    line_ids = fields.One2many('labour.activities.sheet', 'report_id', 'Lines')
    expense_line_ids = fields.One2many('partner.daily.statement.expense', 'report_id', 'General Expenses')


    state = fields.Selection(
        [('draft', 'Draft'), ('request',"Prepared"),('confirmed', 'Confirmed By PM'), ('approved', 'Checked By Planning'), ('checked', 'Approved By GM'),
         ('cancelled', 'Cancelled')], default='draft')
    received_ids = fields.One2many('daily.statement.item.received', 'received_id', 'Receptions')


    approved_by = fields.Many2one('res.users', 'Approved By')
    approved_sign = fields.Binary('Sign')
    checked_by = fields.Many2one('res.users', 'Checked By')
    checked_sign = fields.Binary('Sign')

    operator_daily_stmts = fields.One2many('operator.daily.statement', 'operator_id')

    work_estimation_daily_ids = fields.One2many('work.estimation.daily.work', 'line_id', "Work estimation")
    project_id = fields.Many2one('project.project', string="Project", required='True')
    material_issue_slip_ids = fields.One2many('material.issue.slip.line','partner_daily_statement_id',"material issue line")

    @api.multi
    def action_compute_manpower_estimation(self):
        for rec in self:
            labour_activities = self.env['labour.activities.sheet'].search([('supervisor_id','=',rec.employee_id.id),('date','=',rec.date),('project_id','=',rec.project_id.id)])
            material_issue_slip = self.env['material.issue.slip.line'].search([('employee_id','=',rec.employee_id.id),('date_export','=',rec.date),('project_id_export','=',rec.project_id.id)])

            for labour in labour_activities:
                labour.write({'report_id':rec.id})
            for mate in material_issue_slip:
                mate.write({'partner_daily_statement_id':rec.id})

    @api.multi
    def action_compute_machinery_estimation(self):
        for rec in self:
            machinery_activities = self.env['driver.daily.statement'].search(
                [ ('date', '=', rec.date),
                 ('project_id', '=', rec.project_id.id)])
            machinery_list = []
            print "hhhhhhhhhhhhhhhhhhhhhhh",machinery_activities
            for labour in machinery_activities:
                if labour.vehicle_no:
                    machinery_list.append((0,0,{'machinery_id':labour.vehicle_no.id,
                                                'start_reading':labour.start_km,
                                                'end_reading':labour.actual_close_km,
                                                'breakdown_hours':labour.bd_hrs}))
                if labour.rent_vehicle_id:
                    machinery_list.append((0, 0, {'machinery_id': labour.rent_vehicle_id.id,
                                                  'start_reading': labour.start_km,
                                                  'end_reading': labour.actual_close_km,
                                                  'breakdown_hours': labour.bd_hrs}))
            if not rec.operator_daily_stmts:
                rec.write({'operator_daily_stmts':machinery_list})


    @api.multi
    def set_draft(self):
        self.state = 'draft'

    @api.multi
    def button_prepare(self):
        self.state = 'request'

    @api.multi
    def cancel_entry(self):
        self.state = 'cancelled'

    @api.multi
    def check_entry(self):
        employee = self.env['hr.employee'].search([('id', '=', 1)])
        self.checked_by = self.env.user.id
        self.action_compute_manpower_estimation()
        self.action_compute_machinery_estimation()
        self.checked_sign = self.env.user.employee_id.sign if self.env.user.id != 1 else employee.sign
        self.state = 'checked'



    @api.multi
    def action_confirm(self):
        self.action_compute_manpower_estimation()
        self.action_compute_machinery_estimation()
        self.state = 'confirmed'



    @api.multi
    def approve_entry(self):
        move_line = self.env['account.move.line']
        move = self.env['account.move']



        for rec in self.work_estimation_daily_ids:
            work_estimation = self.env['work.estimation'].search([('project_id','=',self.project_id.id),('category_id','=',rec.category_id.id)])
            if not work_estimation:
                work_estimation = self.env['work.estimation'].create({'project_id':self.project_id.id,
                                                                      'category_id':rec.category_id.id,
                                                                      'date_start':self.date,
                                                                      'completion_date':self.date,

                                                                      'employee_id':self.employee_id.id,

                                                                      })
            if work_estimation:
                work_estimation.write({'completion_date':self.date})

            values={'date':self.date,
                    'name':rec.name,
                    'side':rec.side,
                    'chain_from':rec.chain_from,
                    'chain_to':rec.chain_to,
                    'nos_x':rec.nos,

                    'length':rec.length,

                    'breadth':rec.breadth,

                    'depth':rec.depth,
                    'line_id':work_estimation.id,
                    }
            self.env['work.estimation.line'].create(values)

            if rec.contractor_id:
                work_order = self.env['work.order'].search(
                    [('partner_id', '=', rec.contractor_id.id), ('project_id', '=', self.project_id.id),
                     ('state', '=', 'start')])
                work_order_payment = self.env['work.order.payment'].search([('partner_id','=',rec.contractor_id.id),('project_id','=',self.project_id.id),('state','=','draft')])
                if not work_order_payment:
                    work_order_payment = self.env['work.order.payment'].create({'partner_id':rec.contractor_id.id,
                                                                                'project_id':self.project_id.id,

                                                                                })

                if work_order_payment:
                    for work in work_order.order_lines:
                        if rec.category_id.id == work.category_id.id:
                            work_line = self.env['work.order.line.payment'].search([('category','=',rec.category_id.id),('line_id','=',work_order_payment.id)])
                            if not work_line:
                                work_line =self.env['work.order.line.payment'].create({
                                                                            'category':rec.category_id.id,
                                                                            'unit':work.uom_id.id,
                                                                            'rate':work.rate,
                                                                            'line_id':work_order_payment.id,
                                                                            })

                            self.env['detailed.workorder.line'].create({'name':work.item_work_id.id,
                                'side':rec.side,
                                'chain_from':rec.chain_from,
                                'chain_to':rec.chain_to,
                                'nos_x':rec.nos,

                                'length':rec.length,

                                'breadth':rec.breadth,

                                'depth':rec.depth,
                                'detail_id':work_line.id,
                                })

        self.action_compute_manpower_estimation()
        self.action_compute_machinery_estimation()
        self.state = 'approved'
        employee = self.env['hr.employee'].search([('id', '=', 1)])
        self.approved_by = self.env.user.id
        self.approved_sign = self.env.user.employee_id.sign if self.env.user.id != 1 else employee.sign

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('partner.daily.statement')
        result = super(PartnerDailyStatement, self).create(vals)
        return result

    @api.multi
    def write(self, vals):
        if vals.get('location_ids'):
            latest = self.env['partner.daily.statement'].search([('employee_id', '=', self.employee_id.id)],
                                                                order='date desc', limit=1)
            if latest.id != self.id:
                self.sudo().employee_id.current_location_id = latest.location_ids.id
            if latest.id == self.id:
                self.sudo().employee_id.current_location_id = vals.get('location_ids')
        result = super(PartnerDailyStatement, self).write(vals)
        return result



class next_day_supervisor(models.Model):
    _name = "next.day.supervisor"

    @api.onchange('project_task_id')
    def onchange_project_task(self):
        list_task = []
        list_details = []
        for pt in self.env['project.task'].search([('project_id.location_id', '=', self.statement_id.location_ids.id)]):
            for tl in pt.task_line:
                list_task.append(tl.id)
                for dl in tl.detailed_ids:
                    list_details.append(dl.id)

        return {'domain': {'project_task_id': [('id', 'in', list_task)], 'details_id': [('id', 'in', list_details)]}}

    statement_id = fields.Many2one('partner.daily.statement', 'Supervisor Statement')
    project_task_id = fields.Many2one('project.task.line', 'Project Task')
    details_id = fields.Many2one('detailed.estimation.line', 'Details Of Work')







class PartnerDailyStatementExpense(models.Model):
    _name = 'partner.daily.statement.expense'

    @api.multi
    @api.depends('quantity', 'rate')
    def compute_qty(self):
        for rec in self:
            rec.total = rec.quantity * rec.rate

    date = fields.Date("Date", default=lambda self: fields.datetime.now())
    quantity = fields.Float('Quantity')
    total = fields.Float('Total', compute='compute_qty', stroe=True)
    item = fields.Selection([('rent', "Rent"),
                             ('bank_guarantee', "Bank Guarantee Charges"),
                             ('survey', "Survey Expenses"),
                             ('general', "General Expenses")], "Category")
    rate = fields.Float('Rate')
    unit_id = fields.Many2one('product.uom', "Unit")
    vr_no = fields.Char(String="VR NO")
    payment = fields.Float('Payment')
    remarks = fields.Text('Remarks')
    project_id = fields.Many2one('project.project', "Project")
    report_id = fields.Many2one('partner.daily.statement', 'Report')


class OperatorDailyStatement(models.Model):
    _name = 'operator.daily.statement'

    operator_id = fields.Many2one('partner.daily.statement')
    category_id = fields.Many2one('task.category',"BOQ No")
    employee_id = fields.Many2one('hr.employee', string="Operator", )
    machinery_id = fields.Many2one('fleet.vehicle', string="Machinery",)
    unit_id = fields.Many2one('product.uom',"Unit")
    start_reading = fields.Float('Start Reading')
    end_reading = fields.Float('End Reading')
    working_hours = fields.Float('Working Hours', compute="compute_operator_details")
    breakdown_hours = fields.Float("Breakdown/IDLE Hours")
    quantity = fields.Float('Production(Area or Qty', default="1")
    remarks = fields.Char("Remarks")


    @api.multi
    @api.depends('start_reading', 'end_reading')
    def compute_operator_details(self):
        for record in self:
            record.working_hours = round((record.end_reading - record.start_reading), 2)






class NextDayWork(models.Model):
    _name = 'next.day.work'

    name = fields.Char('Name')


class NextDayWorkItems(models.Model):
    _name = 'next.day.work.items'

    product_id = fields.Many2one('product.product')
    uom_id = fields.Many2one('product.uom', 'Item')
    qty = fields.Float('Qty')


class DailyStatementItem(models.Model):
    _name = 'daily.statement.item'

    @api.constrains('name')
    def _check_duplicate_name(self):
        names = self.search([])
        for c in names:
            if self.id != c.id:
                if self.name.lower() == c.name.lower() or self.name.lower().replace(" ", "") == c.name.lower().replace(
                        " ", ""):
                    raise osv.except_osv(_('Error!'), _('Error: name must be unique'))
            else:
                pass

    name = fields.Char('Name')




class DailyStatementItemReceived(models.Model):
    _name = 'daily.statement.item.received'

    @api.onchange('product_id')
    def onchange_product_id(self):
        for rec in self:
            if rec.product_id:

                date = datetime.strptime(rec.received_id.date, "%Y-%m-%d").strftime("%Y-%m-%d 00:00:00")
                to_date = datetime.strptime(rec.received_id.date, "%Y-%m-%d").strftime("%Y-%m-%d 23:59:59")
                issue_details = self.env['material.issue.slip.line'].search([('item_id','=',rec.product_id.id),
                                                                             ('date_export','>=',date),('date_export','<=',to_date),
                                                                             ('project_id_export','=',rec.received_id.project_id.id),
                                                                             ('employee_id','=',rec.received_id.employee_id.id),
                                                                              ])
                qty = 0
                for issue in issue_details:
                    qty += issue.req_qty
                rec.qty = qty

                opening_balance = self.env['material.issue.slip.line'].search([('item_id','=',rec.product_id.id),
                                                                             ('date_export','<',rec.received_id.date),
                                                                               ('project_id_export','=',rec.received_id.project_id.id),
                                                                               ('employee_id','=',rec.received_id.employee_id.id),
                                                                              ])
                qty = 0
                for opening in opening_balance:
                    qty += opening.req_qty

                consumption = self.search([('product_id','=',rec.product_id.id)])
                for consu in consumption:
                    if consu.received_id.project_id.id == rec.received_id.project_id.id and rec.received_id.employee_id.id == consu.received_id.employee_id.id and consu.received_id.date < rec.received_id.date:
                        qty -= consu.product_qty
                rec.opening_balance = qty
                rec.unit_id = rec.product_id.uom_id.id
                rec.rate = rec.product_id.standard_price

    @api.depends('opening_balance','qty')
    def compute_total_qty(self):
        for rec in self:
            rec.total = rec.opening_balance + rec.qty

    @api.depends('product_qty')
    def compute_bal_qty(self):
        for rec in self:
            rec.balance_qty = rec.total - rec.product_qty

    category_id = fields.Many2one('task.category',"Category")
    product_id = fields.Many2one('product.product', 'Material')
    unit_id = fields.Many2one('product.uom',"Unit")
    name = fields.Char('Chainage')
    rate = fields.Float("Rate")
    opening_balance = fields.Float("Opening Balance at Site (Qty)")
    qty = fields.Float('Received Qty from Store(Qty)')
    total = fields.Float('Total(Qty)',compute='compute_total_qty',store=True)
    product_qty = fields.Float("Consumption at Site (Qty)")
    balance_qty = fields.Float('Balance Qty st Site',compute='compute_bal_qty',store=True)
    received_id = fields.Many2one('partner.daily.statement')



class WorkEstimationDailyWork(models.Model):
    _name = 'work.estimation.daily.work'

    @api.constrains('chain_from','chain_to')
    def check_chain_from_to(self):
        for rec in self:
            daily_work = self.search([('chain_from','=',rec.chain_from),('chain_to','=',rec.chain_to)])
            for daily in daily_work:
                print  "qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq",daily.line_id.date
                if daily.line_id.project_id.id == rec.line_id.project_id.id and daily.line_id.date != rec.line_id.date:

                    user_list = []
                    for user in self.env['res.users'].search([]):
                        if user.has_group('hiworth_construction.group_dpr_checking'):
                            user_list.append(user.id)
                    session_user = []
                    session_user.extend(user_list)
                    session_user.append(self.env.user.id)

                    for us in user_list:

                        print "gggggggggggggggggggggggggggg",session_user

                        session = self.env['im_chat.session'].search([('user_ids', 'in', session_user)])
                        if not session:
                            session = self.env['im_chat.session'].create({'user_ids': [(6, 0, session_user)]})
                        print "sessionnnnnnnnnnnnnnnnnnnnnnnnnnnn",session
                        self.env['im_chat.message'].create({'from_id': self.env.user.id,
                                                            'to_is': us,
                                                            'to_id': session.id,
                                                            'message': 'Chainage From and To duplicate in %s and %s' % (daily.line_id.date,rec.line_id.date)})


    @api.onchange('category_id')
    def onchnage_category_id(self):
        for rec in self:
            category_list = []
            for lin in rec.line_id.project_id.task_ids:
                for tas in lin.task_line:
                    category_list.append(tas.category.id)

            for line in rec.line_id.project_id.task_ids:
                for task in line.task_line:
                    if task.category.id == rec.category_id.id:
                        rec.name = task.name.name
            return {'domain':{'category_id':[('id','in',category_list)]}}



    @api.onchange('contractor_id')
    def onchnage_contractor_id(self):
        for rec in self:
            work_order = self.env['work.order'].search([('project_id','=',rec.line_id.project_id.id),('partner_id','=',rec.contractor_id.id),('state','=','start')])
            for line in work_order:
                for task in line.order_lines:
                    if task.category_id.id == rec.category_id.id:
                        rec.name = task.item_work_id.name

    @api.one
    @api.depends('nos', 'length', 'breadth', 'depth')
    def _get_qty(self):
       for rec in self:
            rec.qty = rec.nos * rec.length * rec.breadth * rec.depth

    category_id = fields.Many2one('task.category',"Category")
    name = fields.Char("Item Description")
    chain_from = fields.Char('Chainage From')
    chain_to = fields.Char('Chainage To')
    side = fields.Selection([('r', 'RHS'), ('l', 'LHS'), ('bs', 'BS')], string="Side")
    unit_id = fields.Many2one('product.uom',"Unit")
    nos = fields.Float("Nos",default=1)
    length = fields.Float(string="Length(m)",default=1)
    breadth = fields.Float(string="Breadth(m)",default=1)
    depth = fields.Float(string="Depth(m)",default=1)
    qty = fields.Float(string="Qty(cum)", compute='_get_qty')
    contractor_id = fields.Many2one('res.partner',domain=[('contractor','=',True)],string="Contractor")
    remarks = fields.Char("Remarks")
    line_id = fields.Many2one('partner.daily.statement',"Supervisor")
    location_id = fields.Many2one('stock.location',"Location")

