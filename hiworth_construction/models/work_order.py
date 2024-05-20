from openerp import fields, models, api
from openerp.osv import fields as old_fields, osv, expression
import time
from datetime import datetime
import datetime
from openerp.exceptions import except_orm, Warning, ValidationError
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
from unittest.util import _ordered_count
import new

class work_order_line(models.Model):
    _name = 'work.order.line'
    _order = "sequence, id"


    @api.onchange('product_id')
    def onchange_product(self):
        if self.product_id:
            self.uom_id = self.product_id.uom_id.id
            self.rate = self.product_id.standard_price


    @api.multi
    @api.depends('qty', 'rate')
    def _compute_amount(self):
        for line in self:
            line.amount = line.qty * line.rate


    @api.multi
    @api.depends('product_id')
    def _compute_paid_amount(self):
        for line in self:
            # payment =  self.env['work.order.payment'].search([('order_id','=',line.id)])
            line.paid_amount = 0


    # @api.onchange('project_id')
    # def onchange_project_id(self):
    #     for rec in self:
    #         item = []
    #         cate = []
    #         for line in rec.project_id.task_ids:
    #             for task_line in line.task_line:
    #                 item.append(task_line.name.id)
    #                 cate.append(task_line.category.id)
    #         print 'sssssssssssssssss',item
    #         print 'vvvvvvvvvvvvvvvvvv',cate
    #     return {'domain':{'item_work_id':[('id','in',item)],
    #                       'category_id':[('id','in',cate)]}}


    @api.onchange('item_work_id')
    def onchange_category_id(self):
        item = []
        cate = []
        for rec in self:
            if rec.item_work_id:
                for line in rec.work_order_id.project_id.task_ids:
                    for task_line in line.task_line:

                        if task_line.name.id == rec.item_work_id.id:
                            rec.estimated_qty = task_line.qty
                            rec.estimated_rate = task_line.rate
                            rec.uom_id = task_line.unit.id

            project = self.env['project.project'].browse(self._context.get('project_id'))
            for line in project.task_ids:
                for task_line in line.task_line:
                    item.append(task_line.name.id)
                    cate.append(task_line.category.id)
        return {'domain': {'item_work_id': [('id', 'in', item)],
                          }}




    @api.depends('estimated_qty', 'qty')
    def compute_remaining_qty(self):
        for rec in self:
            project = self.env['project.project'].browse(self._context.get('project_id'))
            work_order_line = self.env['work.order.line'].search([('category_id', '=', rec.category_id.id)])
            rec.remaining_qty = rec.estimated_qty - rec.qty
            # for work in work_order_line:
            #     if work.work_order_id.project_id == project:
            #         rec.remaining_qty = work.remaining_qty


    # @api.constrains('qty', 'estimated_qty')
    # def check_constrains_qty(self):
    #     for rec in self:
    #         print "ggggggggggg",rec.qty,rec.estimated_qty
    #         if rec.qty > rec.estimated_qty:
    #             raise ValidationError(_('Quantity Cant exceed Estimated Qty'))


    @api.multi
    @api.depends('amount', 'paid_amount')
    def _compute_balance(self):
        for line in self:
            line.balance = line.amount - line.paid_amount


    name = fields.Char('Name')
    sequence = fields.Integer('Sequence', help="Gives the sequence order when displaying a list of Projects.")
    item_work_id = fields.Many2one('item.of.work', "Item of Work")
    product_id = fields.Many2one('product.product', 'Description')
    rate = fields.Float('Rate')
    qty = fields.Float('Qty')
    remaining_qty = fields.Float('Remaining Qty', compute="compute_remaining_qty")
    category_id = fields.Many2one('task.category', "Category")
    estimated_qty = fields.Float("Estimated Qty", )
    estimated_rate = fields.Float("Estimated Rate",)
    uom_id = fields.Many2one('product.uom', 'Unit', required=True)
    amount = fields.Float(compute='_compute_amount', store=True, string='Amount')
    remarks = fields.Text('Remarks')
    work_order_id = fields.Many2one('work.order', 'Work Order', ondelete='cascade')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('partial', 'Partially Paid'),
        ('paid', 'Paid'),
        ('cancel', 'Cancelled'),
    ], string='Status', readonly=True, default='draft')
    paid_amount = fields.Float(compute='_compute_paid_amount', string="Paid Amount")
    balance = fields.Float(compute='_compute_balance', string="Balance")
    #     payment_id = fields.Many2one('work.order.payment', compute='_def_payment', string='Payment')
    binary_field = fields.Binary('File')
    filename = fields.Char('Filename')
    status = fields.Selection(related='work_order_id.state', strore=True, string="Work Order Status", default='draft')
    project_id = fields.Many2one('project.project', string="Project")


    def _def_payment(self):
        self.payment_id = self.env['work.order.payment'].search([('order_id', '=', self.id)]).id


    @api.multi
    def open_payments(self):
        self.ensure_one()
        # Search for record belonging to the current staff
        record = self.env['work.order.payment'].search([('order_id', '=', self.id)])
        context = self._context.copy()
        # context['default_name'] = self.id
        if record:
            res_id = record[0].id
        else:
            res_id = False
        # Return action to open the form view
        return {
            'name': 'Open Payment',
            'view_type': 'form',
            'view_mode': 'form',
            'views': [(False, 'form')],
            'res_model': 'work.order.payment',
            'view_id': 'form_view_work_order_payment',
            'type': 'ir.actions.act_window',
            'res_id': res_id,
            'context': {'default_order_id': self.id, 'default_name': self.product_id.name, 'default_qty': self.qty,
                        'default_rate': self.rate, 'default_amount': self.amount},
        }


class work_order(models.Model):
    _name = 'work.order'
    _order = "sequence, id"


    @api.multi
    @api.onchange('partner_id')
    def _onchange_partner(self):
        if self.partner_id.id != False:
            self.street = self.partner_id.street
            self.street2 = self.partner_id.street2
            self.post = self.partner_id.post
            self.city = self.partner_id.city
            self.state_id = self.partner_id.state_id
            self.zip = self.partner_id.zip
            self.phone = self.partner_id.phone
            self.mobile = self.partner_id.mobile

    @api.multi
    @api.depends('invoice_ids')
    def _count_invoices(self):
        for line in self:
            line.invoice_count = len(line.invoice_ids)

    READONLY_STATES = {
        'approved': [('readonly', True)],
        'reject': [('readonly', True)],
        'cancel': [('readonly', True)],
        'start': [('readonly', True)],
        'done': [('readonly', True)],
        'paid': [('readonly', True)]
    }

    @api.onchange('item_work_id')
    def onchange_item_work_id(self):
        for rec in self:
            if rec.item_work_id:
                master_data = self.env['master.data.work.order'].search([('item_work_id','=',rec.item_work_id.id)])
                if master_data:
                    rec.scope = master_data.scope
                    rec.terms = master_data.terms

    name = fields.Char('Name', states=READONLY_STATES)
    sequence = fields.Integer('Sequence', help="Gives the sequence order when displaying a list of Projects.")
#     index = fields.Integer(compute='_compute_index')
    date = fields.Date('Date', states=READONLY_STATES)
    project_id = fields.Many2one('project.project', states=READONLY_STATES)
    item_work_id = fields.Many2one('item.of.work', string="Name of work")
    partner_id = fields.Many2one('res.partner', states=READONLY_STATES)
    street = fields.Char('Street', states=READONLY_STATES)
    street2 = fields.Char('Street2', states=READONLY_STATES)
    post = fields.Char('Post', states=READONLY_STATES)
    city = fields.Char('City', states=READONLY_STATES)
    state_id = fields.Many2one('res.country.state', 'State', states=READONLY_STATES)
    zip = fields.Char('zip', states=READONLY_STATES)
    phone = fields.Char('Phone', states=READONLY_STATES)
    mobile = fields.Char('Mobile', states=READONLY_STATES)
    reference = fields.Text('Reference', states=READONLY_STATES)
    state = fields.Selection([('draft', 'Waiting For Approval'),
                                   ('approved', 'Approved'),
                                   ('reject', 'Rejected'),
                                   ('start', 'In Progress'),
                                   ('done', 'Completed'),
                                   ('paid', 'Paid'),
                                   ('cancel', 'Cancelled')
                                   ], 'Status', readonly=True, select=True, copy=False, default='draft')
    part1 = fields.Html('Part1', states=READONLY_STATES)
#     item_ids = fields.One2many()
    scope = fields.Html('scope', states=READONLY_STATES)
    terms = fields.Html('Terms', states=READONLY_STATES)
    order_lines = fields.One2many('work.order.line', 'work_order_id', 'Lines')
    invoice_ids = fields.One2many('hiworth.invoice', 'work_order_id', 'Invoice')
    invoice_count = fields.Integer(compute='_count_invoices', string='Invoice Nos')
    # action_compute = fields.Char(compute='_refresh_payment_lines')
    _defaults = {
        'date': fields.Date.today(),
        'sequence': 10,
        }


    @api.model
    def create(self,vals):
        now = datetime.datetime.now()
        nos = self.env['ir.sequence'].get('nos')
#         print 'teay===================', now.year,nos
        vals['name'] = "BIDPL/WO/" + str(nos)+"/" + str(now.year)
        return super(work_order, self).create(vals)

    @api.multi
    def action_approve(self):
        for line in self:
            line.state = 'approved'

    @api.multi
    def action_reject(self):
        for line in self:
            line.state = 'reject'

    @api.multi
    def action_cancel(self):
        for line in self:
            line.state = 'cancel'

    @api.multi
    def action_draft(self):
        for line in self:
            line.state = 'draft'

    @api.multi
    def action_start(self):
        for line in self:
            line.state = 'start'

    @api.multi
    def action_done(self):
        for line in self:
            line.state = 'done'

    @api.multi
    def action_paid(self):
        for line in self:
            line.state = 'paid'

    @api.multi
    def _refresh_payment_lines(self):
        for line in self.order_lines:
            payment =  self.env['work.order.payment'].search([('order_id','=',line.id)])
            if len(payment) == 0:
                values = {'order_id':line.id,
                          'name':line.product_id.name,
                          'qty':line.qty,
                          'rate':line.rate,
                          'amount':line.amount}
                payment_id = self.env['work.order.payment'].create(values)
                payment_id.generate_payment_lines()
            if payment.id:
                payment.generate_payment_lines()
        self.action_compute = ""



class work_order_payment(models.Model):
    _name = 'work.order.payment'

    @api.depends('qty','rate')
    def _compute_amount(self):
        for line in self:
            line.amount = line.qty*line.rate

    @api.depends('line_ids')
    def _compute_balance(self):
        for line in self:
            total = 0.0
            for lines in line.line_ids:
                total += lines.amount
            line.balance = line.amount - total

    @api.multi
    @api.depends('line_ids')
    def _compute_paid_amount(self):
        for line in self:
            for lines in line.line_ids:
                line.paid_amount += lines.amount

    name = fields.Char('Name')
    qty = fields.Float('Qty')
    rate = fields.Float('Rate')
    amount = fields.Float(compute='_compute_amount', store=True, string="Amount")
    balance = fields.Float(compute='_compute_balance', store=True, string='Balance')
    line_ids = fields.One2many('work.order.payment.line', 'order_id', 'Lines')
    order_id = fields.Many2one('work.order.line', 'Order')
    work_order_id = fields.Many2one('work.order', 'Work Order')
    paid_amount = fields.Float(compute='_compute_paid_amount', string="Paid Amount")

    @api.multi
    def generate_payment_lines(self):
        self.ensure_one()
        #invoices = self.env['hiworth.invoice.line'].search([('product_id','=', self.order_id.product_id.id),('work_order_id','=', self.order_id.work_order_id.id),('state','=','paid')])
        for line in self.line_ids:
            if line.invoice_id:
                line.unlink()

        #

class work_order_payment_line(models.Model):
    _name = 'work.order.payment.line'
    _order = 'date '

    name = fields.Char('Name')
    date = fields.Date('Date')
    amount = fields.Float('Amount')
    order_id = fields.Many2one('work.order.payment', 'Work Order')
    invoice_id = fields.Many2one('hiworth.invoice', 'Invoice')

    
class MasterDataWorkOrder(models.Model):
    _name = 'master.data.work.order'
   
   
    item_work_id = fields.Many2one('item.of.work',string="Name of work")
    scope = fields.Html('scope')
    terms = fields.Html('Terms')
   
    
    
    
    

    