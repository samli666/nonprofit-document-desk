"""Compatibility entry point for the source-layout nonprofit QA module.

Keeping this thin re-export allows the module to be imported from a checkout
without requiring an editable package install, while the implementation stays
in ``src/nonprofit_qa.py`` for the documented direct-script workflow.
"""

from src.nonprofit_qa import *

