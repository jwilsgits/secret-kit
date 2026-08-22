"""Secret Kit generation engine. No UI, no disk writes, no sockets."""

from engine.generate import generate
from engine.entropy import EntropyPool

__all__ = ["generate", "EntropyPool"]
