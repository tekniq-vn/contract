# -*- coding: utf-8 -*-

from odoo import _, api, fields, models
from odoo.osv import expression

class LoyaltyReward(models.Model):
    _inherit = 'loyalty.reward'

    discount_line_product_recurring = fields.Boolean(string="Recurring Discount")

    def _get_discount_product_values(self):
        values = super()._get_discount_product_values()
        for reward, value in zip(self, values):
            value['subscribable'] = reward.discount_line_product_recurring
        return values

    def write(self, vals):
        res = super().write(vals)
        if 'discount_line_product_recurring' in vals:
            self.discount_line_product_id.write({'subscribable': vals['discount_line_product_recurring']})

