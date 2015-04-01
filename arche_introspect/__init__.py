from pyramid.i18n import TranslationStringFactory


_ = TranslationStringFactory('arche_introspect')


def includeme(config):
    config.include('.views')
