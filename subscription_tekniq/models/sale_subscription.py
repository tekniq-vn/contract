from datetime import date, datetime

from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models
from odoo.exceptions import AccessError
from odoo.addons.subscription_oca.models.sale_subscription import SaleSubscription as SaleSubscriptionOca

class SaleSubscription(models.Model):
    _inherit = "sale.subscription"

    def calculate_recurring_next_date(self, start_date):
        if self.account_invoice_ids_count == 0:
            self.recurring_next_date = start_date
        else:
            type_interval = self.template_id.recurring_rule_type
            interval = int(self.template_id.recurring_interval)
            self.recurring_next_date = start_date + relativedelta(
                **{type_interval: interval}
            )

    def write(self, values):
        res = super(SaleSubscriptionOca, self).write(values)
        if "stage_id" in values:
            for record in self:
                if record.stage_id:
                    if record.stage_id.type == "in_progress":
                        record.in_progress = True
                    elif record.stage_id.type == "post":
                        record.close_reason_id = False
                        record.in_progress = False
                    else:
                        record.in_progress = False

        return res

    def close_subscription(self, close_reason_id=False):
        self.ensure_one()
        self.recurring_next_date = False
        closed_stage = self.env["sale.subscription.stage"].search(
            [("type", "=", "post")], limit=1
        )
        self.close_reason_id = close_reason_id
        if self.stage_id != closed_stage:
            self.stage_id = closed_stage

