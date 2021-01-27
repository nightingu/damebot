from os import supports_fd
from decorator import decorator

class ComposedFunc:
    def __init__(self, func, *args, **kwargs) -> None:
        self.func = func
    
    def __call__(self, *args, **kwargs):
        return self.func(*args, **kwargs)
    
    def __add__(self, other_func):
        def _add(*args, **kwargs):
            return self.func(*args, **kwargs), other_func(*args, **kwargs)
        return ComposedFunc(_add)
    
    def __radd__(self, other_func):
        def _radd(*args, **kwargs):
            return other_func(*args, **kwargs), self.func(*args, **kwargs)
        return ComposedFunc(_radd)
