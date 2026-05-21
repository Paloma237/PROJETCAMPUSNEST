from django import forms
from campusnest.core.models import Cite, PhotoCity, Chambre, PhotoChambre

class CiteForm(forms.ModelForm):
    """Formulaire de création / édition d'une cité."""

    class Meta:
        model = Cite
        fields = ['nom', 'adresse', 'description']
        widgets = {
            'nom': forms.TextInput(attrs={
                'class': 'input-field',
                'placeholder': 'Ex : Résidence Les Palmiers',
            }),
            'adresse': forms.Textarea(attrs={
                'class': 'input-field resize-none',
                'rows': 2,
                'placeholder': 'Adresse complète',
            }),
            'quartier': forms.TextInput(attrs={
                'class': 'input-field',
                'placeholder': 'Ex : Bafoussam Centre',
            }),
            'ville': forms.TextInput(attrs={
                'class': 'input-field',
                'placeholder': 'Ex : Bandjoun',
            }),
            'description': forms.Textarea(attrs={
                'class': 'input-field resize-none',
                'rows': 4,
                'placeholder': 'Décrivez votre cité (environnement, accès, services…)',
            }),
        }
        labels = {
            'nom': 'Nom de la cité',
            'adresse': 'Adresse',
            'quartier': 'Quartier',
            'ville': 'Ville',
            'description': 'Description',
        }


class PhotoCityForm(forms.ModelForm):
    """Formulaire d'upload d'une photo de cité."""

    class Meta:
        model = PhotoCity
        fields = ['image', 'principale']
        widgets = {
            'image': forms.ClearableFileInput(attrs={'class': 'input-field'}),
            'principale': forms.CheckboxInput(attrs={'class': 'accent-primary'}),
        }
        labels = {
            'image': 'Photo',
            'principale': 'Photo principale ?',
        }


class ChambreForm(forms.ModelForm):
    """Formulaire de création / édition d'une chambre."""

    class Meta:
        model = Chambre
        # Correspondance exacte avec les champs de votre modèle :
        fields = [
            'description', 'superficie', 'loyer', 'type', 'etat',
            'meublee', 'wc_interieur', 'cuisine', 'internet', 'eau_courante', 'electricite',
        ]
        widgets = {
            'description': forms.Textarea(attrs={
                'class': 'input-field resize-none',
                'rows': 3,
                'placeholder': 'chambre 12, 2ième etage',
            }),
            'superficie': forms.NumberInput(attrs={'class': 'input-field', 'placeholder': 'Ex : 12'}),
            'loyer': forms.NumberInput(attrs={'class': 'input-field', 'placeholder': 'Ex : 25000'}),
            'type': forms.Select(attrs={'class': 'input-field'}),
            'etat': forms.Select(attrs={'class': 'input-field'}),
            'meublee':       forms.CheckboxInput(attrs={'class': 'accent-primary'}),
            'wc_interieur':  forms.CheckboxInput(attrs={'class': 'accent-primary'}),
            'cuisine':       forms.CheckboxInput(attrs={'class': 'accent-primary'}),
            'internet':      forms.CheckboxInput(attrs={'class': 'accent-primary'}),
            'eau_courante':  forms.CheckboxInput(attrs={'class': 'accent-primary'}),
            'electricite':   forms.CheckboxInput(attrs={'class': 'accent-primary'}),
        }
        labels = {
            'description':  'Description',
            'superficie':   'Superficie (m²)',
            'loyer':        'Loyer mensuel (FCFA)',
            'type':         'Type de chambre',
            'create_etat':  'État global',
            'meublee':      'Meublée',
            'wc_interieur': 'WC Intérieur',
            'cuisine':      'Cuisine',
            'internet':     'Internet / Wi-Fi',
            'eau_courante': 'Eau courante',
            'electricite':  'Électricité',
        }

class PhotoChambreForm(forms.ModelForm):
    """Formulaire d'upload d'une photo de chambre."""

    class Meta:
        model = PhotoChambre
        fields = ['image', 'principale']
        widgets = {
            'image': forms.ClearableFileInput(attrs={'class': 'input-field'}),
            'principale': forms.CheckboxInput(attrs={'class': 'accent-primary'}),
        }
        labels = {
            'image': 'Photo',
            'principale': 'Photo principale ?',
        }