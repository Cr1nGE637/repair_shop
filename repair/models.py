from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone


class Client(models.Model):
    """Клиент - физическое лицо"""
    first_name = models.CharField('Имя', max_length=100)
    last_name = models.CharField('Фамилия', max_length=100)
    middle_name = models.CharField('Отчество', max_length=100, blank=True)
    phone = models.CharField('Телефон', max_length=20)
    email = models.EmailField('Email', blank=True)
    address = models.TextField('Адрес', blank=True)
    created_at = models.DateTimeField('Дата регистрации', auto_now_add=True)

    class Meta:
        verbose_name = 'Клиент'
        verbose_name_plural = 'Клиенты'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.last_name} {self.first_name} {self.middle_name}".strip()

    @property
    def full_name(self):
        return f"{self.last_name} {self.first_name} {self.middle_name}".strip()


class Device(models.Model):
    """Бытовая техника"""
    DEVICE_TYPES = [
        ('washing_machine', 'Стиральная машина'),
        ('refrigerator', 'Холодильник'),
        ('microwave', 'Микроволновка'),
        ('oven', 'Духовка'),
        ('dishwasher', 'Посудомоечная машина'),
        ('tv', 'Телевизор'),
        ('vacuum', 'Пылесос'),
        ('other', 'Другое'),
    ]

    client = models.ForeignKey(
        Client,
        on_delete=models.CASCADE,
        related_name='devices',
        verbose_name='Клиент'
    )
    device_type = models.CharField('Тип техники', max_length=50, choices=DEVICE_TYPES)
    brand = models.CharField('Бренд', max_length=100)
    model = models.CharField('Модель', max_length=100)
    serial_number = models.CharField('Серийный номер', max_length=100, blank=True)
    description = models.TextField('Описание', blank=True)
    created_at = models.DateTimeField('Дата добавления', auto_now_add=True)

    class Meta:
        verbose_name = 'Техника'
        verbose_name_plural = 'Техника'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_device_type_display()} {self.brand} {self.model}"


class Component(models.Model):
    """Компонент/материал на складе"""
    name = models.CharField('Название', max_length=200)
    part_number = models.CharField('Артикул', max_length=100, blank=True)
    quantity = models.PositiveIntegerField('Количество', default=0, validators=[MinValueValidator(0)])
    unit_price = models.DecimalField('Цена за единицу', max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    supplier = models.CharField('Поставщик', max_length=200, blank=True)
    created_at = models.DateTimeField('Дата добавления', auto_now_add=True)
    updated_at = models.DateTimeField('Дата обновления', auto_now=True)

    class Meta:
        verbose_name = 'Компонент'
        verbose_name_plural = 'Компоненты (Склад)'
        ordering = ['name']

    def __str__(self):
        return f"{self.name} (остаток: {self.quantity})"

    def is_available(self, quantity_needed=1):
        """Проверка наличия компонента на складе"""
        return self.quantity >= quantity_needed


class WorkType(models.Model):
    """Вид выполняемой работы"""
    name = models.CharField('Название работы', max_length=200)
    description = models.TextField('Описание', blank=True)
    standard_price = models.DecimalField('Стандартная цена', max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    created_at = models.DateTimeField('Дата добавления', auto_now_add=True)

    class Meta:
        verbose_name = 'Вид работы'
        verbose_name_plural = 'Виды работ'
        ordering = ['name']

    def __str__(self):
        return self.name


class Repair(models.Model):
    """Ремонт/заказ"""
    STATUS_CHOICES = [
        ('accepted', 'Принят'),
        ('in_progress', 'В работе'),
        ('waiting_parts', 'Ожидание запчастей'),
        ('ready', 'Готов к выдаче'),
        ('completed', 'Выдан'),
        ('cancelled', 'Отменен'),
        ('unrepairable', 'Невозможно отремонтировать'),
    ]

    device = models.ForeignKey(
        Device,
        on_delete=models.CASCADE,
        related_name='repairs',
        verbose_name='Техника'
    )
    problem_description = models.TextField('Описание проблемы (со слов клиента)')
    status = models.CharField('Статус', max_length=20, choices=STATUS_CHOICES, default='accepted')
    accepted_at = models.DateTimeField('Дата приема', auto_now_add=True)
    started_at = models.DateTimeField('Дата начала работ', null=True, blank=True)
    completed_at = models.DateTimeField('Дата завершения', null=True, blank=True)
    issued_at = models.DateTimeField('Дата выдачи', null=True, blank=True)
    master_notes = models.TextField('Заметки мастера', blank=True)
    total_cost = models.DecimalField('Общая стоимость', max_digits=10, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    created_by = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='repairs',
        verbose_name='Мастер'
    )

    class Meta:
        verbose_name = 'Ремонт'
        verbose_name_plural = 'Ремонты'
        ordering = ['-accepted_at']

    def __str__(self):
        repair_id = self.id if self.id else 'новый'
        return f"Ремонт #{repair_id} - {self.device} ({self.get_status_display()})"

    def calculate_total_cost(self):
        """Расчет общей стоимости ремонта"""
        if not self.pk:
            return 0
        total = 0
        # Стоимость работ
        for work in self.works.all():
            total += work.cost
        # Стоимость компонентов
        for component in self.components.all():
            total += component.total_cost
        return total

    def save(self, *args, **kwargs):
        # Пересчитываем стоимость только если repair уже сохранен
        if self.pk:
            self.total_cost = self.calculate_total_cost()
        super().save(*args, **kwargs)


class RepairWork(models.Model):
    """Выполненная работа в ремонте"""
    repair = models.ForeignKey(
        Repair,
        on_delete=models.CASCADE,
        related_name='works',
        verbose_name='Ремонт'
    )
    work_type = models.ForeignKey(
        WorkType,
        on_delete=models.PROTECT,
        related_name='repair_works',
        verbose_name='Вид работы'
    )
    quantity = models.PositiveIntegerField('Количество', default=1, validators=[MinValueValidator(1)])
    unit_price = models.DecimalField('Цена за единицу', max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    cost = models.DecimalField('Стоимость', max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    notes = models.TextField('Примечания', blank=True)

    class Meta:
        verbose_name = 'Выполненная работа'
        verbose_name_plural = 'Выполненные работы'
        ordering = ['work_type__name']

    def __str__(self):
        return f"{self.work_type.name} - {self.quantity} шт."

    def save(self, *args, **kwargs):
        self.cost = self.unit_price * self.quantity
        super().save(*args, **kwargs)
        # Обновляем общую стоимость ремонта
        if self.repair.pk:
            self.repair.total_cost = self.repair.calculate_total_cost()
            self.repair.save(update_fields=['total_cost'])


class RepairComponent(models.Model):
    """Использованный компонент в ремонте"""
    repair = models.ForeignKey(
        Repair,
        on_delete=models.CASCADE,
        related_name='components',
        verbose_name='Ремонт'
    )
    component = models.ForeignKey(
        Component,
        on_delete=models.PROTECT,
        related_name='repair_components',
        verbose_name='Компонент'
    )
    quantity = models.PositiveIntegerField('Количество', default=1, validators=[MinValueValidator(1)])
    unit_price = models.DecimalField('Цена за единицу', max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    total_cost = models.DecimalField('Общая стоимость', max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    was_purchased = models.BooleanField('Закуплен', default=False, help_text='Отметьте, если компонент был закуплен специально для этого ремонта')
    notes = models.TextField('Примечания', blank=True)

    class Meta:
        verbose_name = 'Использованный компонент'
        verbose_name_plural = 'Использованные компоненты'
        ordering = ['component__name']

    def __str__(self):
        return f"{self.component.name} - {self.quantity} шт."

    def save(self, *args, **kwargs):
        self.total_cost = self.unit_price * self.quantity
        super().save(*args, **kwargs)
        # Обновляем общую стоимость ремонта
        if self.repair.pk:
            self.repair.total_cost = self.repair.calculate_total_cost()
            self.repair.save(update_fields=['total_cost'])

        # Уменьшаем количество на складе, если компонент был взят со склада
        if not self.was_purchased and self.component.quantity >= self.quantity:
            self.component.quantity -= self.quantity
            self.component.save(update_fields=['quantity'])


class RepairAct(models.Model):
    """Акт выполненных работ"""
    repair = models.OneToOneField(
        Repair,
        on_delete=models.CASCADE,
        related_name='act',
        verbose_name='Ремонт'
    )
    act_number = models.CharField('Номер акта', max_length=50, unique=True)
    created_at = models.DateTimeField('Дата создания', auto_now_add=True)
    printed_at = models.DateTimeField('Дата печати', null=True, blank=True)
    notes = models.TextField('Дополнительные примечания', blank=True)

    class Meta:
        verbose_name = 'Акт выполненных работ'
        verbose_name_plural = 'Акты выполненных работ'
        ordering = ['-created_at']

    def __str__(self):
        return f"Акт #{self.act_number} от {self.created_at.strftime('%d.%m.%Y')}"

    def save(self, *args, **kwargs):
        if not self.act_number:
            # Генерируем номер акта
            from datetime import datetime
            self.act_number = f"ACT-{datetime.now().strftime('%Y%m%d')}-{self.repair.id}"
        super().save(*args, **kwargs)

