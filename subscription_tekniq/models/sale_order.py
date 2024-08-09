from odoo import api, fields, models
from datetime import date

import logging
_logger = logging.getLogger(__name__)

class SaleOrder(models.Model):
    _inherit = "sale.order"

    subscription_template_id = fields.Many2one('sale.subscription.template', string='Subscription Template', ondelete='restrict')
    start_date = fields.Date(string='Start Date',
            compute='_compute_start_date',
            readonly=False,
            store=True,
            tracking=True,
            help="The start date indicate when the subscription periods begin.")

    def _compute_start_date(self):
        for so in self:
            if not so.subscription_template_id:
                so.start_date = False
            elif not so.start_date:
                so.start_date = fields.Date.today()

    # force grouped by order subscription template
    def group_subscription_lines(self):
        self.ensure_one()
        if self.subscription_template_id:
            return {self.subscription_template_id: self.order_line.filtered(lambda line: line.product_id.subscribable)}
        grouped = defaultdict(self.env['sale.order.line'])
        for order_line in self.order_line.filtered(
            lambda line: line.product_id.subscribable
        ):
            grouped[
                order_line.order_line.product_id.product_tmpl_id.subscription_template_id
            ] += order_line
        return grouped

    def create_subscription(self, lines, subscription_tmpl):
        subscription_lines = []
        for line in lines:
            subscription_lines.append((0, 0, line.get_subscription_line_values()))

        if subscription_tmpl:
            rec = self.env["sale.subscription"].create(
                {
                    "partner_id": self.partner_id.id,
                    "user_id": self._context["uid"],
                    "template_id": subscription_tmpl.id,
                    "pricelist_id": self.partner_id.property_product_pricelist.id,
                    "date_start": self.start_date or date.today(),
                    "recurring_next_date": self.start_date or date.today(),
                    "sale_order_id": self.id,
                    "sale_subscription_line_ids": subscription_lines,
                }
            )
            rec.action_start_subscription()
            self.subscription_ids = [(4, rec.id)]
            lines.write({'subscription_id': rec.id})
            #rec.recurring_next_date = self.get_next_interval(
            #    subscription_tmpl.recurring_rule_type,
            #    subscription_tmpl.recurring_interval,
            #)

    def _get_invoiceable_lines(self, final=False):
        subscription_id = self.env.context.get('subscription_id') 
        if not subscription_id:
            return super()._get_invoiceable_lines(final=final)
        recurring_date = self.env.context.get('recurring_date') or fields.Date.today()
        self.order_line.filtered(lambda line: line.subscription_id.id == subscription_id)._compute_qty_to_invoice()
        return super()._get_invoiceable_lines(final=final)

    def _prepare_invoice(self):
        values = super()._prepare_invoice()
        if recurring_date := self.env.context.get('recurring_date'):
            values['invoice_date'] = recurring_date
        return values

    def _create_recurring_invoice(self, recurring_to_date=None):
        invoices = self.env['account.move']
        # in the futures, when subscription date seperated from invoice date, invoices can be grouped
        grouped = True 
        #final = False 

        recurring_to_date = recurring_to_date or fields.Date.today()
        for order in self:
            for subscription in order.subscription_ids:
                recurring_date = subscription.recurring_next_date
                if not subscription.in_progress:
                    continue
                # increment recurring_date here instead of in create_invoice function make loop more readable
                while recurring_date <= recurring_to_date:
                    invoices += order.with_context(
                        subscription_id=subscription.id, 
                        recurring_date=recurring_date,
                        raise_if_nothing_to_invoice=False
                    )._create_invoices(grouped=grouped, final=True)
                    recurring_date += subscription.template_id.recurring_period
                subscription.recurring_next_date = recurring_date
        return invoices
