from openerp import fields, models, api
from datetime import datetime
from openerp.exceptions import Warning as UserError
from openerp.osv import osv
from openerp.tools.translate import _
from dateutil import relativedelta
from openerp.exceptions import except_orm, ValidationError


class DebitNoteSupplier(models.Model):
    _name = 'debit.note.supplier'
    _order = 'date desc'
    
    
    @api.model
    def create(self, vals):
        
        if vals.get('name', False) == False:
            project = self.env['project.project'].search([('location_id','=',vals['location_id'])],limit=1)
            project.dbn_no += 1
            vals.update({'name': 'DBN-' + str(project.dbn_no).zfill(3) + '/'+str(datetime.now().year)})
        res = super(DebitNoteSupplier, self).create(vals)
        return res
    
    
    @api.depends('debit_note_supplier_lines_ids')
    def compute_items_list(self):
        for rec in self:
            items=''
            for debitnote_supplier in rec.debit_note_supplier_lines_ids:
                items += debitnote_supplier.item_id.name + ','
            rec.items_list = items
            
    @api.depends('debit_note_supplier_lines_ids')
    def compute_total_quantity(self):
        for rec in self:
            quantity = 0
            for debitnote_supplier in rec.debit_note_supplier_lines_ids:
                quantity += debitnote_supplier.total
            rec.total_quantity = quantity
    
    
    name = fields.Char('DBN NO')
    date = fields.Date('Date', default=datetime.today())
    employee_id = fields.Many2one('res.partner', 'User')
    source_location_id = fields.Many2one('stock.location',"Source Location")
    project_id = fields.Many2one('project.project',"Project")
    location_id = fields.Many2one('stock.location', "Location")
    debit_note_supplier_lines_ids = fields.One2many('debit.note.supplier.line', 'debit_note_supplier_id',
                                                    string="Item List")
    #state = fields.Selection([('draft', 'Draft'),
                              #('request', 'Request'),
                             #('receive', 'Received')], default='draft', String="Status")
    is_material_request = fields.Boolean('Material Request',default=False)
    material_requst_id = fields.Many2one('material.issue.slip',"Material Request")
    items_list = fields.Char("Items",compute='compute_items_list')
    total_quantity = fields.Float("Total Quantity", compute='compute_total_quantity')
    
    


class DebitNoteSupplierLine(models.Model):
    _name = 'debit.note.supplier.line'
    
    @api.depends('quantity','rate')
    def compute_amount(self):
        for rec in self:
            rec.total = rec.rate * rec.quantity
    @api.onchange('date')
    def date_onchange(self):
        for rec in self:
            if rec.debit_note_supplier_id.date:
                rec.date = rec.debit_note_supplier_id.date
            
    date = fields.Date('Date',default=lambda self: fields.datetime.now())
    item_id = fields.Many2one('product.product', string="Material Code")
    quantity = fields.Float(string="Quantity")
    unit_id = fields.Many2one('product.uom', string="Unit")
    desc = fields.Char(string="Material Name")
    rate = fields.Float(string="Rate")
    total = fields.Float(string="Total",compute='compute_amount')
    debit_note_supplier_id = fields.Many2one('debit.note.supplier', string="Material Issue Slip")
    grr_number = fields.Many2one('goods.recieve.report', string="GRR No.")
    remarks = fields.Char(string='Remarks')
    name = fields.Char(string='DBN NO',related ="debit_note_supplier_id.name")
    date_export=  fields.Date('Date', related ="debit_note_supplier_id.date")
    employee_id = fields.Many2one(string = "User", related ="debit_note_supplier_id.employee_id")
    location_id = fields.Many2one(string = "Project Store", related ="debit_note_supplier_id.location_id")
    source_location_id = fields.Many2one(string = "Chainage", related ="debit_note_supplier_id.source_location_id")