from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from .models import Repair, Client, Component, RepairAct


def index(request):
    """Главная страница"""
    context = {
        'total_repairs': Repair.objects.count(),
        'active_repairs': Repair.objects.exclude(status__in=['completed', 'cancelled', 'unrepairable']).count(),
        'total_clients': Client.objects.count(),
        'low_stock_components': Component.objects.filter(quantity__lt=5).count(),
    }
    return render(request, 'repair/index.html', context)


@login_required
def repair_list(request):
    """Список ремонтов"""
    status_filter = request.GET.get('status', '')
    search_query = request.GET.get('search', '')

    repairs = Repair.objects.select_related('device', 'device__client', 'created_by').all()

    if status_filter:
        repairs = repairs.filter(status=status_filter)

    if search_query:
        repairs = repairs.filter(
            Q(device__brand__icontains=search_query) |
            Q(device__model__icontains=search_query) |
            Q(device__client__first_name__icontains=search_query) |
            Q(device__client__last_name__icontains=search_query)
        )

    context = {
        'repairs': repairs,
        'status_filter': status_filter,
        'search_query': search_query,
        'status_choices': Repair.STATUS_CHOICES,
    }
    return render(request, 'repair/repair_list.html', context)


@login_required
def repair_detail(request, repair_id):
    """Детальная информация о ремонте"""
    repair = get_object_or_404(
        Repair.objects.select_related('device', 'device__client', 'created_by'),
        id=repair_id
    )
    works = repair.works.select_related('work_type').all()
    components = repair.components.select_related('component').all()

    context = {
        'repair': repair,
        'works': works,
        'components': components,
        'has_act': hasattr(repair, 'act'),
    }
    return render(request, 'repair/repair_detail.html', context)


@login_required
def repair_act(request, repair_id):
    """Акт выполненных работ"""
    repair = get_object_or_404(
        Repair.objects.select_related('device', 'device__client'),
        id=repair_id
    )

    # Создаем акт, если его еще нет
    act, created = RepairAct.objects.get_or_create(repair=repair)

    works = repair.works.select_related('work_type').all()
    components = repair.components.select_related('component').all()

    context = {
        'act': act,
        'repair': repair,
        'works': works,
        'components': components,
    }
    return render(request, 'repair/repair_act.html', context)


@login_required
def client_list(request):
    """Список клиентов"""
    search_query = request.GET.get('search', '')
    clients = Client.objects.prefetch_related('devices').all()

    if search_query:
        clients = clients.filter(
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(phone__icontains=search_query) |
            Q(email__icontains=search_query)
        )

    context = {
        'clients': clients,
        'search_query': search_query,
    }
    return render(request, 'repair/client_list.html', context)


@login_required
def component_list(request):
    """Список компонентов на складе"""
    search_query = request.GET.get('search', '')
    low_stock = request.GET.get('low_stock', '')

    components = Component.objects.all()

    if search_query:
        components = components.filter(
            Q(name__icontains=search_query) |
            Q(part_number__icontains=search_query) |
            Q(supplier__icontains=search_query)
        )

    if low_stock:
        components = components.filter(quantity__lt=5)

    context = {
        'components': components,
        'search_query': search_query,
        'low_stock': low_stock,
    }
    return render(request, 'repair/component_list.html', context)

