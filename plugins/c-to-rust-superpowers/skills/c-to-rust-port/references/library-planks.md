# Library planks: porting a C shared library that C consumers link

A **library plank** replaces a C shared library with Rust, one unit at a time,
while every C consumer keeps building against it. It keeps the library's soname,
its exported symbol set and its upstream headers. Until the last unit lands, the
library is part C, part Rust, inside one `.so`.

These rules are generic: any C shared library replaced by Rust. Examples come
from libubox (OpenWrt's foundational utility library), the worked example.

## When this applies

Apply this file when the answer to the **library-plank check** is yes: *is the
target a library that C consumers link?* Every mode of `c-to-rust-superpowers`
(`new`, `remediate`, `resync`) asks it at entry. A program, a plugin loaded by
one host, or a Rust-only crate answers no; skip this file.

When it applies, each section below adds to the normal method; it does not
replace it. The plan names which sections it used.

## Header contract

<!-- Filled by the "Header contract section" ticket: header inlines and macros
stay C (G1/F12), upstream headers ship verbatim (G2), bindgen
--wrap-static-fns + --allowlist-file (G8/F14). -->

TODO: not yet written.

## Mixed .so build

<!-- Filled by the "Mixed C/Rust .so build recipe" ticket, on the measurements
from "Measure no_std library .so link shapes": link shape and version script
(F6/F13), default runtime no_std + #[panic_handler] (F32/G11), panic policy at
extern "C" (G11), release gates, the UNITS=none identity check. -->

TODO: not yet written.

## Oracle

<!-- Filled by the "Oracle and prove step for library planks" ticket: upstream
test suite as prove-test (G6/F7/F15), units call through the C ABI until the
library is all Rust (F26), memory-safety prove step (G12/F16). -->

TODO: not yet written.

## UB and the exceptions ledger

<!-- Filled by the "UB-in-C policy and exceptions-ledger format" ticket: UB
policy (G18/F21), ledger file and entry shape, ledger in the gate's diff
(F25/F29), ledger scope (F30/F28), stack allocation (F27/G19), build-profile
independent overflow (F23). -->

TODO: not yet written.
