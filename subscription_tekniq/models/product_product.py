from odoo import models


class ProductProduct(models.Model):
    _inherit = 'product.product'

    def _get_best_subscription_pricing_rule(self, **kwargs):
        self.ensure_one()

        duration, unit = kwargs.get('duration', False), kwargs.get('unit', '')

        if not self.subscribable or not duration or not unit:
            return self.env['sale.subscription.pricing']

        pricelist = kwargs.get('pricelist', self.env['product.pricelist'])
        available_pricings = self.product_subscription_pricing_ids.filtered(lambda p: p.subscription_template_id.recurring_interval == duration and p.plan_id.recurring_rule_type == unit and p._applies_to(self))
        best_pricing_with_pricelist = self.env['sale.subscription.pricing']
        best_pricing_without_pricelist = self.env['sale.subscription.pricing']
        for pricing in available_pricings:
            # If there are any variants for the pricing, check if current product id is included in the variants ids.
            variants_ids = pricing.product_variant_ids.ids
            variant_pricing_compatibility = len(variants_ids) == 0 or len(variants_ids) > 0 and self.id in variants_ids
            if pricing.pricelist_id == pricelist and variant_pricing_compatibility:
                best_pricing_with_pricelist |= pricing
            elif not pricing.pricelist_id and variant_pricing_compatibility:
                best_pricing_without_pricelist |= pricing

        return best_pricing_with_pricelist[:1] or best_pricing_without_pricelist[:1] or self.env['sale.subscription.pricing']
