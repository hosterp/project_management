from openerp.exceptions import except_orm, ValidationError
#from openerp.tools import DEFAULT_SERVER_DateTIME_FORMAT
from openerp import models, fields, api, _
from openerp import workflow
import time
import datetime
#from datetime import datetime, timedelta
from datetime import date
#from openerp.osv import fields, osv
from openerp.tools.translate import _
#from openerp import SUPERUSER_ID
import openerp.addons.decimal_precision as dp
from openerp.osv import  osv
from datetime import timedelta
import re



class bank_emi_lines(models.Model):
    _name = 'bank.emi.lines'
    
    
    name = fields.Char('Name', size=64)
    date = fields.Date('Date')
    payment_mode = fields.Selection([('cash','Cash'),('bank','Bank'),('cheque','Cheque')], 'Mode Of Payment', select=True)
    reference = fields.Text('Reference')
    amount = fields.Float('Amount', Default=0.0)
    emi_line = fields.Many2one('fleet.vehicle', 'EMI Payment Details')
    receipt_no = fields.Char('Receipt No', size=64)
    
    
class bank_emi_lines(models.Model):
    _name = 'agent.ins.lines'
    
    
    name = fields.Char('Name', size=64)
    date = fields.Date('Date')
    payment_mode = fields.Selection([('cash','Cash'),('bank','Bank'),('cheque','Cheque')], 'Mode Of Payment', select=True)
    reference = fields.Text('Reference')
    amount = fields.Float('Amount', Default=0.0)
    ins_line = fields.Many2one('fleet.vehicle', 'Insurance Payment Details')
    receipt_no = fields.Char('Receipt No', size=64)
    
    
    
class puc_lines(models.Model):
    _name = 'puc.lines'
    
    
    name = fields.Char('Name', size=64)
    date = fields.Date('Date')
    exp_date = fields.Date('Expiry Date')
    reference = fields.Text('Reference')
    amount = fields.Float('Amount', Default=0.0)
    puc_line = fields.Many2one('fleet.vehicle', 'Insurance Payment Details')
    receipt_no = fields.Char('Receipt No', size=64)
    
    

class fleet_vehicle(models.Model):
    _inherit = 'fleet.vehicle'



    def _generate_virtual_location(self, cr, uid, truck, vehicle_ok, trailer_ok, context): 
        pass
    
    
    # def onchange_basic_odometer(self, cr, uid, ids, counter_basic, context=None):
    #     data={}
    #     if counter_basic:
    #         data['odometer'] = counter_basic
    #     return {'value' : data}

    @api.constrains('license_plate')
    def check_license_plate_format(self):
        for rec in self:

            phoneNumRegex = re.compile(r'[A-Z]{2}[-][0-9]{1,2}[-]([A-Z]{1,2}[-][0-9]{4})')
            plate = re.compile(r'[A-Z]{2}[-][0-9]{1,2}[-][0-9]+}')
            if rec.vehicle_ok or rec.rent_vehicle:
                mo = phoneNumRegex.search(rec.license_plate)
                m = plate.search(rec.license_plate)
                if not mo :
                    raise except_orm(_('Warning'),
                                     _('Please Enter REG No in this format KL-01-XX-XXXX or KL-01-X-XXXX'))




    is_rent_mach = fields.Boolean(string="Is Rent Machinery")
    gasoil_id = fields.Many2one('product.product', 'Fuel', required=False, domain=[('fuel_ok','=','True')])
    emi_no = fields.Char('EMI No', size=64)
    bank_id = fields.Many2one('res.bank','Bank Details')
    emi_lines =  fields.One2many('bank.emi.lines','emi_line', 'EMI Payment Details')
    emi_start_date = fields.Date('Start Date')
    last_paid_date = fields.Date('Last Date Paid')
    next_payment_date = fields.Date('Next Payment Date')
    total_due = fields.Float('Total Due', Default=0.0)
    total_paid = fields.Float('Total Paid', Default=0.0)
    balance_due = fields.Float('Balance', Default=0.0)    
    ############ insurance Details
    ins_no = fields.Char('EMI No', size=64)
    agent_id = fields.Many2one('res.partner','Agent Details')
    ins_lines = fields.One2many('agent.ins.lines','ins_line', 'Insurance Payment Details')
    last_paid_date_ins = fields.Date('Last Date Paid')
    next_payment_date_ins = fields.Date('Next Payment Date')  
    puc_lines = fields.One2many('puc.lines','puc_line', 'PUC Details')
    vehilce_old_odometer = fields.Float('Vehicle Old Old OdoMeter', readonly=False)     
    mileage = fields.Float('Current Reading',)
    odometer = fields.Float( string='Last Odometer', help='Odometer measure of the vehicle at this moment')
    rate_per_km = fields.Float('Rate Per Km')
    vehicle_under  =fields.Many2one('res.partner','Vehicle Under')
    per_day_rent = fields.Float('Rent Per Day')
    rent_vehicle = fields.Boolean(default=False)
    machinery = fields.Boolean(default=False)
    brand_id = fields.Many2one('fleet.vehicle.model.brand', 'Brand')
    vehicle_ok = fields.Boolean('Vehicle')
    model_id = fields.Many2one('fleet.vehicle.model', 'Model', required=False)
    name = fields.Char(compute="_get_tms_vehicle_name", string='Nom', store=True)
    capacity = fields.Float('Capacity')
    chase_no = fields.Char("Chase No")
    engine_no = fields.Char("Engine No")
    sl_no = fields.Char("Sl No")
    vehicle_categ_id = fields.Many2one('vehicle.category.type', string="Vehicle Type")
    expected_working = fields.Float("Expected Working Hour")
    tanker_bool = fields.Boolean("Tanker",default=False)
    fleet_receipt_details_ids = fields.One2many('fleet.receipt.details','name',"Fleet Receipt Details")
    fleet_issue_details_ids = fields.One2many('fleet.issue.details', 'name', "Fleet Issue Details")
    location_id = fields.Many2one('stock.location',"Tanker Location")
    permit_date = fields.Date("Permit Date")
    insurance_date = fields.Date("Insurance Date")
    road_tax_date = fields.Date("Road Tax Date")
    fitness_date = fields.Date("Fitness Date")
    pollution_date = fields.Date("Pollution Date")
    fleet_no = fields.Char("Fleet No")
    insured_by = fields.Many2one('vehicle.insurer',"Insured By")
    premium_amt = fields.Float("Premium Amount")
    state = fields.Selection([('draft','Draft'),('confirm','Confirm'),
                              ('approved','Authorized')],default='draft')
    year_of_manu = fields.Char("Year of Manufactuer")
    vehicle_owner = fields.Many2one('vehicle.owner',"Vehicle Owner")
    vehicle_rate_per_km_ids = fields.One2many('vehicle.rate.per.km','vehicle_id',"Vehicle Rate Per Km Details")
    purchase_value = fields.Float("Purchase Value")
    other = fields.Boolean("Other")
    rent_other = fields.Boolean("Rent Other")

    @api.multi
    def action_confirm(self):
        for rec in self:
            rec.state = 'confirm'

    @api.multi
    def action_approve(self):
        for rec in self:
            rec.state = 'approved'

    # eicher_categ = fields.Boolean('Eicher', compute="_compute_veh_category", store=True)
    # taurus_categ = fields.Boolean('Taurus', compute="_compute_veh_category",  store=True)
    
    ############################# Vehicle status ###################################

    # from_date_status = fields.Date('From Date') 
    # to_date_status = fields.Date('To Date')






    # @api.multi
    # @api.depends('vehicle_categ_id')
    # def _compute_veh_category(self):
    #     for record in self:
    #         if record.vehicle_categ_id.id == :
    #             record.eicher_categ = True
    #         elif record.vehicle_categ_id.id == self.env.ref('hiworth_tms.vehicle_category_taurus').id:
    #             record.taurus_categ = True
    #         else:
    #             pass





    @api.depends('license_plate')
    def _get_tms_vehicle_name(self):
        for record in self:

            record.name = record.license_plate







    @api.constrains('name')
    def _check_duplicate_name(self):
        names = self.search([])
        for c in names:
            if self.id != c.id:
                if self.name and c.name:
                    if self.name.lower() == c.name.lower() or self.name.lower().replace(" ", "") == c.name.lower().replace(" ", ""):
                        raise osv.except_osv(_('Error!'), _('Error: vehicle name must be unique'))
            else:
                pass
    



# <<<<<<< HEAD

# =======


    
    
    # @api.multi
    # @api.depends('meter_lines','fuel_lines','brand_id')
    # def _compute_mileage(self):
    #     for record in self:
    #         km = 0
    #         fuel = 0
    #         # for meter in record.meter_lines:
    #         if record.meter_lines:
    #             km = record.meter_lines[-1].end_value
    #             print 'km------------------------', km
    #
    #         for rec in record.fuel_lines:
    #             fuel += rec.litre * rec.per_litre
    #         print 'fuel------------------------', fuel
    #         if fuel != 0:
    #             record.mileage = km/fuel
class VehicleRatePerKm(models.Model):
    _name='vehicle.rate.per.km'

    rate = fields.Float("Rate")
    with_efect = fields.Date("With Effect From")
    vehicle_id = fields.Many2one('fleet.vehicle',"Vehicle")

class VehicleInsurer(models.Model):
    _name = 'vehicle.insurer'

    name = fields.Char("Name")

class VehicleOwner(models.Model):
    _name='vehicle.owner'

    name=fields.Char("Name")
    address = fields.Text("Address")

class VehicleCategoryType(models.Model):
    _name = 'vehicle.category.type'

    name = fields.Char(string="Vehicle Type")
    priority = fields.Integer("Priority")
    
class FullSupplyLine(models.Model):
    _name = 'fullsupply.line'

    line_id = fields.Many2one('fleet.vehicle')
    date_from = fields.Date('From')
    date_to = fields.Date('To')
    location_id = fields.Many2one('stock.location','Location')
    product_id = fields.Many2one('product.product','Product')
    rate = fields.Float('Rate')
    
class FleetIssueDetails(models.Model):
    _name = 'fleet.issue.details'
    
    name = fields.Many2one('fleet.vehicle',"Vehicle")
    date = fields.Date("Date")
    mrn_no = fields.Many2one('material.issue.slip',"MRN No")
    item_id = fields.Many2one('product.product',"Item")
    qty = fields.Float("Qty")
    rate = fields.Float("Rate")
    amount = fields.Float("Amount")


class FleetReceiptDetails(models.Model):
    _name = 'fleet.receipt.details'
    
    name = fields.Many2one('fleet.vehicle', "Vehicle")
    date = fields.Date("Date")
    grr_no = fields.Many2one('goods.recieve.report', "GRR No")
    item_id = fields.Many2one('product.product', "Item")
    qty = fields.Float("Qty")
    rate = fields.Float("Rate")
    tax_ids = fields.Many2many('account.tax','fleet_receipt_tax_rel','fleet_receipt_id','tax_id',string="Taxes")
    amount = fields.Float("Amount")


class fleet_vehicle_cost(models.Model):
    _inherit = 'fleet.vehicle.cost'
    
    @api.depends('qty','rate','taxes_ids')
    def compute_total(self):
        for rec in self:
            tax = 0
            ctax_amt = 0
            stax_amt = 0
            itax_amt = 0
            for taxes in rec.taxes_ids:
                if taxes.tax_type == 'cgst':
                    ctax_amt += taxes.amount
                if taxes.tax_type == 'sgst':
                    stax_amt += taxes.amount
                if taxes.tax_type == 'igst':
                    itax_amt += taxes.amount
                
                if taxes.tax_type != 'igst':
                    if taxes.price_include:
                        tax += (.5 + taxes.amount)
                    else:
                        tax = 1
                else:
                    if taxes.price_include:
                        tax += (1 + taxes.amount)
                    else:
                        tax = 1
            if tax == 0:
                tax = 1
            rec.sub_total = (rec.rate / tax) * rec.qty
            rec.cgst_amt = rec.sub_total * ctax_amt
            rec.sgst_amt = rec.sub_total * stax_amt
            rec.igst_amt = rec.sub_total * itax_amt
            rec.total = rec.sub_total + rec.cgst_amt + rec.sgst_amt + rec.igst_amt
            
    @api.onchange('particular_id')
    def onchange_particular_id(self):
        for rec in self:
            if rec.particular_id:
                rec.rate = rec.particular_id.standard_price
                rec.taxes_ids = [(6,0,rec.particular_id.taxes_id.ids)]
    
    particular_id = fields.Many2one('product.product',"Particular")
    qty = fields.Float('Qty')
    rate = fields.Float('Rate')
    taxes_ids = fields.Many2many('account.tax','fleet_vehicle_cost_taxes_rel','fleet_vehicle_cost_id','taxes_id',"Taxes")
    sub_total = fields.Float("SubTotal",compute='compute_total',store=True)
    sgst_amt = fields.Float("SGST Amount", compute='compute_total',store=True)
    cgst_amt = fields.Float("CGST Amount", compute='compute_total',store=True)
    igst_amt = fields.Float("IGST Amount", compute='compute_total',store=True)
    total = fields.Float("Total", compute='compute_total',store=True)
    



class VehicleMeter(models.Model):
    _name = 'vehicle.meter'
    _order = 'date desc'

    @api.depends('start_value', 'fuel_value','end_value')
    def _get_consumption(self):
        for rec in self:
            if rec.fuel_value != 0:
                rec.consumption_rate = (rec.end_value - rec.start_value)/rec.fuel_value
            else:
                rec.consumption_rate = 0

    name = fields.Char('Name')
    date = fields.Date('Date')
    vehicle_id = fields.Many2one('fleet.vehicle', 'Vehicle')
    start_value = fields.Float('Start Value')
    end_value = fields.Float('End Value')
    fuel_value = fields.Float('Total Fuel Refilled')
    consumption_rate = fields.Float(string="Consumption Rate", compute="_get_consumption")


class VehicleFuelVoucher(models.Model):
    _name = 'vehicle.fuel.voucher'
    _order = 'date desc'

    @api.multi
    @api.depends('litre','per_litre')
    def compute_amount(self):
        for rec in self:
            rec.amount = rec.litre * rec.per_litre



    name = fields.Char('Name')
    date = fields.Date('Date')
    vehicle_id = fields.Many2one('fleet.vehicle', 'Vehicle')
    pump_id = fields.Many2one('account.account', 'Pump')
    litre = fields.Float('Fuel Qty')
    per_litre = fields.Float('Fuel Price')
    amount = fields.Float(compute='compute_amount', store=True, string='Amount')
    odometer = fields.Float('Total Meter')

class VehicleFuelTanker(models.Model):
    _name = 'vehicle.fuel.tanker'
    _order = 'date desc'

    name = fields.Char('Name')
    date = fields.Date('Date')
    vehicle_id = fields.Many2one('fleet.vehicle', 'Vehicle')
    tanker_id = fields.Many2one('fleet.vehicle', 'Tanker')
    opening_reading = fields.Float('Opening Reading')
    closing_reading = fields.Float('Closing Reading')
    litre = fields.Float('Fuel Qty')
    odometer = fields.Float('Vehicle Reading')

class VehiclePreventiveMaintenance(models.Model):
    _name = 'vehicle.preventive.maintenance'
    _rec_name = 'vehicle_id'

    vehicle_id = fields.Many2one('fleet.vehicle',"Vehicle")
    vehicle_preventive_maintenance_line_ids = fields.One2many('vehicle.preventive.maintenance.line','vehicle_preventive_maintenance_id',"Maintenance")


class VehiclePreventiveMaintenanceLine(models.Model):
    _name = 'vehicle.preventive.maintenance.line'


    @api.depends('service_period','last_service_km')
    def compute_next_service(self):
        for rec in self:
            rec.next_service_km = rec.last_service_km + rec.service_period

    vehicle_id = fields.Many2one('fleet.vehicle',"Vehicle")
    date = fields.Date("Date")
    last_service_km = fields.Float("Last Service KM/HRS")
    service_period = fields.Float("Service Period")
    next_service_km = fields.Float("Next Service KM/HRS",compute='compute_next_service',store=True)
    remarks = fields.Char("Remarks")
    vehicle_preventive_maintenance_id = fields.Many2one('vehicle.preventive.maintenance',"Vehicle Preventive Maintenance")
    