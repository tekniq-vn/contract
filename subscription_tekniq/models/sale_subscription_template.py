from dateutil.relativedelta import relativedelta

from odoo import api, fields, models
from odoo.tools import get_timedelta

class SaleSubscriptionTemplate(models.Model):
    _inherit = "sale.subscription.template"

    @property
    def recurring_period(self):
        if not self.recurring_rule_type or not self.recurring_interval:
            return False
        return relativedelta(**{self.recurring_rule_type: self.recurring_interval})

    
        



