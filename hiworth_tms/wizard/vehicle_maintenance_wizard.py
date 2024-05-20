from openerp import fields, models, api

class VehicleMaintenanceWizard(models.TransientModel):
    _name = 'vehicle.maintenance.wizard'

    date_from = fields.Date("Date From")
    date_to = fields.Date("Date To")
    vehicle_id = fields.Many2one('fleet.vehicle',"Vehicle")

    @api.multi
    def button_print_vehicle_maintenance_wizard(self):

        return self.env["report"].get_action(self, report_name='vehicle.maintenance.report.xlsx')