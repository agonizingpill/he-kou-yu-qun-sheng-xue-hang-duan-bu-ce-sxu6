from enum import StrEnum
class Role(StrEnum):
    operator='operator'
    supervisor='supervisor'
    viewer='viewer'
class CruiseState(StrEnum):
    planned='planned'
    sailing='sailing'
    surveyed='surveyed'
    frozen='frozen'
class AnalysisState(StrEnum):
    queued='queued'
    running='running'
    done='done'
    reviewed='reviewed'
    failed='failed'
