# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api
from odoo.exceptions import UserError
from datetime import date, datetime
import logging
_logger = logging.getLogger(__name__)


class SaleAdvancePaymentInv(models.TransientModel):
    _inherit = 'sale.advance.payment.inv'

    recurring_to_date = fields.Date(string='Recurring to Date', default=date.today())

    def _create_invoices(self, sale_orders):
        sale_orders = sale_orders.with_context(raise_if_nothing_to_invoice=False)
        sale_orders.order_line.filtered('is_subscription').write({'qty_to_invoice': 0.0})
        invoices = super(SaleAdvancePaymentInv, self)._create_invoices(sale_orders)
        if self.advance_payment_method == 'delivered' and \
                sale_orders.subscription_ids.filtered('in_progress') and self.recurring_to_date:
            invoices += sale_orders._create_recurring_invoice(recurring_to_date=self.recurring_to_date)
        sale_orders.order_line._compute_qty_to_invoice()
        if not invoices:
            raise UserError(sale_orders._nothing_to_invoice_error_message())
        return invoices

