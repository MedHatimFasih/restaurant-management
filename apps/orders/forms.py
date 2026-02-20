from django import forms
from .models import Order, OrderItem, Invoice
from apps.tables.models import Table
from apps.menu.models import MenuItem


class OrderForm(forms.ModelForm):
    """
    Formulaire pour créer/modifier une commande
    """
    class Meta:
        model = Order
        fields = ['table', 'order_type', 'customer_name', 'customer_phone', 'delivery_address', 'notes']
        widgets = {
            'table': forms.Select(attrs={
                'class': 'form-select',
            }),
            'order_type': forms.Select(attrs={
                'class': 'form-select',
            }),
            'customer_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nom du client'
            }),
            'customer_phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Téléphone'
            }),
            'delivery_address': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Adresse de livraison'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Notes spéciales'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filtrer uniquement les tables disponibles
        self.fields['table'].queryset = Table.objects.filter(status='available')
        self.fields['table'].required = False


class OrderItemForm(forms.ModelForm):
    """
    Formulaire pour ajouter un article à une commande
    """
    class Meta:
        model = OrderItem
        fields = ['menu_item', 'quantity', 'notes']
        widgets = {
            'menu_item': forms.Select(attrs={
                'class': 'form-select',
            }),
            'quantity': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'value': 1
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Ex: Sans sauce, bien cuit...'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filtrer uniquement les plats disponibles
        self.fields['menu_item'].queryset = MenuItem.objects.filter(is_available=True)


class OrderSearchForm(forms.Form):
    """
    Formulaire de recherche de commandes
    """
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Rechercher par numéro, client, table...'
        })
    )
    
    status = forms.ChoiceField(
        required=False,
        choices=[('', 'Tous les statuts')] + list(Order.STATUS_CHOICES),
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    order_type = forms.ChoiceField(
        required=False,
        choices=[('', 'Tous les types')] + list(Order.TYPE_CHOICES),
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )


class InvoiceForm(forms.ModelForm):
    """
    Formulaire pour créer une facture
    """
    class Meta:
        model = Invoice
        fields = ['payment_method', 'amount_paid', 'notes']
        widgets = {
            'payment_method': forms.Select(attrs={
                'class': 'form-select',
            }),
            'amount_paid': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Notes supplémentaires'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        self.order = kwargs.pop('order', None)
        super().__init__(*args, **kwargs)
        
        if self.order:
            # Pré-remplir le montant avec le total de la commande
            self.fields['amount_paid'].initial = self.order.total


class DiscountForm(forms.Form):
    """
    Formulaire pour appliquer une remise
    """
    discount_type = forms.ChoiceField(
        choices=[
            ('amount', 'Montant fixe'),
            ('percentage', 'Pourcentage'),
        ],
        widget=forms.RadioSelect(attrs={
            'class': 'form-check-input'
        })
    )
    
    discount_value = forms.DecimalField(
        min_value=0,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'placeholder': 'Valeur de la remise'
        })
    )
    
    reason = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Raison de la remise (optionnel)'
        })
    )