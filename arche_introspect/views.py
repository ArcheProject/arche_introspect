import StringIO

from arche import security
from arche.interfaces import IContextACL, IWorkflow
from arche.interfaces import ILocalRoles
from arche.interfaces import IRoot
from arche.utils import get_addable_content
from arche.utils import get_content_factories
from arche.utils import get_content_schemas
from arche.utils import get_content_views
from arche.utils import get_image_scales
from arche.utils import image_mime_to_title
from arche.views.actions import generic_submenu_items
from arche.views.base import BaseView
from betahaus.viewcomponent import view_action
from betahaus.viewcomponent.interfaces import IViewGroup
from pyramid.httpexceptions import HTTPNotFound
from pyramid.renderers import render
from pyramid.response import Response

try:
    import pygraphviz as pgv
except ImportError:
    pgv = None

from arche_introspect import _


common_titles = {False: _(u"No"),
                 True: _(u"Yes"),
                 security.Allow: _(u"Allow"),
                 security.Deny: _(u"Deny")}


class SystemInformationView(BaseView):

    def __call__(self):
        reg = self.request.registry
        vg = reg.queryUtility(IViewGroup, name = 'sysinfo')
        sysinfo_panels = []
        for (name, va) in vg.items():
            out = va(self.context, self.request, view = self)
            if out:
                sysinfo_panels.append({'id': name,
                                       'title': va.title,
                                       'body': out})
        return {'sysinfo_panels': sysinfo_panels}


@view_action('sysinfo', 'content_types',
             title = _(u"Content types"),
             permission = security.PERM_MANAGE_SYSTEM)
def content_types_panel(context, request, va, **kw):
    response = {
        'content_factories': get_content_factories(request.registry),
        'addable_content': get_addable_content(request.registry),
        'content_views': get_content_views(request.registry),
        'content_schemas': get_content_schemas(request.registry),
        'workflows': request.registry.workflows,
        'acl_iface': IContextACL,
        'local_roles_iface': ILocalRoles,
        }
    return render('arche_introspect:templates/content_types.pt', response, request = request)

@view_action('sysinfo', 'roles',
             title = _(u"Roles"),
             permission = security.PERM_MANAGE_SYSTEM)
def roles_pane(context, request, va, **kw):
    roles = security.get_roles(registry = request.registry).values()
    response = {
        'roles': roles,
        'common_titles': common_titles,
        'role_titles': dict([(x, x.title) for x in roles]),
        }
    return render('arche_introspect:templates/roles.pt', response, request = request)

@view_action('sysinfo', 'acl',
             title = "ACL",
             permission = security.PERM_MANAGE_SYSTEM)
def acl_panel(context, request, va, **kw):
    roles = security.get_roles(registry = request.registry).values()
    response = {
        'acl_registry': request.registry.acl,
        'role_titles': dict([(x, x.title) for x in roles]),
        }
    return render('arche_introspect:templates/acl.pt', response, request = request)

def _draw_wf_graph(wf, request):
    assert pgv is not None
    trans = request.localizer.translate
    G=pgv.AGraph(directed = True)
    for (name, title) in wf.states.items():
        G.add_node(name, label = trans(title))
    for transition in wf.transitions.values():
        G.add_edge(transition.from_state, transition.to_state, label = trans(transition.title))
    G.layout(prog = 'dot')
    output = StringIO.StringIO()
    G.draw(output, format = 'svg')
    contents = output.getvalue()
    output.close()
    return contents

@view_action('sysinfo', 'workflows',
             title = "Workflows",
             permission = security.PERM_MANAGE_SYSTEM)
def workflows_panel(context, request, va, **kw):
    workflows = [ar.factory for ar in request.registry.registeredAdapters() if ar.provided == IWorkflow]
    response = {
        'workflows': workflows,
        'has_pgv': pgv is not None,
        }
    return render('arche_introspect:templates/workflows.pt', response, request = request)

@view_action('sysinfo', 'images',
             title = _(u"Images"),
             permission = security.PERM_MANAGE_SYSTEM)
def images_panel(context, request, va, **kw):
    response = {'mime_to_title': image_mime_to_title,
                'scales': get_image_scales(request.registry)}
    return render('arche_introspect:templates/images.pt', response, request = request)

@view_action('site_menu', 'introspection',
             title = _("Introspection"),
             description = _("Technichal system information"),
             permission = security.PERM_MANAGE_SYSTEM,
             view_name = '__introspection__')
def sysinfo_menu(context, request, va, **kw):
    #This will probablt change in arche so keep track of it.
    return generic_submenu_items(context, request, va, **kw)

def wf_graph_response(context, request):
    if pgv is None:
        raise HTTPNotFound("pygraphwiz must be installed")
    wf_name = request.matchdict.get('wf_name', '')
    wf = None
    for ar in request.registry.registeredAdapters():
        if ar.provided == IWorkflow and wf_name == ar.name:
            wf = ar.factory
    if wf is None:
        #raise Exception()
        raise HTTPNotFound("No workflow registered with the name: %s" % wf_name)
    return Response(
            body = _draw_wf_graph(wf, request),
            headerlist=[
               ('Content-Type', "image/svg+xml"),
               # ('Content-Type', "image/png"),
               # ('Etag', thumb.etag)
                ]
            )

def includeme(config):
    config.add_view(SystemInformationView,
                    context = IRoot,
                    name = '__introspection__',
                    renderer = "arche_introspect:templates/introspect.pt",
                    permission = security.PERM_MANAGE_SYSTEM)
    config.add_route("wf_graph_img", "/_wf_graph_img/{wf_name}")
    config.add_view(wf_graph_response,
                    route_name="wf_graph_img",
                    permission=security.PERM_MANAGE_SYSTEM)
    config.scan()
