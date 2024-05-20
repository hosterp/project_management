from openerp import models, fields, api, _
from openerp import tools, _
from datetime import datetime, date, timedelta


class FleetDocumentRetread(models.TransientModel):
	_name = 'fleet.documents.retread'

	vehicle_id = fields.Many2one('fleet.vehicle',"Vehicle")
	date_from = fields.Date('Date From')
	date_to = fields.Date('Date To')
	tyre_id = fields.Many2one('vehicle.tyre',"Tyre")

	@api.multi
	def action_fleet_documents_open_window(self):

		datas = {
			'ids': self._ids,
			'model': self._name,
			'form': self.read(),
			'context': self._context,
		}

		return {
			'name': 'Documents Renewal Report',
			'type': 'ir.actions.report.xml',
			'report_name': 'hiworth_tms.report_fleet_vehicle_retrading_template',
			'datas': datas,
			'report_type': 'qweb-pdf'
		}

	@api.multi
	def action_fleet_documents_open_window1(self):

		datas = {
			'ids': self._ids,
			'model': self._name,
			'form': self.read(),
			'context': self._context,
		}

		return {
			'name': 'Documents Renewal Report',
			'type': 'ir.actions.report.xml',
			'report_name': 'hiworth_tms.report_fleet_vehicle_retrading_template',
			'datas': datas,
			'report_type': 'qweb-html'
		}


	@api.multi
	def get_details(self):
		list = []
		dom = []
		if self.date_from:
			dom.append(('removed_date','>=',self.date_from))
		if self.date_to:
			dom.append(('removed_date', '<=', self.date_to))
		if self.tyre_id:
			dom.append(('tyre_id', '=', self.tyre_id.id))
		re_vehicles = self.env['retreading.tyre.line'].search(dom)




		return re_vehicles





class FleetDocumentWizard(models.TransientModel):
	_name = 'fleet.documents.wizard'

 
	document_type = fields.Selection([('pollution','Pollution'),
									('road_tax','Road Tax'),
									('fitness','Fitness'),
									('insurance','Insurance'),
									  ('permit',"Permit"),
									], string="Document Type")
	date_from = fields.Date('Date From')
	date_to = fields.Date('Date To')
		


	@api.multi
	def action_fleet_documents_open_window(self):

			datas = {
				 'ids': self._ids,
				 'model': self._name,
				 'form': self.read(),
				 'context':self._context,
			}
		 
			return{
				 'name' : 'Documents Renewal Report',
				 'type' : 'ir.actions.report.xml',
				 'report_name' : 'hiworth_tms.report_fleet_documents_renewal_template',
				 'datas': datas,
				 'report_type': 'qweb-pdf'
			}

	@api.multi
	def action_fleet_documents_open_window1(self):

			datas = {
				 'ids': self._ids,
				 'model': self._name,
				 'form': self.read(),
				 'context':self._context,
			}
		 
			return{
				 'name' : 'Documents Renewal Report',
				 'type' : 'ir.actions.report.xml',
				 'report_name' : 'hiworth_tms.report_fleet_documents_renewal_template',
				 'datas': datas,
				 'report_type': 'qweb-html'
			}

 

	@api.multi
	def get_details123(self):
		list = []
		doc_renewal = ''
		vehicles = self.env['fleet.vehicle'].search([])
		for veh_id in vehicles:

			if self.document_type == 'pollution':
				doc_renewal = self.env['fleet.vehicle.documents'].search([('document_type','=','pollution'),('vehicle_id','=', veh_id.id),('renewal_date','>=',self.date_from),('renewal_date','<=',self.date_to)], order="renewal_date desc",limit=1)
			elif self.document_type == 'road_tax':
				doc_renewal = self.env['fleet.vehicle.documents'].search([('document_type','=','road_tax'),('vehicle_id','=', veh_id.id),('renewal_date','>=',self.date_from),('renewal_date','<=',self.date_to)], order="renewal_date desc",limit=1)
			elif self.document_type == 'fitness':
				doc_renewal = self.env['fleet.vehicle.documents'].search([('document_type','=','fitness'),('vehicle_id','=', veh_id.id),('renewal_date','>=',self.date_from),('renewal_date','<=',self.date_to)], order="renewal_date desc",limit=1)
			elif self.document_type == 'insurance':
				doc_renewal = self.env['fleet.vehicle.documents'].search([('document_type','=','insurance'),('vehicle_id','=', veh_id.id),('renewal_date','>=',self.date_from),('renewal_date','<=',self.date_to)], order="renewal_date desc",limit=1)
			elif self.document_type == 'permit':
				doc_renewal = self.env['fleet.vehicle.documents'].search([('document_type','=','permit'),('vehicle_id','=', veh_id.id),('renewal_date','>=',self.date_from),('renewal_date','<=',self.date_to)], order="renewal_date desc",limit=1)
			else:
				pass

			if doc_renewal:
				print 'doc_renewal.renewal_date1234--------------------', doc_renewal.renewal_date, datetime.strptime(doc_renewal.renewal_date, '%Y-%m-%d').strftime('%-m/%d/%y')
				list.append({'vehicle_type':veh_id.categ_id.name,
							 'present_insurance':doc_renewal.insurer_id.name,
								'vehicle_name': veh_id.name,
								'renewal_date': datetime.strptime(doc_renewal.renewal_date, '%Y-%m-%d').strftime('%d-%m-%Y'),
								'amount':doc_renewal.amount,
							 'renewal_premeium':doc_renewal.renewal_premeium,
								})

		
		list_new  = sorted(list, key = lambda i: datetime.strptime(i['renewal_date'], '%d-%m-%Y'))
		
		return list_new



class FleetDocumentsAll(models.Model):
	_name = 'fleet.documents.all'

 
	document_ids = fields.One2many('fleet.documents.all.line', 'line_id')

	@api.multi
	def open_report_documents_all(self):
		return self.env['report'].get_action(self, 'hiworth_tms.report_fleet_documents_all')

	@api.model
	def default_get(self, default_fields):
		vals = super(FleetDocumentsAll, self).default_get(default_fields)
		list=[]
		vehicles = self.env['fleet.vehicle'].search([('rent_vehicle','!=',True)])
		for veh_id in vehicles:
			pollution = self.env['fleet.vehicle.documents'].search([('document_type','=','pollution'),('vehicle_id','=', veh_id.id)], order="date desc", limit=1)
			road_tax = self.env['fleet.vehicle.documents'].search([('document_type','=','road_tax'),('vehicle_id','=', veh_id.id)], order="date desc", limit=1)
			fitness = self.env['fleet.vehicle.documents'].search([('document_type','=','fitness'),('vehicle_id','=', veh_id.id)], order="date desc", limit=1)
			insurance = self.env['fleet.vehicle.documents'].search([('document_type','=','insurance'),('vehicle_id','=', veh_id.id)], order="date desc", limit=1)
			if pollution or road_tax or fitness or insurance:
				list.append([0, 0, {'vehicle_id':veh_id.id,
									'pollution_date':pollution.renewal_date,
									'road_tax_date':road_tax.renewal_date,
									'fitness_date':fitness.renewal_date,
									'insurance_date':insurance.renewal_date,
									'customer':True,
									'customer1':1,
									}])
			vals['document_ids'] = list
		return vals


class FleetDocumentsAll1(models.Model):
	_name = 'fleet.documents.all.line'

	line_id = fields.Many2one('fleet.documents.all')
	vehicle_id = fields.Many2one('fleet.vehicle', 'Vehicle')
	pollution_date = fields.Date('Pollution Renewal Date')
	road_tax_date = fields.Date('Road Tax Renewal Date')
	fitness_date = fields.Date('Fitness Renewal Date')
	insurance_date = fields.Date('Insurance Renewal Date')


class VehicleMileageWizard(models.TransientModel):
	_name = 'vehicle.mileage.wizard'

 
	date_from = fields.Date('Date From')
	date_to = fields.Date('Date To')
		


	@api.multi
	def action_vehicle_mileage_open_window(self):

			datas = {
				 'ids': self._ids,
				 'model': self._name,
				 'form': self.read(),
				 'context':self._context,
			}
		 
			return{
				 'name' : 'Mileage Report',
				 'type' : 'ir.actions.report.xml',
				 'report_name' : 'hiworth_tms.report_fleet_vehicle_mileage_template',
				 'datas': datas,
				 'report_type': 'qweb-pdf'
			}

	@api.multi
	def action_vehicle_mileage_open_window1(self):

			datas = {
				 'ids': self._ids,
				 'model': self._name,
				 'form': self.read(),
				 'context':self._context,
			}
		 
			return{
				 'name' : 'Mileage Report',
				 'type' : 'ir.actions.report.xml',
				 'report_name' : 'hiworth_tms.report_fleet_vehicle_mileage_template',
				 'datas': datas,
				 'report_type': 'qweb-html'
			}

 

	@api.multi
	def get_details(self):
		list = []
		mileage = 0
		vehicles = self.env['fleet.vehicle'].search([])
		for veh_id in vehicles:
			# line1 = self.env['diesel.pump.line'].search([('vehicle_id','=', veh_id.id),('date','>=',self.date_from),('date','<=',self.date_to)], order="date asc", limit=1)
			# line2 = self.env['diesel.pump.line'].search([('vehicle_id','=', veh_id.id),('date','>=',self.date_from),('date','<=',self.date_to)], order="date desc", limit=1)
			
			# if line1.date != self.date_from:
   #          	raise osv.except_osv(('Error'), ('Please configure journal and account for this payment'));
   			


   			vals2 = 0
			vals1 = 0
			km2 = 0
			km1 = 0
			km = 0
			litre = 0

			lines = self.env['diesel.pump.line'].search([('is_full_tank','=',True),('vehicle_id','=', veh_id.id),('date','>=',self.date_from),('date','<=',self.date_to)])
			if lines:
				for line_id in lines:
					print 'line_id.date-------------------------', line_id.date, line_id.odometer
					vals2 = vals1
					vals1 = line_id.date
					km2 = km1
					km1 = line_id.odometer
					if vals1 and vals2:
						print '2------------------------------------', vals2,vals1,km2,km1
						lines2 = self.env['diesel.pump.line'].search([('is_full_tank','=',False),('vehicle_id','=', veh_id.id),('date','>',vals1),('date','<',vals2)])
						if not lines2:
							km = km + (km1 - km2)
							litre = litre + line_id.litre
							mileage = km/litre


				list.append({
								'vehicle_name': veh_id.name,
								'km': km,
								'litre': litre,
								'mileage': mileage,
								})

		return list


