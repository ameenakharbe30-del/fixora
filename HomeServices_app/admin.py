from django.contrib import admin


from .models import ContactMessage
from .models import ServiceCatogarys

admin.site.register(ServiceCatogarys)


from django.contrib import admin
from django.utils.html import format_html
from .models import workers

class WorkerAdmin(admin.ModelAdmin):
    list_display = ('admin', 'contact_number', 'city', 'gender', 'acc_activation', 'avalability_status', 'aadhar_card_preview')

    def aadhar_card_preview(self, obj):
        if obj.aadhar_card:
            return format_html(
                '<a href="{}" target="_blank"><img src="{}" width="100"/></a>',
                obj.aadhar_card.url,
                obj.aadhar_card.url
            )
        return "No file"

    aadhar_card_preview.short_description = "Aadhar Card"

admin.site.register(workers, WorkerAdmin)



from django.contrib import admin
from .models import ContactMessage

@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'subject', 'created_at')
    search_fields = ('name', 'email', 'subject')
    list_filter = ('created_at',)

