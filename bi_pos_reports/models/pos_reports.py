# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

import logging
from odoo import fields, models, api, _ , tools
import random
from datetime import date, datetime
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT
_logger = logging.getLogger(__name__)

class POSConfigSummery(models.Model):
	_inherit = 'pos.config'
	
	order_summery = fields.Boolean('Order Summery')
	product_summery = fields.Boolean('Product Summery')
	product_categ_summery = fields.Boolean('Product Category Summery')
	loc_summery = fields.Boolean('Audit Report')
	payment_summery = fields.Boolean('Payment Summery')


class ResConfigSettings(models.TransientModel):
	_inherit = 'res.config.settings'


	order_summery = fields.Boolean(related='pos_config_id.order_summery',readonly=False)
	product_summery = fields.Boolean(related='pos_config_id.product_summery',readonly=False)
	product_categ_summery = fields.Boolean(related='pos_config_id.product_categ_summery',readonly=False)
	loc_summery = fields.Boolean(related='pos_config_id.loc_summery',readonly=False)
	payment_summery = fields.Boolean(related='pos_config_id.payment_summery',readonly=False)

class PosSession(models.Model):
	_inherit = 'pos.session'


	def load_pos_data(self):
		loaded_data = {}
		self = self.with_context(loaded_data=loaded_data)
		for model in self._pos_ui_models_to_load():
			loaded_data[model] = self._load_model(model)
		self._pos_data_process(loaded_data)        
		pos_session_data=self._get_pos_ui_pos_pos_sessions(self._loader_params_pos_pos_sessions())
		loaded_data['pos_sessions'] = pos_session_data
		return loaded_data

	def _loader_params_pos_pos_sessions(self):
		return {
			'search_params': {
				'fields': [
					'id', 'name', 'user_id', 'config_id', 'start_at', 'stop_at', 'sequence_number',
					'payment_method_ids', 'statement_line_ids', 'state', 'update_stock_at_closing'
				],
			},
		}

	def _get_pos_ui_pos_pos_sessions(self, params):
		users = self.env['pos.session'].search_read(**params['search_params'])
		return users


	def _pos_ui_models_to_load(self):
		result = super()._pos_ui_models_to_load()
		new_model = 'stock.location'
		if new_model not in result:
			result.append(new_model)
		return result


	def _loader_params_stock_location(self):
		return {
			'search_params': {
				'domain': [['company_id', '=', self.config_id.company_id.id]],
			}
		}

	def _get_pos_ui_stock_location(self, params):
		return self.env['stock.location'].search_read(**params['search_params'])


class PosOrderSummery(models.Model):
	_inherit = 'pos.order'

	location_id = fields.Many2one(comodel_name='stock.location',string="Location", store=True,compute="compute_location")
	
	@api.depends('picking_ids')
	def compute_location(self):
		for rec in self:
			rec.location_id = False
			for pck in rec.picking_ids:
				rec.location_id = pck.location_id

	def update_order_summery(self, ord_st_date, ord_end_date, ord_state,curr_session,order_current_session):
		to_day_date = datetime.now().date()		
		summery_order = []
		current_lang = self.env.context

		if order_current_session == True:
			if ord_state == 'Select State':
				orders = self.env['pos.order'].search([
					('session_id', '=', curr_session),
					('state', 'in', ['paid','invoiced','done']),
					])
			else:
				orders = self.env['pos.order'].search([
					('session_id', '=', curr_session),
					('state','=',ord_state.lower()),
					])

		else:
			if ord_state == 'Select State':
				orders = self.env['pos.order'].search([
					('date_order', '>=', ord_st_date + ' 00:00:00'),
					('date_order', '<=', ord_end_date + ' 23:59:59'),
					('state', 'in', ['paid','invoiced','done']),
					])
			else:
				orders = self.env['pos.order'].search([
					('date_order', '>=', ord_st_date + ' 00:00:00'),
					('date_order', '<=', ord_end_date + ' 23:59:59'),
					('state','=',ord_state.lower()),
					])
		for order in orders:
			date = order.date_order.strftime('%Y-%m-%d')
			summery_order.append({'name': order.name, 'total': order.amount_total, 'date':date, 'state':order.state})

		return summery_order
	
	def update_product_summery(self,pro_st_date,pro_ed_date,prod_current_session,curr_session):
		config_obj = self.env['pos.config'].search([])
		current_lang = self.env.context

		if prod_current_session == True:
			orders = self.env['pos.order'].search([
			('session_id', '=', curr_session),
			('state', 'in', ['paid','invoiced','done']),
			('config_id', 'in', config_obj.ids)])

		else:
			if pro_st_date and pro_ed_date :
				orders = self.env['pos.order'].search([
					('date_order', '>=', pro_st_date + ' 00:00:00'),
					('date_order', '<=', pro_ed_date + ' 23:59:59'),
					('state', 'in', ['paid','invoiced','done']),
					('config_id', 'in', config_obj.ids)])
			else:
				orders = self.env['pos.order'].search([
					('session_id', '=', curr_session),
					('state', 'in', ['paid','invoiced','done']),
					('config_id', 'in', config_obj.ids)])

		pos_line_ids = self.env["pos.order.line"].search([('order_id', 'in', orders.ids)]).ids
		
		
		if pos_line_ids:
			self.env.cr.execute("""
				SELECT product_tmpl.name, sum(pos_line.qty) total
				FROM pos_order_line AS pos_line,
					 pos_order AS pos_ord,
					 product_product AS product,
					 product_template AS product_tmpl
				WHERE pos_line.product_id = product.id
					AND product.product_tmpl_id = product_tmpl.id
					AND pos_line.order_id = pos_ord.id
					AND pos_line.id IN %s 
				GROUP BY product_tmpl.name
				
			""", (tuple(pos_line_ids),))
			products = self.env.cr.dictfetchall()
		else:
			products = []

		return products

class LocationSumm(models.Model):

	_name = "pos.order.location" 
	_description ="POS Order Locaton"

	
	def update_location_summery(self, location,select_session,tab1,tab2):
		res = []
		prod =[]
		final_data ={
			'Abierto_por': None,
			'Punto_de_Venta': None,
			'Fecha_de_Apertura': None,
			'Fecha_de_Cierre': None,
			'Saldo_Inicial': None,
			'Saldo_Final': None,
			'Descuento': None,
			'Total_en_Bruto': None,
			'Tax': None,
			'Estado': None,
			'Lista_Productos': [],
			'Lista_Categorias': [],
			'Detalle_Inpuestos': [],
			'Metodos_de_Pago': [],
			'Metodos_de_Pago_Invoice': [],
			'Cantidad_de_Tipos':[],
		}

		prod_data = {}
		categ_data = {}
		payment_data = {}
		payment_invoice_data = {} 
		tax_total = 0
		descuentos = 0

		product_ids = self.env['product.product'].search([])
		if tab1 == True:
			session_id = self.env['pos.session'].browse(int(select_session))
			orders = self.env['pos.order'].search([
					('session_id', '=', session_id.id),
					('state', 'in', ['paid','invoiced','done']),
					])
			final_data.update({
				'Abierto_por': session_id.user_id.name,
				'Punto_de_Venta': session_id.config_id.name,
				'Fecha_de_Apertura': session_id.start_at,
				'Fecha_de_Cierre': session_id.stop_at,
				'Saldo_Inicial': session_id.cash_register_balance_start,
				'Saldo_Final': session_id.cash_register_balance_end_real,
				'Estado': session_id.state,
				'Total_en_Bruto': session_id.total_payments_amount,
			})
			for odr in orders:
				tax_total +=  odr.amount_tax
				for line in odr.lines:
					quants = self.env['stock.quant'].search(
						[
							('product_id.id', '=', line.product_id.id),
							('location_id.id', '=', odr.location_id.id)
						]
					)
					product = line.product_id.name
					categories = line.product_id.pos_categ_ids
					descuentos += (line.qty * line.price_unit) - line.price_subtotal_incl
					if product in prod_data:
						old_qty = prod_data[product]['qty']
						old_qty_remb = prod_data[product]['qty_remb']
						if len(odr.refunded_order_ids) > 0:
							prod_data[product].update({
								'qty_remb' : old_qty_remb + line.qty,
							})
						else:
							prod_data[product].update({
								'qty' : old_qty + line.qty,
							})
					else:
						if len(quants) > 1:
							if len(odr.refunded_order_ids) > 0:
								prod_data.update({ product : {
									'product_id': line.product_id.id,
									'product_name': line.product_id.name,
									'qty' : 0,
									'qty_remb' : line.qty,
									'product_unit_price': line.price_unit,
								}})
							else:
								prod_data.update({ product : {
									'product_id':line.product_id.id,
									'product_name':line.product_id.name,
									'qty' : line.qty,
									'qty_remb' : 0,
									'product_unit_price': line.price_unit,
								}})
						else:
							if len(odr.refunded_order_ids) > 0:
								prod_data.update({ product : {
									'product_id':line.product_id.id,
									'product_name':line.product_id.name,
									'qty' : 0,
									'qty_remb' : line.qty,
									'product_unit_price': line.price_unit,
								}})
							else:
								prod_data.update({ product : {
									'product_id':line.product_id.id,
									'product_name':line.product_id.name,
									'qty' : line.qty,
									'qty_remb' : 0,
									'product_unit_price': line.price_unit,
								}})
					for category in categories:
						key_category = category.id
						if key_category in categ_data:
							old_qty = categ_data[key_category]['qty']
							old_qty_remb = categ_data[key_category]['qty_remb']
							if len(odr.refunded_order_ids) > 0:
								categ_data[key_category].update({
									'qty_remb' : old_qty_remb + line.qty,
								})
							else:
								categ_data[key_category].update({
									'qty' : old_qty + line.qty,
								})
						else:
							categ_data.update({ key_category : {
								'category_id':category.id,
								'categ_name':category.name,
								'qty' : line.qty,
								'qty_remb': line.qty if len(odr.refunded_order_ids) > 0 else 0
							}})

				payments = odr.payment_ids
				for payment in payments:
					if odr.state == 'invoiced':
						key_payment = payment.payment_method_id.name
						if key_payment in payment_invoice_data:
							old_amount = payment_invoice_data[key_payment]['amount']
							payment_invoice_data[key_payment].update({
								'amount' : old_amount+payment.amount,
								'qty': payment_invoice_data[key_payment]['qty'] + 1,
							})
						else:
							payment_invoice_data.update({ key_payment : {
								'payment_id':payment.id,
								'payment_name':payment.payment_method_id.name,
								'amount' : payment.amount,
								'qty': 1,
							}})
					else:
						key_payment = payment.payment_method_id.name
						if key_payment in payment_data:
							old_amount = payment_data[key_payment]['amount']
							payment_data[key_payment].update({
								'amount' : old_amount+payment.amount,
								'qty': payment_data[key_payment]['qty'] + 1,
							})
						else:
							payment_data.update({ key_payment : {
								'payment_id':payment.id,
								'payment_name':payment.payment_method_id.name,
								'amount' : payment.amount,
								'qty': 1,
							}})
			final_data.update({
				'Lista_Productos': prod_data,
				'Lista_Categorias': categ_data,
				'Metodos_de_Pago': payment_data,
				'Metodos_de_Pago_Invoice': payment_invoice_data,
				'Tax': tax_total,
				'Descuento': descuentos,
			})
			return final_data
		else:
			orders = self.env['pos.order'].search([('state', 'in', ['paid','invoiced','done']),])
			location_id = int(location)
			for odr in orders:
				if odr.location_id.id == location_id :
					for line in odr.lines:
						quants = self.env['stock.quant'].search([
							('product_id.id', '=', line.product_id.id),
							('location_id.id', '=', location_id)])

						product = line.product_id.name
						if product in prod_data:
							old_qty = prod_data[product]['qty']
							prod_data[product].update({
								'qty' : old_qty+line.qty,
							})
						else:
							if len(quants) > 1:
								quantity = 0.0
								for quant in quants:
									quantity += quant.quantity

								prod_data.update({ product : {
									'product_id':line.product_id.id,
									'product_name':line.product_id.name,
									'qty' : line.qty,
									'avail_qty':quantity,
								}})
							else:
								prod_data.update({ product : {
									'product_id':line.product_id.id,
									'product_name':line.product_id.name,
									'qty' : line.qty,
									'avail_qty':quants.quantity,
								}})

			return prod_data
		

class PosCashReport(models.TransientModel):

	_name='cash.report.wizard'
	_description = "POS Cash Report Wizard"

	pos_session_id = fields.Many2one(
		'pos.session', 
		string="POS Sesión",
		required=True
	)
	#company_id = fields.Many2one('res.company',"Company")
	def action_print_pdf(self):
		
		data = {
            'session_id': self.pos_session_id
        }
		
		location_model = self.env['pos.order.location']
		result = location_model.update_location_summery(
			None, 
			self.pos_session_id, 
			True, 
			False
		)

		data =  {
				'type': 'ir.actions.report',
				'report_name': 'bi_pos_reports.cash_report_pdf_doc',  # Reemplaza con el nombre de tu reporte
				'report_type': 'qweb-pdf',
				'data': {
					'form': result,  # Aquí está tu diccionario con los datos
				}, 
				'context': self.env.context,
			}		
		return data
		
	

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:    
