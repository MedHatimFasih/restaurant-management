from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
import datetime

from .models import Table, TableMerge, Reservation


class TableForm(forms.ModelForm):
    """
    Formulaire pour créer/modifier une table
    """
    class Meta:
        model = Table
        fields = ['number', 'capacity', 'zone', 'status', 'description', 'position_x', 'position_y', 'is_active']
        widgets = {
            'number': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1
            }),
            'capacity': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'max': 20
            }),
            'zone': forms.Select(attrs={
                'class': 'form-select'
            }),
            'status': forms.Select(attrs={
                'class': 'form-select'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Description optionnelle'
            }),
            'position_x': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.1',
                'placeholder': 'Position X (optionnel)'
            }),
            'position_y': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.1',
                'placeholder': 'Position Y (optionnel)'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
    
    def clean_number(self):
        """Validation du numéro de table"""
        number = self.cleaned_data.get('number')
        
        # Vérifier l'unicité (sauf pour la modification)
        if self.instance.pk:
            if Table.objects.exclude(pk=self.instance.pk).filter(number=number).exists():
                raise ValidationError(f'Une table avec le numéro {number} existe déjà.')
        else:
            if Table.objects.filter(number=number).exists():
                raise ValidationError(f'Une table avec le numéro {number} existe déjà.')
        
        return number
    
    def clean_capacity(self):
        """Validation de la capacité"""
        capacity = self.cleaned_data.get('capacity')
        if capacity < 1:
            raise ValidationError('La capacité doit être au moins 1.')
        if capacity > 20:
            raise ValidationError('La capacité ne peut pas dépasser 20 personnes.')
        return capacity


class TableSearchForm(forms.Form):
    """
    Formulaire de recherche de tables
    """
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Rechercher par numéro...'
        })
    )
    
    zone = forms.ChoiceField(
        required=False,
        choices=[('', 'Toutes les zones')] + list(Table.ZONE_CHOICES),
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    status = forms.ChoiceField(
        required=False,
        choices=[('', 'Tous les statuts')] + list(Table.STATUS_CHOICES),
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    min_capacity = forms.IntegerField(
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Capacité min',
            'min': 1
        })
    )


class TableMergeForm(forms.ModelForm):
    """
    Formulaire pour fusionner des tables
    """
    class Meta:
        model = TableMerge
        fields = ['name', 'tables']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: Tables 5+6 pour groupe'
            }),
            'tables': forms.CheckboxSelectMultiple(attrs={
                'class': 'form-check-input'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filtrer uniquement les tables disponibles
        self.fields['tables'].queryset = Table.objects.filter(status='available', is_active=True)
    
    def clean_tables(self):
        """Validation des tables à fusionner"""
        tables = self.cleaned_data.get('tables')
        
        if not tables:
            raise ValidationError('Veuillez sélectionner au moins 2 tables.')
        
        if len(tables) < 2:
            raise ValidationError('Vous devez sélectionner au moins 2 tables pour une fusion.')
        
        # Vérifier que toutes les tables sont disponibles
        for table in tables:
            if not table.is_available():
                raise ValidationError(f'La table {table.number} n\'est pas disponible.')
        
        return tables


class ReservationForm(forms.ModelForm):
    """
    Formulaire pour créer/modifier une réservation
    """
    class Meta:
        model = Reservation
        fields = [
            'table', 'customer_name', 'customer_phone', 'customer_email',
            'num_guests', 'date', 'time', 'duration_minutes', 'notes'
        ]
        widgets = {
            'table': forms.Select(attrs={
                'class': 'form-select'
            }),
            'customer_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nom complet'
            }),
            'customer_phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '06XXXXXXXX'
            }),
            'customer_email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'email@exemple.com'
            }),
            'num_guests': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1
            }),
            'date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'time': forms.TimeInput(attrs={
                'class': 'form-control',
                'type': 'time'
            }),
            'duration_minutes': forms.NumberInput(attrs={
                'class': 'form-control',
                'value': 120
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Allergies, occasions spéciales...'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filtrer uniquement les tables actives
        self.fields['table'].queryset = Table.objects.filter(is_active=True)
    
    def clean_date(self):
        """Validation de la date"""
        date = self.cleaned_data.get('date')
        
        if date < timezone.now().date():
            raise ValidationError('La date de réservation ne peut pas être dans le passé.')
        
        return date
    
    def clean_time(self):
        """Validation de l'heure"""
        time = self.cleaned_data.get('time')
        
        # Vérifier les heures d'ouverture (exemple: 11h-23h)
        opening_time = datetime.time(11, 0)
        closing_time = datetime.time(23, 0)
        
        if time < opening_time or time > closing_time:
            raise ValidationError(f'Les réservations sont acceptées entre {opening_time.strftime("%H:%M")} et {closing_time.strftime("%H:%M")}.')
        
        return time
    
    def clean(self):
        """Validation globale"""
        cleaned_data = super().clean()
        table = cleaned_data.get('table')
        num_guests = cleaned_data.get('num_guests')
        date = cleaned_data.get('date')
        time = cleaned_data.get('time')
        
        # Vérifier la capacité
        if table and num_guests:
            if num_guests > table.capacity:
                raise ValidationError(
                    f'La table {table.number} a une capacité de {table.capacity} personnes. '
                    f'Vous avez demandé {num_guests} personnes.'
                )
        
        # Vérifier la disponibilité (pas de réservation existante)
        if table and date and time:
            # Exclure la réservation actuelle si modification
            existing_reservations = Reservation.objects.filter(
                table=table,
                date=date,
                time=time,
                status__in=['pending', 'confirmed']
            )
            
            if self.instance.pk:
                existing_reservations = existing_reservations.exclude(pk=self.instance.pk)
            
            if existing_reservations.exists():
                raise ValidationError(
                    f'La table {table.number} est déjà réservée à cette date et heure.'
                )
        
        return cleaned_data


class ReservationSearchForm(forms.Form):
    """
    Formulaire de recherche de réservations
    """
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Rechercher par nom, téléphone...'
        })
    )
    
    status = forms.ChoiceField(
        required=False,
        choices=[('', 'Tous les statuts')] + list(Reservation.STATUS_CHOICES),
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    table = forms.ModelChoiceField(
        queryset=Table.objects.filter(is_active=True),
        required=False,
        empty_label="Toutes les tables",
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )


class QuickReservationForm(forms.Form):
    """
    Formulaire de réservation rapide (simplifié)
    """
    customer_name = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nom du client'
        })
    )
    
    customer_phone = forms.CharField(
        max_length=15,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '06XXXXXXXX'
        })
    )
    
    num_guests = forms.IntegerField(
        min_value=1,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nombre de personnes'
        })
    )
    
    date = forms.DateField(
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    time = forms.TimeField(
        widget=forms.TimeInput(attrs={
            'class': 'form-control',
            'type': 'time'
        })
    )