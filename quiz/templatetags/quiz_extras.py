from django import template

register = template.Library()


@register.filter
def style_badge_class(style):
    mapping = {
        "VISUEL": "sl-badge-visuel",
        "AUDITIF": "sl-badge-auditif",
        "KINESTHESIQUE": "sl-badge-kinesthesique",
    }
    return mapping.get(style, "sl-badge-accent")


@register.filter
def style_label(style):
    mapping = {
        "VISUEL": "Visuel",
        "AUDITIF": "Auditif",
        "KINESTHESIQUE": "Kinesthesique",
    }
    return mapping.get(style, style)
