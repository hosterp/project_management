from openerp import models, fields, api
import datetime

class ServiceMonthlyDaily(models.Model):

	_name = 'service.month.day'

	date_from = fields.Date('Date From', default=datetime.datetime.now().date())
	date_to = fields.Date('Date To')

	@api.multi
	def print_report(self):
		datas = {
			# 'ids': ids,
			'model': 'fleet.vehicle.log.services',
			'form': self.read()[0]
		}
		return self.env['report'].get_action(self, 'hiworth_tms.report_daily_monthly_service_template', data=datas)

class ReportServiceVehicle(models.AbstractModel):

	_name = 'report.hiworth_tms.report_daily_monthly_service_template'

	@api.model
	def render_html(self, docids, data=None):
		print data.get('form')
		if data.get('form'):
			datas = []
			domain = []
			if data.get('form')['date_to']:
				domain.append(('date', '>=', data.get('form')['date_from']))
				domain.append(('date', '<=', data.get('form')['date_to']))
			else:
				domain.append(('date', '>=', data.get('form')['date_from']))
			for i in self.env['fleet.vehicle.log.services'].search(domain):
				mec=[]
				part = []
				for m in i.mechanic_id:
					mec.append(m.name)
				for p in i.cost_ids:
					part.append(p.particular_id.name)
				datas.append({
					'date_received': i.date or '',
					'type': i.vehicle_id.vehicle_categ_id.name or '',
					'vehicle_number': i.vehicle_id.license_plate or '',
					'fleet_number': i.vehicle_id.license_plate or '',
					'reading': i.odometer_end,
					'work': i.nature_id.name,
					'work_done': i.works_done,
					'spare_used': part,
					'mechanic': mec,
					'category': i.cost_subtype_id.name or '',
					'remark': i.notes
				})
			docargs = {
			  'doc_ids': data['form']['id'],
			  'doc_model': 'fleet.vehicle.log.services',
			  'docs': datas,
			}
			print docargs, "+_+_+_+__+_+_+_++_+_"
			return self.env['report'].render('hiworth_tms.report_daily_monthly_service_template', docargs)