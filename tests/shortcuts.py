def get_class_path(cls: type) -> str:
    return '%s.%s' % (cls.__module__, cls.__name__)