from opendevin.core.config import AppConfig
from opendevin.events.action import (
    FileReadAction,
    FileWriteAction,
)
from opendevin.events.observation import (
    ErrorObservation,
    FileReadObservation,
    FileWriteObservation,
    Observation,
)
from opendevin.events.stream import EventStream
from opendevin.runtime import Sandbox
from opendevin.runtime.plugins import PluginRequirement
from opendevin.runtime.server.files import insert_lines, read_lines
from opendevin.runtime.server.runtime import ServerRuntime

from .sandbox import ModalSandBox


class ModalRuntime(ServerRuntime):
    def __init__(
        self,
        config: AppConfig,
        event_stream: EventStream,
        sid: str = "default",
        plugins: list[PluginRequirement] | None = None,
        sandbox: Sandbox | None = None,
    ):
        super().__init__(config, event_stream, sid, plugins, sandbox)
        if not isinstance(self.sandbox, ModalSandBox):
            raise ValueError("ModalRuntime requires an ModalSandBox")
