from openerp import fields, models, api
from openerp.osv import osv
from dateutil import relativedelta


class ResPartner(models.Model):
    _inherit = 'res.partner'
    
    is_insurer = fields.Boolean('Is Insurer')
    is_rent_mach_owner = fields.Boolean(string='Is Rent Machine Owner')
    rent_vehicle_bata_ids = fields.One2many('rent.vehicle.bata','partner_id',"Rent & Bata Details")
    rent_vehicle_km_ids = fields.One2many('rent.vehicle.km','partner_id',"Rate Per Km Details")

class RentVehicleBata(models.Model):
    _name = 'rent.vehicle.bata'

    vehicle_categ_id = fields.Many2one('vehicle.category.type',"Vehicle Category")
    mode_of_bata = fields.Selection([('per_day','Per Day'),('per_month','Per Month'),('per_hour','Per Hour')],"Mode of Bata")
    mode_of_rate = fields.Selection([('per_day', 'Per Day'), ('per_month', 'Per Month'), ('per_hour', 'Per Hour')],
                                    "Mode of Rate")
    rate = fields.Float("Rate")
    bata = fields.Float("Bata")
    with_effect = fields.Date("With Effect")
    partner_id = fields.Many2one('res.partner')

class RentVehicleKm(models.Model):
    _name = 'rent.vehicle.km'


    rate_km = fields.Float("Rate Per Km")
    with_effect = fields.Date("With Effect")
    partner_id = fields.Many2one('res.partner')

class VehicleLogservices1(models.Model):
    _inherit = 'fleet.vehicle.log.services'
    
    def _get_default_service_type(self, cr, uid, context):
        try:
            model, model_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'fleet', 'type_service_service_8')
        except ValueError:
            model_id = False
        return model_id


    _defaults = {

        'cost_subtype_id': _get_default_service_type,
        'cost_type': 'services'
    }
    
    date_com = fields.Date('Date')
    odometer_end = fields.Float('Km/Hrs Reading')
    start_location = fields.Char('Location From')
    dest_location = fields.Char('Location To')
    opening_bal = fields.Float('Opening Balance')
    ending_bal = fields.Float('Ending Balance')
    nature_id = fields.Many2one('work.nature', 'Nature Of Work/Complaint')
    works_done = fields.Text('Works Done')
    mechanic_id = fields.Many2many('mechanic.person', string='Mechanic')
    maintenance_type_id = fields.Many2one('maintanence.type','Type of Maintenance')
    daily_maint_bool = fields.Boolean('Daily Maintenance',default=True)
    r_b_bool = fields.Boolean('Repair/Breakdown')
    prev_main_bool = fields.Boolean('Preventive Maintenance')
    project_id = fields.Many2one('project.project','Project')
    reg_code = fields.Many2one('vehicle.category.type',related="vehicle_id.vehicle_categ_id")
    tyre_bool = fields.Boolean('Tyre Repairs')
    other_bool = fields.Boolean('Other Repairs')
    last_main = fields.Date('Last Maintenance Attended')
    greasing_bool = fields.Boolean('Greasing')
    inspec_bool = fields.Boolean('All Round Insp')
    oil_check_bool = fields.Boolean('Oil Checks')
    tyre_battery_bool = fields.Boolean('Tyres/Battery')
    nature_breakdown = fields.Char('Nature Of breakdown')
    complete_work = fields.Boolean('Completed')
    taken_out_tyre = fields.Many2one('fleet.vehicle','Tyre taken Out From')
    fitted_tyre = fields.Many2one('fleet.vehicle','Tyre fitted To')
    type_tyre_work = fields.Selection([('retar','Rethread'),
                                        ('new','New')],'Rethread/New')
    mileage = fields.Float('Mileage')
    date_of_rectification = fields.Date("Date of Rectification")
    target_date_completion = fields.Date("Target Date of Completion")
    tyre_fitting_date = fields.Date("Tyre Fitting Date")
    last_pmr_reading = fields.Float("Last Service SMR Reading")
    service_period = fields.Float("Service Period")


class TyreNumberType(models.Model):
    
    _name = 'tyre.number.type'

    name = fields.Char('Tyre No')

class MaintenanceType(models.Model):

    _name = 'maintanence.type'

    name = fields.Char('Name')


class NatureOfWork(models.Model):

    _name = 'work.nature'
    _rec_name = 'name'

    name = fields.Char('Name')
    code = fields.Char('Code')

class Mechanic(models.Model):

    _name = 'mechanic.person'
    _rec_name = 'name'

    name = fields.Char('Name')
    code = fields.Char('Code')

class VehicleRouteMapping(models.Model):
    _name = 'fleet.route.mapping'

    vehicle_id = fields.Many2one('fleet.vehicle', string='Vehicle')
    start_date = fields.Date('Start Date')
    end_date = fields.Date('End Date')
    driver_id = fields.Many2one('hr.employee', string='Driver')
    routes = fields.One2many('fleet.route.mapping.line','route_id')
    start_bal = fields.Float('Start Balance')
    # end_bal = fields.Float('End Balance', compute="_compute_end_balance")


    @api.onchange('vehicle_id')
    def onchange_driver(self):
    	self.driver_id = self.vehicle_id.hr_driver_id.id

	# @api.multi
	# def _compute_end_balance(self):
	# 	for record in self:
	# 		bal = record.start_bal
	# 		for rec in record.routes:
	# 			bal = bal - rec.ending_bal


class VehicleRouteMapping1(models.Model):
    _name = 'fleet.route.mapping.line'

    route_id = fields.Many2one('fleet.route.mapping')
    vehicle_id = fields.Many2one('fleet.vehicle', string='Vehicle', related='route_id.vehicle_id')
    # license_plate = fields.Char('Liscense Plate', related='vehicle.license_plate')
    time_from = fields.Datetime('Start Time')
    time_to = fields.Datetime('End Time')
    driver_id = fields.Many2one('hr.employee', string='Driver', related='route_id.driver_id')
    odometer_start = fields.Float('Odometer Start Value')
    odometer_end = fields.Float('Odometer End Value')
    start_location = fields.Many2one('stock.location', string='Route From')
    dest_location = fields.Many2one('stock.location', string='Route To')
    opening_bal = fields.Float('Opening Balance')
    ending_bal = fields.Float('Ending Balance')

    stocks = fields.One2many('fleet.vehicle.stock','stock_id')

    @api.onchange('vehicle_id')
    def onchange_driver(self):
    	self.driver_id = self.vehicle_id.hr_driver_id.id

    

class VehicleRouteMapping2(models.Model):
    _name = 'fleet.vehicle.stock'

    stock_id = fields.Many2one('fleet.route.mapping.line')
    product_id = fields.Many2one('product.product', string='Product')
    description = fields.Char('Description')
    quantity = fields.Float('Quantity')



class VehicleDocuments(models.Model):
    _name = 'fleet.vehicle.documents'


    @api.model
    def create(self,vals):
        res = super(VehicleDocuments, self).create(vals)
        if res.document_type == 'permit':
            res.vehicle_id.permit_date = res.renewal_date
        if res.document_type == 'insurance':
            res.vehicle_id.insurance_date = res.renewal_date
        if res.document_type == 'fitness':
            res.vehicle_id.fitness_date = res.renewal_date
        if res.document_type == 'road_tax':
            res.vehicle_id.road_tax_date = res.renewal_date
        if res.document_type == 'pollution':
            res.vehicle_id.pollution_date = res.renewal_date
        return res


    @api.multi
    def write(self,vals):
        for rec in self:
            res = super(VehicleDocuments, self).write(vals)
            if res.document_type == 'permit':
                res.vehicle_id.permit_date = vals['renewal_date']
            if res.document_type == 'insurance':
                res.vehicle_id.insurance_date = vals['renewal_date']
            if res.document_type == 'fitness':
                res.vehicle_id.fitness_date = vals['renewal_date']
            if res.document_type == 'road_tax':
                res.vehicle_id.road_tax_date = vals['renewal_date']
            if res.document_type == 'pollution':
                res.vehicle_id.pollution_date = vals['renewal_date']
            return res


    date = fields.Date('Date')
    renewal_date = fields.Date('Renewal Date')
    vehicle_id = fields.Many2one('fleet.vehicle', string="Vehicle", domain="[('rent_vehicle','!=',True)]")
    vehicle_type = fields.Many2one('vehicle.category.type', string="Vehicle Type", related='vehicle_id.vehicle_categ_id')
    amount = fields.Float('Last Premium')
    journal_id = fields.Many2one('account.journal',string='Mode Of Payment', domain="[('type','in',['cash','bank'])]")
    account_id = fields.Many2one('account.account', string="Debit Account")
    insurer_id = fields.Many2one('res.partner', string="Insurance Company")
    state = fields.Selection([('draft','Draft'),('paid','Paid')], default="draft")
    renewal_premeium = fields.Float("Renewal Premium")
    document_type = fields.Selection([('pollution','Pollution'),
                                    ('road_tax','Road Tax'),
                                    ('fitness','Fitness'),
                                    ('insurance','Insurance'),
                                      ('permit',"Permit"),
                                    ], string="Document Type")
    is_account_entry = fields.Boolean('Is Account Entry Needed?', default=True)

    @api.onchange('date')
    def onchange_renewal_date(self):
        if self.date:
            date = fields.Datetime.from_string(self.date)
            if self.document_type == 'pollution':
                self.renewal_date = date + relativedelta.relativedelta(months=6)
            elif self.document_type == 'fitness':
                self.renewal_date = date + relativedelta.relativedelta(months=12)
            elif self.document_type == 'insurance':
                self.renewal_date = date + relativedelta.relativedelta(months=12)
            elif self.document_type == 'permit':
                self.renewal_date = date + relativedelta.relativedelta(months=12)
            else:
                pass
   







