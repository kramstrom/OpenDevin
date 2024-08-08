from .e2b.sandbox import E2BBox
from .modal.sandbox import ModalSandBox


def get_runtime_cls(name: str):
    # Local imports to avoid circular imports
    if name == 'eventstream':
        from .client.runtime import EventStreamRuntime

        return EventStreamRuntime
    elif name == 'e2b':
        from .e2b.runtime import E2BRuntime

        return E2BRuntime
    elif name == 'modal':
        from .modal.runtime import ModalRuntime

        return ModalRuntime
    else:
        raise ValueError(f'Runtime {name} not supported')


__all__ = [
    'E2BBox',
    'ModalSandBox',
    'get_runtime_cls',
]
