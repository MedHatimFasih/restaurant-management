from django import forms
from .models import Category, MenuItem

class CategoryForm(forms.ModelForm):
    """
    Formulaire pour créer/modifier une catégorie
    """
    class Meta:
        model = Category
        fields = ['name', 'description', 'icon', 'order', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: Entrées, Plats, Desserts...'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Description de la catégorie (optionnel)'
            }),
            'icon': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: bi-cup-hot, bi-egg-fried'
            }),
            'order': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
        labels = {
            'name': 'Nom de la catégorie',
            'description': 'Description',
            'icon': 'Icône Bootstrap',
            'order': 'Ordre d\'affichage',
            'is_active': 'Catégorie active',
        }


class MenuItemForm(forms.ModelForm):
    """
    Formulaire pour créer/modifier un plat
    """
    class Meta:
        model = MenuItem
        fields = [
            'name', 'description', 'price', 'image', 'category',
            'is_available', 'prep_time', 'allergens',
            'is_spicy', 'is_vegetarian', 'is_vegan', 'calories'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nom du plat'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Description détaillée du plat'
            }),
            'price': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00'
            }),
            'image': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'category': forms.Select(attrs={
                'class': 'form-select'
            }),
            'is_available': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'prep_time': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'placeholder': '15'
            }),
            'allergens': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: Gluten, Lactose, Fruits à coque'
            }),
            'is_spicy': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'is_vegetarian': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'is_vegan': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'calories': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'placeholder': 'Optionnel'
            }),
        }
        labels = {
            'name': 'Nom du plat',
            'description': 'Description',
            'price': 'Prix (MAD)',
            'image': 'Image',
            'category': 'Catégorie',
            'is_available': 'Disponible',
            'prep_time': 'Temps de préparation (minutes)',
            'allergens': 'Allergènes',
            'is_spicy': 'Plat épicé',
            'is_vegetarian': 'Végétarien',
            'is_vegan': 'Végan',
            'calories': 'Calories',
        }
    
    def clean_price(self):
        """Validation du prix"""
        price = self.cleaned_data.get('price')
        if price and price <= 0:
            raise forms.ValidationError('Le prix doit être supérieur à 0')
        return price
    
    def clean_prep_time(self):
        """Validation du temps de préparation"""
        prep_time = self.cleaned_data.get('prep_time')
        if prep_time and prep_time < 1:
            raise forms.ValidationError('Le temps de préparation doit être au moins 1 minute')
        return prep_time


class MenuItemSearchForm(forms.Form):
    """
    Formulaire de recherche de plats
    """
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Rechercher un plat...'
        })
    )
    
    category = forms.ModelChoiceField(
        queryset=Category.objects.filter(is_active=True),
        required=False,
        empty_label="Toutes les catégories",
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    availability = forms.ChoiceField(
        required=False,
        choices=[
            ('', 'Tous'),
            ('available', 'Disponibles uniquement'),
            ('unavailable', 'Non disponibles uniquement'),
        ],
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    dietary = forms.MultipleChoiceField(
        required=False,
        choices=[
            ('vegetarian', 'Végétarien'),
            ('vegan', 'Végan'),
            ('spicy', 'Épicé'),
        ],
        widget=forms.CheckboxSelectMultiple(attrs={
            'class': 'form-check-input'
        })
    )