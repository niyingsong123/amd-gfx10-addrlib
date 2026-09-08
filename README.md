# AMD AddrLib Research

Research on AMD surface layout, swizzle and mip-tail algorithms across GFX10, GFX11 and GFX12.

## Current findings

[ADDRLIB.md](ADDRLIB.md) is the preserved user-supplied pseudo-RTL excerpt. Its mode set and linear-pitch policy primarily match GFX12, while several mip-tail formulas are shared across generations. It is not a complete compilable RTL implementation.

- [逐段版本匹配表与问题清单](analysis/addrlib_version_audit.md)
- [经核对的tail注释](ADDRLIB_comment.md)
- [修正后的计算例子](analysis/three_address_calculation_examples.md)
- [固定上游来源](upstream/README.md)

## Repository contents

- analysis/: explanatory documents, version audit and arithmetic verification script.
- upstream/: provenance documentation; no complete upstream source snapshot is checked in.
- verilog/: model-planning README; no complete RTL model is checked in.

The original excerpt is retained unchanged so audit line references remain reproducible. Hardware pipeline stages are outside this functional analysis. Full upstream/RTL differential validation remains future work; the included arithmetic checks do not substitute for it.
