from django.conf import settings

from taxis.utils.whatsapp import admin_help_message, build_wa_link


def site_contact(request):
    """Feeds the floating 'Chat with admin' WhatsApp button in base.html.
    Empty string (button hidden) until WHATSAPP_ADMIN_NUMBER is set in .env."""
    return {
        "admin_wa_link": build_wa_link(settings.WHATSAPP_ADMIN_NUMBER, admin_help_message()),
    }
