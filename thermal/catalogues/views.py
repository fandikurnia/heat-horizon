import json
import httplib2

from horizon import tables
from horizon import forms
from horizon import messages
from horizon import exceptions
from horizon import tabs

from django.core.urlresolvers import reverse_lazy
from django.core.urlresolvers import reverse
from django.views.generic import TemplateView
from django.http import HttpResponseRedirect
from django.core.cache import cache
from django.views import generic

from thermal import CATALOGUES
from thermal.models import HeatTemplate
from thermal.models import GitContent
from thermal.models import AWSContent
from thermal.api import heatclient

from .tables import ThermalCataloguesTable
from .forms import CataloguesForm


class IndexView(tables.DataTableView):
    table_class = ThermalCataloguesTable
    template_name = 'thermal/catalogues/index.html'

    def get_data(self, **kwargs):
        templates = []
        if 'catalogue' in self.request.GET:
            # TODO: make cache dir configurable via django settings
            # TODO: make disabling ssl verification configurable too
            h = httplib2.Http(".cache",
                              disable_ssl_certificate_validation=True)
            catalogue = CATALOGUES[self.request.GET['catalogue']]
            resp, content = h.request(catalogue['feed'], "GET")
         
            if catalogue['type'] == 'github':
                templates = json.loads(content)
                if type(templates) == dict and 'message' in templates:
                    # github returned an error
                    messages.error(self.request, templates['message'])
                    return []
                templates = map(lambda x: GitContent(x), templates)
            elif catalogue['type'] == 'aws':
                # TODO: figure this out after python-heatclient is implimented
                # the xml handling used in models may be ripped out if the
                # new client doesn't return xml
                import xml.etree.ElementTree as ET
                root = ET.fromstring(content)
                content = root.findall(".//{http://s3.amazonaws.com/doc/2006-03-01/}Contents")
                templates = map(lambda x: AWSContent(xml=x), content)
        return templates

    def get_context_data(self, **kwargs):
        context = super(IndexView, self).get_context_data(**kwargs)
        context['form'] = CataloguesForm()
        return context
