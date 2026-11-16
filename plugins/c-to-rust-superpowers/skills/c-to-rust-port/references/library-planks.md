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

The library's public headers are the spec. Consumers compile them, inline
bodies and macros included, so the Rust meets them; it never replaces them.

### Header code stays C

`static inline` functions and macros in a public header compile into every
consumer, not into the `.so`. Porting them changes nothing a consumer runs, so
they are a **contract** on the Rust, not units: the Rust must leave bytes and
struct state that the header code reads correctly (libubox: `blob_len()` reads
`attr->id_len` straight from memory, so the Rust writes `id_len` exactly as
the C does).

- **The coverage walk skips them.** The work list holds the functions defined
  in the library's `.c` files, including file-local `static` ones. A header
  inline or macro with no Rust counterpart is the expected state, not a
  dropped unit.
- **The plan states the contract.** In its Interfaces block, the plan lists
  the headers whose inline code stays C and says how the Rust reaches it
  (below). The oracle checks the contract: upstream tests and consumers
  compile the inlines from the real header and run them over the Rust's
  output.

### Upstream headers ship verbatim

- **Install the upstream headers unchanged,** from the same pinned SHA as the
  C. A resync takes them with the C; the reference set already lists them, and
  a header change can change every unit that touches the type.
- **The Rust gets its types from those headers through bindgen.** Use the
  bindgen types in `extern "C"` signatures and for every struct a consumer
  sees. Keep bindgen's layout tests on (drop `--no-layout-tests`): they are
  compile-time asserts, free under `no_std`, so a header change that moves a
  field fails the build. A Rust-side `#[repr(C)]` copy of a header type gets
  its own `size_of`/`align_of`/`offset_of!` asserts against the bindgen type.
- **Run bindgen for the C toolchain's target:** pass the same `--target`,
  sysroot and `-I`/`-D` flags the C build uses after `--`. Otherwise the
  layouts and asserts are the host's.
- **cbindgen is at most a drift check:** generate a header from the Rust
  exports and diff its prototypes against the upstream declarations. Its
  output never ships, since it cannot emit inline bodies, function-like macros
  or attributes such as `__packed`.

### Calling header code from Rust

When a ported unit calls a header inline (libubox: `blob_len`, the `list_*`
helpers), call the C through bindgen's wrappers, so the header stays the one
source of truth:

```
bindgen wrapper.h --use-core --wrap-static-fns --experimental \
  --wrap-static-fns-path $OUT_DIR/extern \
  --allowlist-file '.*/(blob|blobmsg)\.h' \
  --allowlist-function 'malloc|realloc|free|strcmp' \
  --allowlist-var 'EINVAL|ENOMEM' \
  -o $OUT_DIR/bindings.rs -- <C toolchain target and flags>
```

- **`--wrap-static-fns`** emits `extern.c`, one exported `*__extern` wrapper
  per inline. `build.rs` compiles it with the C compiler and flags and links it
  as a bundled static library, so the wrappers land inside the staticlib. The
  version script keeps them out of `.dynsym`. Measured on libubox: every
  inline in `blob.h` and `blobmsg.h` wrapped, oracle green.
- **`--allowlist-file`** scoped to the library's own headers. Unscoped,
  bindgen binds all of libc (libubox: 4,174 → 531 lines). Add the libc
  functions and constants the port calls by name with `--allowlist-function`
  and `--allowlist-var`.
- **`--use-core`** for the `no_std` default; without it the bindings name
  `::std::` and fail to build.
- **Use `core` for memory primitives:** `core::ptr::copy_nonoverlapping`,
  `write_bytes` and slice compares, in place of binding `memcpy`, `memset`,
  `memcmp` and `strlen`. Bindgen's declarations of those four trip rustc's
  lint on redefining runtime symbols.
- **Function-like macros cannot be wrapped.** Expand one in Rust by its exact
  structure, with an anchor naming it (`// C: blob.h:blob_for_each_attr`),
  and treat the expansion as a port the gate reviews. The catalog has the loop
  rules. A header change to the macro is a resync item for every expansion.

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

- **Release profile:** `opt-level = "z"`, `lto = true`, `codegen-units = 1`;
  `overflow-checks` as in [UB and the exceptions ledger](#ub-and-the-exceptions-ledger).
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

A library plank's counterpart is cheap to run: the pure-C reference build of
the same library. Phase 1.5 (prove it) for a library plank is the rules below.

### The upstream test suite is the prove-test

Link the library's own tests (unit binaries, cram or golden-output tests, the
fuzz corpus) against the reference C `.so`, then against the mixed `.so`. Same
inputs, same observable output. This is not circular: upstream wrote those
tests against the C, so nothing in them comes from the port. The ported unit
leaves the tests untouched; a test that must change is an oracle change and
goes in the plan, not the diff.

- **Expected output comes from the C build.** Where a test has no checked-in
  expectation, the reference C build's output at the pinned SHA is the
  expectation. The mixed build's output must diff empty against it.
- **Fuzz corpus:** replay every corpus input through the fuzz target linked
  against each build. Outcome (clean exit or abort) and any output must match.
- **Projection harness** for goldens in a consumer's format. When the best
  goldens are a consumer's wire format rather than calls into this library
  (libubox: ubus-zero's frames are ubus messages, not blob calls), write a small
  harness that drives them through the library's C API: parse, walk, rebuild,
  print. Run it on the C build to make the reference output, then on the mixed
  build; the diff must be empty. List every input the harness excludes, with
  the reason (libubox: 2 of 1572 frames, deliberately malformed ACL goldens).
- **Coverage check:** before porting a unit, confirm the suite reaches it. A
  unit no upstream test calls gets a projection harness or a new differential
  test, written and run against the C build first so its expectation comes
  from the C.

### Units call each other through the C ABI

Until the whole library is Rust, a ported unit calls every other unit through
its exported C symbol (`ffi::blob_put`), never through a Rust path
(`crate::blob::put`), even when that unit is already Rust. Then any mix of C
and Rust units links and runs, and each mix is an oracle configuration: with
two units, the 2×2 (C/C, Rust-on-C, C-on-Rust, Rust/Rust). Run the oracle on
every build CI makes (pure C, `none`, the full set); the per-unit knob builds
the other mixes, which bisect a failure to one unit. Whether these seams
collapse once the library is all Rust is a Phase 2 decision.

### Memory-safety prove step

MIRI cannot execute calls into C, and every oracle test above makes them, so
MIRI covers the cargo unit tests only. Upstream's sanitizer builds
(`-fsanitize=address` on the test binary) instrument the test binary, not the
`.so`, and stable Rust has no ASan: inside the library they catch only what
ASan's libc interceptors (`memcpy`, `free`) see.

The memory-safety prove step is **valgrind memcheck over the oracle inputs
against the plain mixed `.so`**: the test binaries, the projection harness,
edge cases and the fuzz corpus replay, each under `valgrind --leak-check=full`.
Run the same inputs on the C build first; its report is the baseline, since
upstream tests may leak by design. Gate: per input, the mixed build adds no
errors and no leaks beyond the baseline.

Memcheck sees heap misuse: out-of-bounds heap access, use after free, double
or mismatched free, reads of uninitialised memory, leaks. It misses overruns
inside the stack and in globals, which stay unchecked unless CI also builds
with nightly `-Zsanitizer=address` (Rust and C both instrumented). State that
gap in the plan.

## UB and the exceptions ledger

### UB in the C

When the C has undefined behaviour, the port follows this ladder. Take the
first step that fits:

1. **UB that compilers define in practice** (signed overflow, shifts into the
   sign bit, arithmetic on a NULL pointer): reproduce what the compiler
   actually does with defined Rust operations: `wrapping_*`, or integer
   address math (`wrapping_offset`). The result is the same and the UB is gone.
   libubox: `id << 24` in `blob_init`, `wrapping_add` in `blobmsg_new`.
2. **Out-of-bounds access where Rust has the bound** (a negative index into a
   `static` table): let Rust's check trap. With `panic = "abort"` the process
   aborts, where C reads adjacent memory. libubox: `blob_type_minlen[type]`
   with a negative `type`.
3. **Rust cannot know the bound** (a length the caller supplies for the
   caller's own arrays): keep the C behaviour inside `unsafe`, using raw-pointer
   reads and writes with the same sign extension. libubox:
   `blobmsg_parse_array` with `policy_len <= 0`.

**Never invent a guard.** A guard returns a value the C never defines, so it is
a new API, not a port. A guard arrives only when upstream adds it, and a resync
absorbs it (libubox: upstream 4811166 guards `blobmsg_parse`, so the Rust has
that guard; `blobmsg_parse_array` has none, so the Rust has none).

### Overflow must not depend on the build profile

- Use `wrapping_*` wherever the C wraps: all unsigned arithmetic, and every
  signed operation that step 1 reproduces.
- Set `overflow-checks` to the same value in the dev and release profiles:
  `true` by default, so an overflow the porter missed traps in every build, as
  in step 2. If that fails the size gate, set `false` in both and record it in
  the plan.

The reason: with the cargo defaults, `+` on a C-derived integer panics in dev
and wraps in release. The oracle builds release, so no test sees the
difference.

### Stack allocation (alloca, VLA)

Rust has no `alloca` or VLA, and the `no_std` default has no heap.

- **The C caps the size:** reserve a fixed worst-case array
  (`MaybeUninit<[T; N]>`, left uninitialised like the alloca block). Results
  match; the stack profile does not, because the frame is always the worst
  case, even on early returns. It gets a ledger entry with class `stack`, and
  its Risk names small thread stacks. libubox: `blobmsg_parse`, capped at 8 KiB.
- **The C has no cap:** the function stays C (keep it as a C helper) until
  Phase 2.

### The exceptions ledger

Each Rust crate has one ledger, `DIVERGENCES.md` at the crate root. Its header
names the C files it covers and the pinned reference SHA. It records every
deliberate difference between the Rust and the C, so a resync knows what to
re-check.

**What gets an entry:**

- every UB case, at any ladder step, **including step 3**: UB kept identical
  inside `unsafe` is still a fact a resync must re-check;
- every `stack` divergence;
- any other behaviour difference a review accepted.

**What gets no entry:** an implementation-defined conversion that `as`
reproduces exactly (`size_t → int → u16` truncation). Rust's `as` truncates
the way gcc and clang do on every target Rust supports, so it is not a
divergence. It needs an entry only when the Rust result differs from the C
build's, or differs between supported targets.

**Entry shape.** Ids are `D<n>`, assigned in order, never renumbered or reused;
a removed divergence keeps its id, marked `Resolved` with the commit.

```markdown
## D4: `alloca` scratch array in `blobmsg_parse`
- Class: stack            (ub-defined | ub-trap | ub-kept | stack | other)
- Rust: `src/blobmsg.rs`, `blobmsg_parse` (`MaybeUninit<[u16; 4096]>` local).
- C: `blobmsg.c:blobmsg_parse` (`pslen = alloca(policy_len * sizeof(*pslen))`).
- C behaviour: what the C does, including what is undefined.
- Rust behaviour: what the Rust does instead, and what it relies on
  (`panic = "abort"`, overflow-checks).
- Why: the ruling, and who made it.
- Evidence: how the case is reached: from wire bytes, or only from a caller's
  arguments or compile-time tables. Cite the C lines and the tests that cover it.
- Risk: the cost if this entry is wrong. Required.
```

**The ledger goes in the gate's diff.** A unit's new or changed entries are
part of the diff the faithful-port gate reviews. The gate re-derives each
C-behaviour and Evidence claim from the C. A false claim is IMPORTANT, because
tests cannot catch a wrong claim in prose (libubox: an entry claimed
`blob_add` rejects negative payloads; it does not). A divergence with no entry
is a finding at its own severity; for `stack` it is IMPORTANT.
