from django.views.generic import TemplateView
from campusnest.core.models import Chambre

class AccueilView(TemplateView):
    template_name = 'index.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['chambres'] = Chambre.objects.filter(
            statut='disponible'
        ).order_by('-created')[:6]
        return context
    