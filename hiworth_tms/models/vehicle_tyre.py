from openerp import fields, models, api

class TyreModel(models.Model):
    _name = 'tyre.model'

    name=fields.Char("Name")

class TyrePosition(models.Model):
    _name='tyre.position'

    name=fields.Char("Name")

class TyreManufactuer(models.Model):
    _name = 'tyre.manufactuer'

    name=fields.Char("Name")

class TyreType(models.Model):
    _name = 'tyre.type'

    name=fields.Char("Name")

class RetreadingType(models.Model):
    _name = 'retreading.type'

    name=fields.Char("Name")



class VehicleTyre(models.Model):
    _name = 'vehicle.tyre'



    name = fields.Char("Tyre ID/SN")
    purchase_type = fields.Selection([('new','New'),('secondary','Secondary')],"Purchase Type")
    purchase_date = fields.Datetime("Purchase Date")
    tyre_model_id = fields.Many2one('tyre.model',"Tyre Model")
    supplier = fields.Many2one('res.partner',"Supplier Name",domain="[('supplier','=',True)]")
    tyre_cost = fields.Float("Tyre Cost")
    projected_life = fields.Float("Fitting KM")
    tyre_size = fields.Char("Tyre Size")
    warranty_period=fields.Datetime("Warranty Period")
    warranty_km =fields.Float("Warranty KM")
    manufacture_id = fields.Many2one('tyre.manufactuer',"Tyre Manufactuer")
    tyre_type_id = fields.Many2one('tyre.type',"Tyre Type")
    purchase_mileage = fields.Float("Purchase Mileage(KM)")
    position_id = fields.Many2one('tyre.position',"Tyre Position")
    is_remouldable = fields.Boolean("Is Remouldable")
    tread_warning=fields.Float("Tread/Retread Warning At Kms")
    # odometer_reading = fields.Float("Odometer Reading at Tyre Mount")
    vehicle_id = fields.Many2one('fleet.vehicle',"Vehicle")
    active = fields.Boolean("Active",default=True)
    tyre_retreading_line_ids = fields.One2many('retreading.tyre.line','tyre_id',"Tyre Rethreading")
    dispose_tyre_ids = fields.One2many('dispose.tyre','tyre_id',"Tyre Disposing Details")
    warranty_tyre_ids = fields.One2many('warranty.tyre','tyre_id',"Tyre Warranty Details")

    _sql_constraints = [('name', 'unique(name)', 'Tyre Name Already Exists')]

class RetreadingTyreLine(models.Model):
    _name = 'retreading.tyre.line'

    @api.onchange('vehicle_id')
    def onchange_vehicle_id(self):
        for rec in self:
            rec.tyre_id.vehicle_id = rec.vehicle_id.id

    @api.depends('fitting_km','removing_km')
    def compute_total_km(self):
        for rec in self:

            rec.total_km = rec.removing_km - rec.fitting_km
            cum = 0
            for tyre in rec.tyre_id.tyre_retreading_line_ids:
                cum += tyre.total_km
            rec.cum_km = cum

    # retreading_id = fields.Many2one('retreading.tyre')
    tyre_id = fields.Many2one('vehicle.tyre',"Tyre")
    manufacture_id = fields.Many2one('res.partner', "Retread Manufactuer/Vendor",domain="[('supplier','=',True)]")
    tyre_retrading_type = fields.Many2one('retreading.type',"Retreading Type")
    retreading_date = fields.Datetime("Retreading Date")
    estimated_life = fields.Float("Estimated Life ")
    retrading_cost = fields.Float("Retrading Cost")
    retreading_km = fields.Float("Retreading at KM")
    total_km= fields.Float("Total Mileage(KM) ",compute='compute_total_km')
    cum_km = fields.Float("Cum (KM)",compute='compute_total_km')
    vehicle_id = fields.Many2one('fleet.vehicle',"Vehicle")
    removing_km = fields.Float("Removing KM")
    removed_date = fields.Date("Removed Date")
    fitting_km = fields.Float("Fitiing KM")
    fitting_date = fields.Date("Fitting Date")
    remarks = fields.Char("Remarks")








class WarrantyTyre(models.Model):
    _name='warranty.tyre'

    date = fields.Date("Date")
    tyre_id = fields.Many2one('vehicle.tyre',"Tyre")
    tyre_type_id = fields.Many2one('tyre.type', "Tyre Type")
    amount = fields.Float("Claim Amount")
    claim_date = fields.Date("Claim Date")
    manufacture_id = fields.Many2one('tyre.manufactuer', "Tyre Manufactuer")
    insurer_id = fields.Many2one('res.partner',"Insurer",domain="[('is_insurer','=',True)]")
    is_account_entry = fields.Boolean("Is Account Entry Needed?")
    journal_id = fields.Many2one('account.journal',"Mode of Payment")
    account_id = fields.Many2one('account.account',"Debit Account")
    state = fields.Selection([('draft','Draft'),
                              ('paid','Paid')],default='draft',string="State")

    @api.multi
    def action_done(self):
        for rec in self:
            if rec.is_account_entry == True:
                move = self.env['account.move']
                move_line = self.env['account.move.line']

                if rec.account_id.id == False and rec.journal_id.id == False:
                    raise osv.except_osv(('Error'), ('Please configure journal and account for this payment'));
                elif rec.account_id.id == False:
                    raise osv.except_osv(('Error'), ('Please configure account for this payment'));
                elif rec.journal_id.id == False:
                    raise osv.except_osv(('Error'), ('Please configure journal for this payment'));
                else:
                    pass

                values = {
                    'journal_id': rec.journal_id.id,
                    'date': rec.date,
                }
                move_id = move.create(values)

                values = {
                    'account_id': rec.account_id.id,
                    'name':  ' Tyre Warrant Claim Payment',
                    'debit': rec.amount,
                    'credit':0,
                    'move_id': move_id.id,
                }
                line_id = move_line.create(values)

                values2 = {
                    'account_id': self.journal_id.default_credit_account_id.id,
                    'name': str(self.document_type) + 'Payment',
                    'debit': 0,
                    'credit': self.amount,
                    'move_id': move_id.id,
                }
                line_id = move_line.create(values2)
                move_id.button_validate()
            rec.state = 'paid'


class DisposeTyre(models.Model):
    _name = 'dispose.tyre'

    @api.onchange('vehicle_id')
    def onchange_vehicle_id(self):
        for rec in self:
            if rec.vehicle_id:
                tyre_list = []
                mounting_tyre = self.env['vehicle.mount'].search([('vehicle_id', '=', rec.vehicle_id.id)])
                for mount in mounting_tyre:
                    for list in mount.mounting_tyre_ids:
                        tyre_list.append(list.name.id)
                return {'domain': {'tyre_id': [('id', 'in', tyre_list)]}}

    @api.depends('retreading_km')
    def compute_total_km(self):
        for rec in self:
            if rec.retreading_km or rec.tyre_id:
                rec.total_km = rec.retreading_km - rec.tyre_id.purchase_mileage


    @api.model
    def create(self,vals):
        res = super(DisposeTyre, self).create(vals)
        res.tyre_id.active = False;
        return res

    retreading_date = fields.Datetime("Disposed Date")
    vehicle_id = fields.Many2one('fleet.vehicle',"Vehicle")
    tyre_id = fields.Many2one('vehicle.tyre',"Tyre")
    retreading_km = fields.Float("Disposed at KM")
    total_km = fields.Float("Total KM ", compute='compute_total_km')