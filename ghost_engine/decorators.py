from typing import TYPE_CHECKING, Any, TypeAlias
if TYPE_CHECKING:
    from .scripting.behavior import Behavior
else:
    Behavior: TypeAlias = Any
from .core.logger import Logger

def deprecated(replacement = None):
    def deprecated_decorator(func):
        def wrapper(*args):
            warning = f"Method {func.__qualname__} is deprecated and may be removed in future versions."
            if replacement:
                warning += f" Please use {replacement.__qualname__} instead!"
            Logger("DEPRECATION WARNING").log_warning(warning)

            func(*args)

        return wrapper
    
    return deprecated_decorator

class NonOverrideable:
    """
        Makes the decorated method unable to be overridden.
    """
    def __init__(self, func):
        self.func = func

        self.inst = None
        def wrapper(*args, **kwds):
            return self.func(self.inst, *args, **kwds)
        self.wrapped_func = wrapper

    def __set_name__(self, owner: Behavior, name):        
        if not getattr(owner, 'override-patched', False):
            setattr(owner, 'orig-init-subclass', owner.__dict__['__init_subclass__'])
            def wrapper(cls):
                non_overrideable: dict[str, NonOverrideable] = getattr(owner, 'non-overrideable-methods', dict())
                for name, method in non_overrideable.items():
                    func = getattr(cls, name)
                    if func and func != method:
                        Logger("OVERRIDE PREVENTION").log_warning(f"{name} is marked as non-overrideable, yet was overriden by {cls.__name__}. It has been removed.")
                        delattr(cls, name)

                getattr(owner, 'orig-init-subclass').__func__(cls)
            
            owner.__init_subclass__ = classmethod(wrapper)
            setattr(owner, 'non-overrideable-methods', dict())
            setattr(owner, 'override-patched', True)

        getattr(owner, 'non-overrideable-methods')[self.func.__name__] = self.wrapped_func
    
    def __call__(self, *args, **kwds):
        return self.func(*args, **kwds)
    
    def __get__(self, instance, owner):
        self.inst = instance
        return self.wrapped_func