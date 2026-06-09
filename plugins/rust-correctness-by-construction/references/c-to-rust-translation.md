# C → Rust Translation: Pattern Recognition & Tool Selection

This doc is for the workflow: **faithful safe translation → prove it works →
idiomatic upgrade.** It is organized the way that workflow actually hits you —
you're looking at a C construct and need to know which Rust tool it maps to, and
*which phase* to apply it in.

## The phasing discipline (read first)

The two passes have different goals, and conflating them is the main failure
mode:

**Phase 1 — faithful + safe.** The goal is a translation that (a) is sound (no
UB; any `unsafe` is concentrated behind a checked boundary), (b) preserves
observable behavior exactly, and (c) stays structurally close enough to the C
that a human or agent can *diff the two side by side and believe they match*.
That third constraint is the one people forget. If you refactor a tagged union
into a beautiful sum type in Phase 1, the diff no longer lines up with the C and
your behavioral proof gets much harder to trust. **In Phase 1, resist
cleverness.** Mirror the control flow, keep names close, keep the structure
recognizable.

**Phase 1.5 — prove it.** Establish behavioral equivalence with the C *before*
touching idioms. For driver/netstack work this is differential/behavioral
testing against the original — the same observable outputs (your DHCP lease,
ping RTT, iperf throughput, HDMI capture). Add MIRI over the test suite to vet
the `unsafe`, and Loom if there's hand-rolled atomics. Only once the faithful
version is trusted do you upgrade. See `verification-tools.md`.

**Phase 2 — idiomatic upgrade.** Now reach for the unrepresentable-states
toolbox. Each upgrade should be behavior-preserving (most type-level refactors
are, by construction) and you re-run the same oracles after each one, so a
regression is bisectable to a single upgrade. This is where the rest of this
skill's docs come in.

The per-pattern entries below are tagged:
- **[P1]** — do this in the faithful pass; the safe translation *is* the
  idiomatic one (or close enough that it doesn't obscure the diff). Free win.
- **[P2]** — defer to the idiomatic pass; it changes structure enough to
  complicate the equivalence proof.
- **[P1→P2]** — a P1 version and a better P2 version both exist; start safe,
  upgrade later.

## Quick lookup table

| You see in C | Phase 1 (faithful + safe) | Phase 2 (idiomatic) | Detail / see |
|---|---|---|---|
| `NULL` for "no value" | `Option<&T>` / `Option<NonNull<T>>` | same | §1 |
| Return `-EINVAL` / errno | `Result<T, i32>` or error newtype | `Result<T, Error>` enum + `?` | §2, type-system §1 |
| Out-param `int f(T *out)` | return value / tuple | `Result`, named return struct | §3 |
| `goto cleanup;` chains | early-return + manual cleanup | RAII / `Drop` / `?` | §4 |
| Tagged union (tag + `union`) | `enum` w/ data, or faithful union | sum type; illegal combos gone | §5, type-system §2 |
| Struct + `is_valid`/`state` flag | keep flag | sum type or typestate | §6, type-system §2/§4 |
| `int state; switch(state)` | `enum State` | typestate if state gates ops | §6, type-system §4 |
| `kref` / `refcount_t` get/put | `Arc`/`Rc` (or kernel `Arc`) | same | §7 |
| `list_head` intrusive list | raw ptrs in `unsafe`, or index/arena | `GhostCell`/`qcell`, `intrusive-collections` | §8, type-system §6 |
| `mutex_lock`/`unlock` pairs | `Mutex<T>` guard | guard + static lock order | §9, concurrency doc |
| Struct of fn pointers (ops) | keep fn-ptr struct | `trait` (dyn or generic) | §10 |
| `void *ctx` callback | `*mut c_void` + cast in `unsafe` | generic param / `Box<dyn>` / closure | §11 |
| `#define FLAG (1<<n)` + bit ops | integer consts | `bitflags!` | §12 |
| `char buf[N]; size_t len` | array/slice + len, or `heapless::Vec` | slices `&[u8]`, `heapless` | §13 |
| Cast buffer → header struct | `unsafe` ptr cast / transmute | `zerocopy` (`FromBytes`/`Ref`) | §14 |
| `union` for type punning | `zerocopy`/`bytemuck`, or match | same | §14 |
| `static` mutable global | `static mut`(unsafe)/`OnceLock` | pass state explicitly / `OnceLock` | §15 |
| `container_of(ptr,...)` | `offset_of!` + ptr math in `unsafe` | `intrusive-collections`, typed | §16 |
| Volatile MMIO reads/writes | `read_volatile`/`write_volatile` | typed register block (`tock-registers`) | §17 |
| Sentinel (`-1`, `0xFFFF` = none) | keep sentinel, comment it | `Option`, `NonZero*` niche | §18, type-system §1 |
| Unit in comment (jiffies, ms, bytes) | keep raw int | newtype / `uom` | §19, type-system §1/§8 |
| Manual bounds check before index | keep check / `.get()` | branded index, newtype index | §20, type-system §1/§6 |
| `char *` / `const char *` string | `*const c_char` + `CStr` at boundary | `&str`/`&CStr`/`String` | §21 |
| Self-referential struct, no-move | raw ptrs, `unsafe`, document | `Pin` + `pin-init` | §22, concurrency §9 |

---

## 1. NULL → Option [P1]

NULL-as-"absent" maps directly and safely to `Option`, and this is one of the
few upgrades that's *also* faithful — the diff still reads cleanly, so do it in
Phase 1. A nullable borrowed pointer becomes `Option<&T>`; a nullable owning raw
pointer that must stay raw (FFI, intrusive) becomes `Option<NonNull<T>>`. The
niche optimization makes `Option<&T>` and `Option<NonNull<T>>` the same size as
the pointer, so it's free. NULL-as-error is better modeled as `Result` (§2).

## 2. Error codes → Result [P1→P2]

**P1:** a function returning `-EINVAL`/`-ENOMEM` can translate to
`Result<T, i32>` or `Result<T, Errno>` (a thin newtype over the int), preserving
the exact codes so behavior and the diff stay obvious. Keep the same codes.

**P2:** replace the integer with a domain error `enum` (each failure mode a
variant, optionally carrying context), thread it with `?`, and reserve
exhaustive `match` for callers that branch on the reason. This makes "forgot to
check the return" unrepresentable — you can't ignore a `Result` without a
warning, and `?` propagates correctly by construction. In `no_std`, hand-write
the enum (or use a `no_std`-friendly derive); avoid pulling in `std`-only error
crates.

## 3. Out-parameters → return values [P1→P2]

C's `int f(T *out)` (status code + result via pointer) is two return channels
welded together. **P1:** return a tuple `(status, value)` or fill a returned
struct — close to the C shape. **P2:** collapse to `Result<T, E>`; for genuine
in/out parameters use `&mut`, but only when the value is truly read-and-written.
Multiple outputs become a named struct, not a pile of `&mut` args.

## 4. goto-cleanup → RAII [P2]

The C `goto err_free_x;` ladder exists *because C has no destructors*. Rust does,
so the entire pattern dissolves. **P1:** to keep the diff legible you can mirror
the cleanup with early returns and explicit drops. **P2:** wrap each resource in
a type whose `Drop` releases it (or use existing RAII types — `Box`,
`MutexGuard`, file handles), and let `?` early-return safely; cleanup runs
automatically in reverse order. This is one of the highest-value upgrades: it
eliminates the classic C bug of a `goto` skipping or double-running a cleanup.

## 5. Tagged unions → sum types [P2]

A C `struct { enum tag; union { ... } u; }` is exactly the product-with-flags
that admits illegal states (tag says A, you read `u.b`). **P1:** translate to a
Rust `enum` carrying data if it's mechanical, or keep a faithful
`tag + union` (with `unsafe` field access) when the C does pointer tricks you
need to preserve for the proof. **P2:** lift to a clean sum type so the
tag/payload mismatch is unrepresentable and `match` is exhaustive. See
`type-system-patterns.md` §2.

## 6. Flag/integer state → sum type or typestate [P1→P2]

`bool is_initialized` next to fields that are only meaningful when set, or an
`int state` driven through a `switch`. **P1:** an `enum State { ... }` mirroring
the integer states is faithful and already safer (exhaustive match). **P2:** if
the state gates *which operations are legal* (you may only `send` on a connected
socket), promote it to **typestate** so illegal operations don't compile; if it
only gates *which data is present*, a **sum type** is enough. See
`type-system-patterns.md` §4 (typestate) and §2 (sum types). Judgment call:
typestate is worth it when the state machine is small and the illegal-operation
bugs are real; for many irregular states, the enum is clearer.

## 7. Manual refcounting → Arc/Rc [P1→P2]

`kref`, `refcount_t`, `get`/`put`, `_ref`/`_unref` pairs are reference counting
done by hand. They map onto `Rc` (single-threaded) or `Arc` (atomic). **P1:** if
the count is *intrusive* (embedded in the struct, as in the kernel) you may need
to keep it raw initially, or adopt the kernel `Arc` which wraps a C `refcount_t`
with saturating overflow. **P2:** ordinary heap refcounts become `Arc<T>` and
the get/put calls vanish into clone/drop. Watch for cycles (C code that relies on
manual breaking) — those need `Weak`.

## 8. Intrusive linked lists → GhostCell / arena / crate [P2]

`list_head`-style intrusive lists with aliased mutable nodes are the hardest C
pattern to translate, because they violate Rust's aliasing-xor-mutation head-on.
Options, roughly in order of how much they preserve the C structure:

- **P1, faithful:** keep raw `*mut Node` links inside `unsafe`, behind a safe
  API. Document the invariants. Vet heavily with MIRI. This is legitimate for
  the faithful pass.
- **P2, index/arena:** store nodes in a `Vec`/slab and replace pointers with
  indices (ideally *branded* indices so they can't be used with the wrong arena
  — `type-system-patterns.md` §6). No `unsafe`, cache-friendly.
- **P2, GhostCell/qcell:** keep the pointer-graph shape but separate permission
  from data, so a single token grants safe mutation of the whole list with no
  per-node `RefCell`. The closest safe analogue to the C structure.
- **P2, crate:** `intrusive-collections` provides ready-made intrusive lists/
  trees with a safe interface.

## 9. Lock/unlock pairs → guarded data + static order [P1→P2]

`mutex_lock(&m); ... mutex_unlock(&m);` around accesses to some shared field.
**P1:** put the protected data *inside* a `Mutex<T>` so the only way to touch it
is to hold the guard (the guard pattern), and let the guard's `Drop` do the
unlock — this already eliminates "unlock-skipped" and "use-without-lock" bugs.
**P2:** if there are multiple locks with an acquisition order (and in a netstack
there will be), encode that order in the type system so cycles are a compile
error. See `concurrency-lock-ordering.md` — this is the centerpiece for your
domain.

## 10. Ops structs (struct of function pointers) → traits [P2]

The C polymorphism idiom — `struct foo_ops { int (*read)(...); ... };` — is a
vtable by hand. **P1:** keep it as a struct of `fn` pointers / `Option<fn>`;
faithful and works. **P2:** define a `trait` with those methods. Use `dyn Trait`
when you need runtime dispatch over heterogeneous implementors (mirrors the C
most closely), or a generic `T: Trait` bound when the type is known statically
(zero-cost). A trait also lets you make required methods non-optional, killing
the C "forgot to set a function pointer → NULL deref" bug.

## 11. void* context → generics / trait objects / closures [P2]

`void *ctx` threaded through callbacks is type-erased state. **P1:** translate as
`*mut c_void` with a cast back inside `unsafe` at the callback — faithful but
unsafe. **P2:** make the callback generic over the context type, or take a
`Box<dyn FnMut(...)>` / `&mut dyn Trait`, or a closure that captures the context.
The type erasure and its attendant `transmute` disappear.

## 12. Bitflags → the bitflags crate [P1→P2]

`#define X (1u<<0)` plus `flags |= X` / `flags & X`. **P1:** keep the integer
constants — it's faithful and the bit ops are unchanged. **P2:** `bitflags!`
generates a newtype with named flags, type-safe set operations, and no risk of
mixing flag namespaces (you can't OR a `FileFlags` into a `PageFlags`). Cheap,
behavior-preserving, worth doing.

## 13. Fixed buffers + length → slices / heapless [P1→P2]

`char buf[256]; size_t len;` with manual length bookkeeping. **P1:** an array
`[u8; 256]` plus a `len`, or pass `&[u8]`/`&mut [u8]` slices at call boundaries
(faithful and bounds-checked). **P2:** `heapless::Vec<u8, 256>` carries the
capacity in the type and the length internally, never allocates, and makes
overflow a checked operation; or just use slices throughout and let the length
live in the slice. Eliminates manual length/overflow bugs.

## 14. Buffer↔struct casts → zerocopy [P2]

Parsing wire formats by casting `buf` to a `struct packet_hdr *`, or `union`
type-punning, is pervasive in netstack/driver code and is UB-adjacent in C and
genuinely UB if done naively in Rust. **P1:** an `unsafe` pointer cast /
`read_unaligned`, with alignment and length checked first. **P2:** use
**`zerocopy`** (`FromBytes`, `IntoBytes`, `KnownLayout`, `Unaligned`, and
`Ref<_, Hdr>` for zero-copy views over a byte slice) or **`bytemuck`** (`Pod`,
`Zeroable`). These make "interpret these bytes as this struct" a *safe*,
checked, zero-copy operation — no `unsafe` at the call site. (`zerocopy` is by
the Netstack3 author and is built for exactly this kind of code.)

## 15. Mutable globals → OnceLock / explicit state [P1→P2]

A `static` global mutated at runtime. **P1:** `static mut` is `unsafe` to touch
and easy to get wrong; prefer `OnceLock`/`OnceCell` for init-once globals, or a
`Mutex`/atomic for mutable ones, even in the faithful pass. **P2:** the most
idiomatic move is often to *stop having the global* — thread the state through
explicitly (the `Locked` context in `concurrency-lock-ordering.md` is an example
of state-as-parameter), which also makes test isolation possible.

## 16. container_of → offset_of! / intrusive-collections [P2]

`container_of(ptr, type, member)` recovers a struct pointer from a pointer to one
of its fields. **P1:** `core::mem::offset_of!` (stable since 1.77) plus pointer
arithmetic inside `unsafe`, mirroring the macro. **P2:** if the reason for
`container_of` was an intrusive collection, switch to `intrusive-collections`
and the pattern goes away entirely.

## 17. Volatile MMIO → typed register blocks [P1→P2]

Device register access via `*(volatile u32*)addr`. **P1:** `read_volatile` /
`write_volatile` on a raw pointer, in `unsafe`, preserves exact access semantics
— do this faithfully first (volatile ordering and width matter for hardware).
**P2:** wrap the register block in a typed abstraction (`tock-registers`,
`volatile-register`, or an svd2rust-generated PAC) so each register has a type,
fields are typed bitflags, and read-only/write-only is enforced. The volatile
access stays correct but misuse (writing a read-only register, wrong width)
becomes a compile error.

## 18. Sentinel values → Option / NonZero [P1→P2]

`-1`, `0xFFFFFFFF`, or `0` standing in for "none/invalid". **P1:** keep the
sentinel and *comment it loudly* so the proof reviewer knows the magic value.
**P2:** `Option<T>` for the general case; `NonZeroU32` etc. when zero is the
sentinel (the niche makes `Option<NonZeroU32>` free). Now "forgot to check for
the sentinel" is unrepresentable — you must handle the `None`.

## 19. Units in comments → newtypes / uom [P2]

C encodes units in names and comments: `timeout_ms`, `size_in_pages`, `jiffies`.
**P1:** keep the raw integer. **P2:** a newtype (`struct Millis(u64)`,
`struct Pages(usize)`) or `uom` makes unit mismatches a type error. High value
where a unit mix-up is a real, expensive bug (timers, memory sizing, network
MTUs). See `type-system-patterns.md` §1 and §8.

## 20. Manual bounds checks → typed/branded indices [P2]

C code that validates `idx < len` before `arr[idx]`. **P1:** keep the check, or
use `slice.get(idx)` returning `Option` (faithful and safe). **P2:** for indices
that index a *specific* container and must not be used elsewhere, a branded index
(`type-system-patterns.md` §6) makes "used the index with the wrong array"
unrepresentable; a plain newtype index documents intent and prevents mixing index
spaces.

## 21. C strings → CStr / str at the boundary [P1]

`char *` / `const char *`. **P1:** at the FFI boundary keep `*const c_char` and
convert with `CStr::from_ptr` (unsafe, but the right safe-ish conversion point);
for owned C strings use `CString`. Internally, prefer `&str`/`String` for UTF-8
text and `&CStr`/`CString` for NUL-terminated C-ABI strings. Doing the conversion
*at the boundary* and using Rust string types inside is both faithful and
idiomatic, so it's largely a Phase 1 move.

## 22. Self-referential / no-move structs → Pin + pin-init [P2]

C structs that embed list nodes, locks, or back-pointers and must not be moved
after registration. **P1:** raw pointers and `unsafe`, with the no-move invariant
documented. **P2:** `Pin` plus `pin-init` for sound in-place initialization, so
"initialized in place, never moved" becomes a type-level fact. See
`concurrency-lock-ordering.md` §9 and the Rust-for-Linux `pin-init` exemplar.

---

## Reading ownership intent out of C

The hardest part of Phase 2 isn't syntax — it's that **C encodes ownership in
conventions, and Rust encodes it in types.** Most of the idiomatic upgrade is
lifting those conventions into the type system. Learn to read the cues:

- **Naming:** `_get`/`_put`, `_ref`/`_unref`, `_hold`/`_release` → refcounting →
  `Arc` (§7). `_dup`/`_clone` → an owned copy. `_borrow`/`_peek` → a borrow,
  `&T`. `_take`/`_steal` → ownership transfer, return/accept `T` by value or
  `Box<T>`.
- **Who calls `free`:** if the *caller* frees what a function returns, the
  function transfers ownership → return `Box<T>`/`T`/`Vec<T>`. If the *callee*
  retains and frees later, it's borrowing or sharing → `&T` or `Arc<T>`.
- **`const` qualifiers:** `const T *` argument → `&T`. `T *` that's written
  through → `&mut T`. `T *` that's stored → ownership or shared ownership.
- **Comments:** "caller owns", "takes ownership of", "the buffer must outlive",
  "borrowed reference, do not free" — these are lifetime and ownership
  annotations waiting to become `&'a`, `Box`, or `Arc`.
- **Lifetime hints:** "must remain valid until X" → a borrow with a lifetime tied
  to X, or shared ownership so it lives long enough.

A useful Phase 2 habit: for each translated function, write down the ownership
contract you *inferred* from these cues as a doc comment, then encode it in the
signature. If you can't decide between `&T`, `Box<T>`, and `Arc<T>`, that
uncertainty is exactly what the C left implicit — resolve it deliberately and the
type now documents it forever.

## What NOT to upgrade

Idiomatic does not mean "maximally clever." Leave it alone when:

- **The FFI boundary itself.** Functions that are still called from C, or that
  call C, keep their raw `extern "C"` signatures and `repr(C)` layouts. The
  `unsafe` shim is the boundary; don't try to make the ABI surface "nice".
- **`repr(C)` layout matters.** Structs shared with hardware or C must keep their
  exact layout; don't reorder fields for an enum refactor.
- **A type-level encoding would be write-only.** If the trait bounds needed to
  make something unrepresentable are unreadable to the team, you've traded a
  findable bug for an unmaintainable abstraction. Stay on a lower rung and check
  at runtime (see SKILL.md "When NOT to climb").
- **The behavior would change.** If an upgrade can't be made behavior-preserving,
  it's not part of the faithful-translation contract — flag it as a separate,
  reviewed change, not folded silently into the idiomatic pass.

## How this drives the agent loop

Concretely, for an agent doing a translation pass:

1. **Scan the C for the patterns in the lookup table.** Each match is a planned
   edit with a known target.
2. **In Phase 1, apply only [P1] mappings** plus faithful versions of [P1→P2]
   ones. Keep [P2] items as a TODO list attached to the code, not as edits.
3. **Prove behavioral equivalence** (the oracles) and run MIRI/Loom on the
   `unsafe`/concurrency. Don't proceed until green.
4. **In Phase 2, work the TODO list**, applying one [P2]/[P1→P2] upgrade at a
   time and re-running the oracles after each, so any regression bisects to one
   upgrade. Route each upgrade through the relevant reference doc.
5. **Record the inferred ownership contract** in each signature as you go.
