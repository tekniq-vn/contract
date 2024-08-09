from dateutil.relativedelta import relativedelta
from odoo import models, fields, api, _
from odoo.tools import format_date
import logging
_logger = logging.getLogger(__name__)


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    is_subscription = fields.Boolean(related="product_template_id.subscribable")
    subscription_id = fields.Many2one('sale.subscription', "Subscription")

    def _get_pricelist_price(self):
        if pricing := self.is_subscription and \
                      self.env['sale.subscription.pricing']._get_first_suitable_recurring_pricing(self.product_id, self.order_id.subscription_template_id, self.order_id.pricelist_id):
            return pricing.currency_id._convert(pricing.price, self.currency_id, self.company_id, fields.date.today())
        return super()._get_pricelist_price()

    def _get_subscription_qty_to_invoice(self, start_date=None, end_date=None):
        result = {}
        today = fields.Date.context_today(self)
        for line in self:
            if line.state != 'sale' or not line.subscription_id.in_progress:
                continue

            template = line.subscription_id.template_id
            if not start_date:
                start_date = line.order_id.start_date
                if today < start_date:
                    while start_date > today:
                        start_date -= template.recurring_period
                else:
                    while start_date + template.recurring_period <= today:
                        start_date += template.recurring_period
            end_date = end_date or start_date + template.recurring_period - relativedelta(days=1)
            qty_invoiced = line._get_subscription_qty_invoiced(start_date, end_date)

            if line.product_id.invoice_policy == 'order':
                if end_date < line.order_id.start_date or line.subscription_id.date and start_date >= line.subscription_id.date:
                    result[line.id] = 0 - qty_invoiced.get(line.id, 0.0)
                else:
                    result[line.id] = line.product_uom_qty - qty_invoiced.get(line.id, 0.0)
            else:
                result[line.id] = line.qty_delivered - qty_invoiced.get(line.id, 0.0)
        return result

    def _get_subscription_qty_invoiced(self, start_date=None, end_date=None):
        result = {}
        amount_sign = {'out_invoice': 1, 'out_refund': -1}
        for line in self:
            if not line.is_subscription or line.order_id.state != 'sale':
                continue
            qty_invoiced = 0.0

            #template = line.subscription_id.template_id
            #if not start_date:
            #    today = self.env.context.get("force_today") or fields.Date.context_today(self)
            #    start_date = line.subscription_id.recurring_next_date - relativedelta(
            #        **{template.recurring_rule_type: int(template.recurring_interval)}
            #        )
            #end_date = end_date or start_date + template.recurring_period - relativedelta(days=1)

            if not start_date or not end_date:
                continue
            related_invoice_lines = line.invoice_lines.filtered(
                lambda l: l.move_id.state != 'cancel' and
                        l.invoice_date and start_date <= l.invoice_date <= end_date)
            for invoice_line in related_invoice_lines:
                line_sign = amount_sign.get(invoice_line.move_id.move_type, 1)
                qty_invoiced += line_sign * invoice_line.product_uom_id._compute_quantity(invoice_line.quantity, line.product_uom)
            result[line.id] = qty_invoiced
        return result

    def _prepare_invoice_line(self, **optional_values):
        recurring_date = self.env.context.get('recurring_date')
        self.ensure_one()
        res = super()._prepare_invoice_line(**optional_values)

        if self.display_type:
            return res
        elif (template := self.subscription_id.template_id) and self.is_subscription:
            description = "%s - %s" % (self.name, template.name)
            lang_code = self.order_id.partner_id.lang
            new_period_start = recurring_date or self.subscription_id.recurring_next_date
            format_start = format_date(self.env, new_period_start, lang_code=lang_code)

            next_invoice_date = new_period_start + template.recurring_period
            new_period_end = next_invoice_date - relativedelta(days=1)

            format_end = format_date(self.env, new_period_end, lang_code=lang_code)
            description += _("\n%s to %s", format_start, format_end)

            #qty_to_invoice = self._get_subscription_qty_to_invoice(start_date=new_period_start,
            #                                                       end_date=new_period_end)
            #res['quantity'] = qty_to_invoice.get(self.id, 0.0)

            res.update({
                'name': description,
                #'start_date': new_period_start,
                #'end_date': new_period_end,
            })
        return res

    @api.depends('is_subscription', 'invoice_lines.invoice_date', 'subscription_id.recurring_next_date')
    def _compute_qty_to_invoice(self):
        other_lines = self.env['sale.order.line']
        recurring_date = self.env.context.get("recurring_date")
        subscription_id = self.env.context.get("subscription_id")
        subscription_qty_to_invoice = self._get_subscription_qty_to_invoice(start_date=recurring_date)
        for line in self:
            if not line.is_subscription:
                other_lines |= line
                continue
            if not subscription_id or line.subscription_id.id == subscription_id:
                line.qty_to_invoice = subscription_qty_to_invoice.get(line.id, 0.0)
            else:
                line.qty_to_invoice = 0.0
        super(SaleOrderLine, other_lines)._compute_qty_to_invoice()


