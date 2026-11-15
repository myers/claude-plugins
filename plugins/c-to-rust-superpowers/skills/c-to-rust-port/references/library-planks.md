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

While a library plank is in progress, one `.so` holds the C units that remain
plus a Rust `staticlib` for the ported units. The consumer-visible ABI stays the
C build's: same SONAME, same exported symbols and versions, same `DT_NEEDED`.
The **release gates** below check this. Every other rule in this section exists
so the gates pass at a size near C.

### Build plumbing (first commit of every library plank)

1. **The library's own build system owns the link.** CMake, Make or meson calls
   cargo for the staticlib (target triple taken from the C toolchain) and does
   the final link itself. One target, unchanged soname and install rules.
2. **Add a per-unit knob** that lists which units build from Rust. Each listed
   unit drops its `.c` from the C sources. Three states matter:
   - *empty*: pure C, no Rust toolchain needed (the reference build);
   - `none`: the Rust plumbing links an empty staticlib and drops no `.c`;
   - a unit list: those units in Rust.
3. **Pass the identity check:** the `none` build passes every release gate and
   the oracle. This proves the plumbing before any unit is ported. Done when
   `none` is green and committed.

CI builds pure C, `none`, and the full ported set. Use per-unit toggles to
bisect an oracle failure down to one unit.

### Export list (version script)

If upstream ships a version script, use it verbatim, version nodes included.
Otherwise, generate `{ global: <symbols>; local: *; };` from the reference C
build's `nm -D --defined-only` output, commit it, and re-derive it on every
resync. It is the single list of exports: it hides Rust core, compiler-builtins
and bindgen's `*__extern` wrappers, and it roots `--gc-sections`.
`--exclude-libs` is the wrong tool: it hides the `#[no_mangle]` exports too.

### Link shape

```
-Wl,--whole-archive librs.a -Wl,--no-whole-archive
-Wl,--gc-sections -Wl,--version-script=exports.map -lc
```

- `--gc-sections` is the main lever: about a 4x size cut, measured.
- `--whole-archive` keeps exports that no C file references (`blob_memdup` in
  libubox). Without it they survive only when rustc's codegen-unit partitioning
  happens to place them in an object that C does reference, which is not
  guaranteed. Under gc it costs no bytes.
- Leave the C compile flags as they are; gc changes nothing on the C side.

**Static twin** (`libfoo.a`, if the library ships one): no version script
applies to an archive, and two Rust-bearing archives in one consumer link
collide on unmangled runtime symbols. Partial-link the staticlib into one
object (`ld -r --whole-archive librs.a --gc-sections`, with the exports as
roots), then `objcopy --keep-global-symbols=<exports>` so only the C exports
stay global, and add that object to the archive. Gate: `nm -g --defined-only`
of the twin equals the C twin's. *Not yet measured; the first library plank
that ships a twin proves it.*

### Runtime and panics

- **`no_std`, core only, no `alloc` crate** by default:
  `#![cfg_attr(not(test), no_std)]`, so cargo unit tests keep std. libc comes
  in through FFI. bindgen needs `--use-core` (see Header contract). For
  allocator identity, see the catalog's API-surface rows.
- **std is allowed only when the build still passes every release gate.** On
  glibc, std adds `libgcc_s` to `DT_NEEDED` even with nightly
  `panic=immediate-abort`, so in practice the gates rule it out.
- **Panics abort; they never unwind across `extern "C"`.** Set
  `panic = "abort"` in both the dev and release profiles. The handler calls
  libc `abort()` and prints nothing, so a Rust panic looks like a failed C
  `assert`: SIGABRT and a core dump.

```rust
#[cfg(not(test))]
#[panic_handler]
fn panic(_: &core::panic::PanicInfo) -> ! {
    extern "C" { fn abort() -> !; }
    unsafe { abort() }
}
```

- **Release profile:** `opt-level = "z"`, `lto = true`, `codegen-units = 1`.
  Stable is enough: with `no_std` and the abort handler above, nightly
  `-Zbuild-std`, `panic=immediate-abort` and `-Zlocation-detail=none` remove
  nothing more (measured).

Measured on libubox (x86_64 glibc, blob + blobmsg in Rust): this shape is 1.11×
the C `.so` stripped, with `DT_NEEDED` and `.dynsym` identical to C's. The
spike's std + whole-archive shape without gc was 16.6×.

### Release gates

Run on **every unit**, against the pure-C reference build:

1. **Exports:** defined global `.dynsym` symbols and their versions
   (`readelf --dyn-syms -V`) equal C's. For a static twin, compare
   `nm -g --defined-only` instead.
2. **Linkage:** SONAME and the `DT_NEEDED` list equal C's.
3. **Size:** stripped `.so` ≤ 1.25× C, unless the plan sets another budget.
4. **Oracle** green on the host.

At **release**, also run the oracle and the size gate on the cross target
(qemu-user or a device), not only on the host.

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
