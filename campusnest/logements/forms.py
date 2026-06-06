from django import forms
from django.forms import inlineformset_factory
from campusnest.logements.models import Cite, PhotoCity, Chambre, PhotoChambre, DateVisiteChambre


class CiteForm(forms.ModelForm):
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
            'description': forms.Textarea(attrs={
                'class': 'input-field resize-none',
                'rows': 4,
                'placeholder': 'Décrivez votre cité (environnement, accès, services…)',
            }),
        }
        labels = {
            'nom':         'Nom de la cité',
            'adresse':     'Adresse',
            'description': 'Description',
        }


class PhotoCityForm(forms.ModelForm):
    class Meta:
        model = PhotoCity
        fields = ['image', 'est_principale']
        widgets = {
            'image':          forms.ClearableFileInput(attrs={'class': 'input-field'}),
            'est_principale': forms.CheckboxInput(attrs={'class': 'accent-primary'}),
        }
        labels = {
            'image':          'Photo',
            'est_principale': 'Photo principale ?',
        }


class ChambreForm(forms.ModelForm):
    class Meta:
        model = Chambre
        fields = [
            'description', 'superficie', 'loyer', 'type', 'etat',
            'meublee', 'wc_interieur', 'cuisine', 'internet',
            'eau_courante', 'electricite', 'armoire',
        ]
        widgets = {
            'description': forms.Textarea(attrs={
                'class': 'input-field resize-none',
                'rows': 3,
                'placeholder': 'chambre 12, 2ième etage',
            }),
            'superficie':    forms.NumberInput(attrs={'class': 'input-field', 'placeholder': 'Ex : 12'}),
            'loyer':         forms.NumberInput(attrs={'class': 'input-field', 'placeholder': 'Ex : 25000'}),
            'type':          forms.Select(attrs={'class': 'input-field'}),
            'etat':          forms.Select(attrs={'class': 'input-field'}),
            'meublee':       forms.CheckboxInput(attrs={'class': 'accent-primary'}),
            'wc_interieur':  forms.CheckboxInput(attrs={'class': 'accent-primary'}),
            'cuisine':       forms.CheckboxInput(attrs={'class': 'accent-primary'}),
            'internet':      forms.CheckboxInput(attrs={'class': 'accent-primary'}),
            'eau_courante':  forms.CheckboxInput(attrs={'class': 'accent-primary'}),
            'electricite':   forms.CheckboxInput(attrs={'class': 'accent-primary'}),
            'armoire':       forms.CheckboxInput(attrs={'class': 'accent-primary'}),
        }
        labels = {
            'description':  'Description',
            'superficie':   'Superficie (m²)',
            'loyer':        'Loyer mensuel (FCFA)',
            'type':         'Type de chambre',
            'etat':         'État global',
            'meublee':      'Meublée',
            'wc_interieur': 'WC Intérieur',
            'cuisine':      'Cuisine',
            'internet':     'Internet / Wi-Fi',
            'eau_courante': 'Eau courante',
            'electricite':  'Électricité',
            'armoire':      'Armoire',
        }


class DateVisiteForm(forms.ModelForm):
    """Formulaire unitaire pour une date de visite (utilisé dans le formset)."""
    class Meta:
        model = DateVisiteChambre
        fields = ['date']
        widgets = {
            'date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'w-full border border-gray-300 rounded-xl px-3 py-2 text-base '
                         'focus:outline-none focus:ring-2 focus:ring-primary/40',
            }),
        }
        labels = {'date': ''}


# Formset inline : permet d'ajouter/supprimer N dates de visite depuis le formulaire chambre
DateVisiteFormSet = inlineformset_factory(
    Chambre,
    DateVisiteChambre,
    form=DateVisiteForm,
    fields=['date'],
    extra=3,          # 3 lignes vides par défaut à la création
    can_delete=True,  # case "Supprimer" sur chaque ligne existante
    min_num=0,
    validate_min=False,
)


class PhotoChambreForm(forms.ModelForm):
    class Meta:
        model = PhotoChambre
        fields = ['image', 'est_principale']
        widgets = {
            'image':          forms.ClearableFileInput(attrs={'class': 'input-field'}),
            'est_principale': forms.CheckboxInput(attrs={'class': 'accent-primary'}),
        }
        labels = {
            'image':          'Photo',
            'est_principale': 'Photo principale ?',
        }