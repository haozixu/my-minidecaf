from .passes.manage import Func2ProgPassConverter
from .passes.local_reg_alloc import LocalRegAllocator
from .passes.code_gen import AsmCodeEmitter
from .passes.translate import ProgramTranslator


backend_passes = [
    Func2ProgPassConverter(LocalRegAllocator()),
    Func2ProgPassConverter(AsmCodeEmitter()),
]
