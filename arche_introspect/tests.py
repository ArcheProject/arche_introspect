from unittest import TestCase

from arche.api import Root
from arche.utils import get_view
from pyramid import testing


class IntegrationTests(TestCase):
     
    def setUp(self):
        self.config = testing.setUp(request = testing.DummyRequest())
 
    def tearDown(self):
        testing.tearDown()

    def test_include(self):
        self.config.registry.settings['arche.includes'] = 'arche_introspect'
        self.config.include('arche')
        root = Root()
        request = testing.DummyRequest()
        self.failUnless(get_view(root, request, '__introspection__'))
