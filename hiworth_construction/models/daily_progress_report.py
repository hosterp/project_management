from openerp import fields, models, api
from openerp.osv import fields as old_fields, osv, expression
import time
from datetime import datetime
import datetime
from openerp.exceptions import except_orm, Warning, RedirectWarning
#from openerp.osv import fields
from openerp import tools
from openerp.tools import float_compare
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp
from pychart.arrow import default
from cookielib import vals_sorted_by_key
# from pygments.lexer import _default_analyse
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, DATETIME_FORMATS_MAP
# from openerp.osv import osv
from openerp import SUPERUSER_ID

from lxml import etree


class daily_progress_report(models.Model):
    _name = 'daily.progress.report'
    _order = 'date desc'
    
    
    @api.onchange('employee_id')
    def onchange_employee_id(self):
        for rec in self:
           if rec.employee_id and rec.date:
               rec.name = rec.employee_id.name + str(rec.date)
    
    name = fields.Char('Name')
    employee_id = fields.Many2one('hr.employee',string="Employee")
    date = fields.Date('Date')
    project_id = fields.Many2one('project.project',string="Project")
    remark =fields.Text(string="Remarks")
    dpr_line_ids = fields.One2many('daily.progress.report.line','report_id')
#
    
    _defaults = {
        'date': date.today()
        }
    
class daily_progress_report_line(models.Model):
    _name = 'daily.progress.report.line'
    
    @api.onchange('item_work_id')
    def onchange_item_id(self):
        for rec in self:
            master_paln_ids = self.env['master.data.estimation'].search([('item_work_id','=',rec.item_work_id.id),('project_id','=',rec.report_id.project_id.id)])
            for master_plan in master_paln_ids:
                    if master_plan.item_work_id.id == rec.item_work_id.id:
                        rec.no_of_labours = master_plan.no_of_labours
                        rec.veh_categ_id = [(6,0,master_plan.veh_categ_id.ids)]
                       
                
    name = fields.Char('Name')
   
    report_id = fields.Many2one('daily.progress.report', 'Report')
    item_work_id = fields.Many2one('item.of.work', string="Item of Work")
    veh_categ_id = fields.Many2many('vehicle.category.type', string='Machinery')
    product_id = fields.Many2one('product.product', string="Item")
    no_of_labours = fields.Float(string="No of Labours")
    present_labour = fields.Float(string="No of Present Labour")
    machinery = fields.Float(String="No of Present machinery")
    prsent_veh_categ_id = fields.Many2many('vehicle.category.type', string='Machinery')
    remarks = fields.Char(string="Remarks")
   


class daily_usage_report(models.Model):
    _name = 'daily.usage.report'



    READONLY_STATES = {
        'approved': [('readonly', True)],
    }

    name = fields.Char('Name',  states=READONLY_STATES)
    date = fields.Date('Date',  states=READONLY_STATES)
    journal_id = fields.Many2one('account.journal','Journal',  states=READONLY_STATES, domain=[('type','in',['cash','bank','general'])])
    line_ids = fields.One2many('daily.usage.report.line', 'report_id', 'Lines',  states=READONLY_STATES)
    user_id = fields.Many2one('res.users', 'User', default=lambda self: self.env.user)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('approved', 'Approved'),
        ],default='draft')


    _defaults = {
        'date': fields.datetime.now(),

    }

    @api.multi
    def action_approve(self):
        self.ensure_one()
        move = self.env['account.move']
        move_line = self.env['account.move.line']
        for lines in self.line_ids:
            values = {
                'journal_id': lines.journal_id.id,
                'date': self.date,
                }
            move_id = move.create(values)
            values2 = {
                    'account_id': lines.account_id.id,
                    'name': 'Stock Movement' + ' ' + lines.product_id.name,
                    'debit': 0,
                    'credit': lines.inventory_value,
                    'move_id': move_id.id,
                    }
            line_id = move_line.create(values2)
            values3 = {
                    'account_id': lines.exp_account_id.id,
                    'name': 'Stock Movement' + ' ' + lines.product_id.name,
                    'debit': lines.inventory_value,
                    'credit': 0,
                    'move_id': move_id.id,
                    }
            line_id = move_line.create(values3)
            move_id.button_validate()

            estimation = self.env['project.task.estimation'].search([('task_id','=',lines.task_id.id),('pro_id','=',lines.product_id.id)])
            if estimation:
                estimation.qty_used = estimation.qty_used+lines.qty
        consumed_product_location = self.env.ref("hiworth_construction.stock_location_product_consumption").id
        move = self.env['stock.move']
        for transfer in self.line_ids:
            move_id = move.create({
                'name': transfer.product_id.name,
                'product_id': transfer.product_id.id,
                'restrict_lot_id': False,
                'product_uom_qty': transfer.qty,
                'product_uom': transfer.uom_id.id,
                'partner_id': self.user_id.partner_id.id,
                'location_id': transfer.location_id.id,
                'location_dest_id': consumed_product_location,
                'picking_id': False,
                'invoice-state': 'none',
                'date': self.date,

            })
            move_id.location_id = transfer.location_id.id
            move_id.action_done()
        self.state = 'approved'



class daily_usage_report_line(models.Model):
    _name = 'daily.usage.report.line'


    @api.multi
    @api.depends('product_id', 'qty', 'price_unit')
    def compute_invemtory_value(self):
        for line in self:
            line.inventory_value = line.qty * line.price_unit

    @api.onchange('product_id')
    def onchange_product(self):
        if self.product_id:
            self.price_unit = self.product_id.standard_price
            self.uom_id = self.product_id.uom_id.id

    @api.onchange('project_id')
    def onchange_report(self):
        if self.report_id:
            self.journal_id = self.report_id.journal_id.id

    name = fields.Char('Name of the work')
    report_id = fields.Many2one('daily.usage.report', 'Report')
    project_id = fields.Many2one('project.project', 'Project')
    task_id = fields.Many2one('project.task', 'Task')
    product_id = fields.Many2one('product.product', 'Product')
    qty = fields.Float('Used Qty')
    uom_id = fields.Many2one('product.uom', 'Uom')
    price_unit = fields.Float('Unit Price')
    account_id = fields.Many2one('account.account', 'Asset Account')
    exp_account_id = fields.Many2one('account.account', 'Expense Account')
    journal_id = fields.Many2one('account.journal', 'Journal')
    inventory_value = fields.Float(compute='compute_invemtory_value', store=True, string="inventory Value")
    location_id = fields.Many2one('stock.location', 'Location')


    @api.model
    def create(self,vals):
        if vals.get('qty') == 0:
            raise osv.except_osv(_('Warning!'),_('Used Qty must be greater than zero'))

        return super(daily_usage_report_line, self).create(vals)