from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import (
    Client, Device, Component, WorkType,
    Repair, RepairWork, RepairComponent, RepairAct
)


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'phone', 'email', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('first_name', 'last_name', 'middle_name', 'phone', 'email')
    readonly_fields = ('created_at',)


@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'client', 'brand', 'model', 'created_at')
    list_filter = ('device_type', 'created_at')
    search_fields = ('brand', 'model', 'serial_number', 'client__first_name', 'client__last_name')
    readonly_fields = ('created_at',)
    raw_id_fields = ('client',)


@admin.register(Component)
class ComponentAdmin(admin.ModelAdmin):
    list_display = ('name', 'part_number', 'quantity', 'unit_price', 'supplier', 'is_available_display')
    list_filter = ('supplier',)
    search_fields = ('name', 'part_number', 'supplier')
    readonly_fields = ('created_at', 'updated_at')

    def is_available_display(self, obj):
        if obj.quantity > 0:
            return format_html('<span style="color: green;">✓ В наличии ({})</span>', obj.quantity)
        return format_html('<span style="color: red;">✗ Нет в наличии</span>')
    is_available_display.short_description = 'Наличие'


@admin.register(WorkType)
class WorkTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'standard_price', 'created_at')
    search_fields = ('name', 'description')
    readonly_fields = ('created_at',)


class RepairWorkInline(admin.TabularInline):
    model = RepairWork
    extra = 1
    fields = ('work_type', 'quantity', 'unit_price', 'cost', 'notes')
    readonly_fields = ('cost',)


class RepairComponentInline(admin.TabularInline):
    model = RepairComponent
    extra = 1
    fields = ('component', 'quantity', 'unit_price', 'total_cost', 'was_purchased', 'notes')
    readonly_fields = ('total_cost',)


@admin.register(Repair)
class RepairAdmin(admin.ModelAdmin):
    list_display = ('id', 'device_link', 'client_name', 'status', 'total_cost', 'accepted_at', 'created_by')
    list_filter = ('status', 'accepted_at', 'created_by')
    search_fields = ('device__brand', 'device__model', 'device__client__first_name', 'device__client__last_name')
    readonly_fields = ('accepted_at', 'total_cost')
    fieldsets = (
        ('Основная информация', {
            'fields': ('device', 'problem_description', 'status', 'created_by')
        }),
        ('Даты', {
            'fields': ('accepted_at', 'started_at', 'completed_at', 'issued_at')
        }),
        ('Финансы', {
            'fields': ('total_cost',)
        }),
        ('Дополнительно', {
            'fields': ('master_notes',)
        }),
    )
    inlines = [RepairWorkInline, RepairComponentInline]

    def device_link(self, obj):
        url = reverse('admin:repair_device_change', args=[obj.device.id])
        return format_html('<a href="{}">{}</a>', url, obj.device)
    device_link.short_description = 'Техника'

    def client_name(self, obj):
        return obj.device.client.full_name
    client_name.short_description = 'Клиент'

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(RepairAct)
class RepairActAdmin(admin.ModelAdmin):
    list_display = ('act_number', 'repair_link', 'client_name', 'total_cost_display', 'created_at', 'printed_at')
    list_filter = ('created_at', 'printed_at')
    search_fields = ('act_number', 'repair__device__brand', 'repair__device__client__first_name')
    readonly_fields = ('act_number', 'created_at', 'repair_info', 'works_list', 'components_list', 'total_cost_display')

    fieldsets = (
        ('Основная информация', {
            'fields': ('repair', 'act_number', 'created_at', 'printed_at')
        }),
        ('Информация о ремонте', {
            'fields': ('repair_info', 'works_list', 'components_list', 'total_cost_display')
        }),
        ('Дополнительно', {
            'fields': ('notes',)
        }),
    )

    def repair_link(self, obj):
        url = reverse('admin:repair_repair_change', args=[obj.repair.id])
        return format_html('<a href="{}">Ремонт #{}</a>', url, obj.repair.id)
    repair_link.short_description = 'Ремонт'

    def client_name(self, obj):
        return obj.repair.device.client.full_name
    client_name.short_description = 'Клиент'

    def repair_info(self, obj):
        repair = obj.repair
        device = repair.device
        client = device.client
        return format_html(
            '<strong>Клиент:</strong> {}<br>'
            '<strong>Техника:</strong> {}<br>'
            '<strong>Проблема:</strong> {}<br>'
            '<strong>Статус:</strong> {}',
            client.full_name,
            device,
            repair.problem_description,
            repair.get_status_display()
        )
    repair_info.short_description = 'Информация о ремонте'

    def works_list(self, obj):
        works = obj.repair.works.all()
        if not works:
            return 'Работы не указаны'
        html = '<table style="width: 100%; border-collapse: collapse;">'
        html += '<tr><th style="border: 1px solid #ddd; padding: 8px;">Вид работы</th>'
        html += '<th style="border: 1px solid #ddd; padding: 8px;">Количество</th>'
        html += '<th style="border: 1px solid #ddd; padding: 8px;">Цена</th>'
        html += '<th style="border: 1px solid #ddd; padding: 8px;">Стоимость</th></tr>'
        for work in works:
            html += f'<tr>'
            html += f'<td style="border: 1px solid #ddd; padding: 8px;">{work.work_type.name}</td>'
            html += f'<td style="border: 1px solid #ddd; padding: 8px;">{work.quantity}</td>'
            html += f'<td style="border: 1px solid #ddd; padding: 8px;">{work.unit_price} руб.</td>'
            html += f'<td style="border: 1px solid #ddd; padding: 8px;">{work.cost} руб.</td>'
            html += f'</tr>'
        html += '</table>'
        return mark_safe(html)
    works_list.short_description = 'Выполненные работы'

    def components_list(self, obj):
        components = obj.repair.components.all()
        if not components:
            return 'Компоненты не использовались'
        html = '<table style="width: 100%; border-collapse: collapse;">'
        html += '<tr><th style="border: 1px solid #ddd; padding: 8px;">Компонент</th>'
        html += '<th style="border: 1px solid #ddd; padding: 8px;">Количество</th>'
        html += '<th style="border: 1px solid #ddd; padding: 8px;">Цена</th>'
        html += '<th style="border: 1px solid #ddd; padding: 8px;">Стоимость</th></tr>'
        for comp in components:
            html += f'<tr>'
            html += f'<td style="border: 1px solid #ddd; padding: 8px;">{comp.component.name}</td>'
            html += f'<td style="border: 1px solid #ddd; padding: 8px;">{comp.quantity}</td>'
            html += f'<td style="border: 1px solid #ddd; padding: 8px;">{comp.unit_price} руб.</td>'
            html += f'<td style="border: 1px solid #ddd; padding: 8px;">{comp.total_cost} руб.</td>'
            html += f'</tr>'
        html += '</table>'
        return mark_safe(html)
    components_list.short_description = 'Использованные компоненты'

    def total_cost_display(self, obj):
        return f"{obj.repair.total_cost} руб."
    total_cost_display.short_description = 'Общая стоимость'

    def save_model(self, request, obj, form, change):
        if 'printed_at' in form.changed_data and obj.printed_at is None:
            from django.utils import timezone
            obj.printed_at = timezone.now()
        super().save_model(request, obj, form, change)

