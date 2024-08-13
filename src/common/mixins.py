class BreadcrumbsAndButtonsMixin:
    def get_breadcrumbs(self):
        """
        Override this method to define breadcrumbs for the view.
        """
        return []

    def get_top_buttons(self):
        """
        Override this method to define top buttons for the view.
        """
        return []

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['breadcrumbs'] = self.get_breadcrumbs()
        context['top_buttons'] = self.get_top_buttons()
        return context
