# Foundational Papers & Essays

Primary sources behind the patterns in this skill. When teaching or justifying a
technique, cite from here rather than from a tutorial. Grouped by tradition.

## The "illegal states unrepresentable" philosophy

- **Yaron Minsky — "Effective ML" / the original slogan.** Minsky coined "make
  illegal states unrepresentable" in a 2010 Harvard guest lecture, in the
  OCaml/Jane Street context. The canonical example converts a flat
  `connection_state` record with nullable fields into a sum type so the
  impossible combinations can't be written. See blog.janestreet.com/effective-ml/
  and the community wiki at functional-architecture.org/make_illegal_states_unrepresentable/.
  *Teaches:* the core philosophy and the product→sum refactor.

- **Scott Wlaschin — "Designing with Types: Making illegal states
  unrepresentable."** fsharpforfunandprofit.com/posts/designing-with-types-making-illegal-states-unrepresentable/,
  expanded in the book *Domain Modeling Made Functional*. The contact-info
  example (email OR postal address, never neither) is the canonical teaching
  case. *Teaches:* domain modeling with sum types; the F# lineage.

- **Richard Feldman — "Making Impossible States Impossible," elm-conf 2016.**
  youtube.com/watch?v=IcgmSRJHu_8. Popularized the principle for application
  state: the most expensive bugs are the "this shouldn't be possible" ones, and
  a good model lets the compiler rule them out up front. *Teaches:* the
  motivation, accessibly; good to quote when persuading a skeptic.

- **Alexis King — "Parse, don't validate" (2019).**
  lexi-lambda.github.io/blog/2019/11/05/parse-don-t-validate/. The most-cited
  modern essay. A parser maps less-structured to more-structured data and
  *preserves the evidence* in the type; a validator throws the evidence away.
  Maxims: "use a data structure that makes illegal states unrepresentable,"
  "push the burden of proof upward as far as possible, but no further," and the
  "shotgun parsing" anti-pattern. *Teaches:* where to validate and what to
  return when you do. The intellectual core of `type-system-patterns.md` §3.

## Ghost / branded types & proofs

- **Matt Noonan — "Ghosts of Departed Proofs (functional pearl)," Haskell 2018.**
  doi 10.1145/3242744.3242755; PDF kataskeue.com/gdp.pdf; repo
  github.com/matt-noonan/gdp-paper. Encodes sophisticated preconditions as
  *proofs* inhabiting phantom type parameters on newtype wrappers, with no
  runtime cost, and crucially lets the *library user* choose when and how to
  discharge the proof. *Teaches:* the conceptual parent of branded-API design;
  read before designing a proof-carrying newtype API.

- **Yanovski, Dang, Jung, Dreyer — "GhostCell: Separating Permissions from Data
  in Rust," ICFP 2021.** doi 10.1145/3473597; project + PDF at
  plv.mpi-sws.org/rustbelt/ghostcell/. Separates a structure's permission
  (`GhostToken<'id>`) from its data (`GhostCell<'id, T>`) using a unique
  invariant `'id` brand, giving zero-cost interior mutability over aliased
  structures (graphs, linked lists) and safe concurrent reads. Soundness proven
  by extending RustBelt in Coq. *Teaches:* the permission/data split and the
  branding that makes it sound; the basis for `qcell`'s `LCell`.

- **Generativity lineage.** The branding trick descends from Launchbury & Peyton
  Jones's `ST` monad (1995) and was named "generativity" for Rust in Aria
  Beingessner's 2015 MSc thesis. Arhan Chaudhary's "The Generativity Pattern in
  Rust" (arhan.sh/blog/the-generativity-pattern-in-rust/) is the best modern
  walkthrough and ties the history together. *Teaches:* why invariant,
  per-call-unique lifetimes brand values; underpins the `generativity` crate.

## Typestate & session types

- **Duarte & Ravara — "Retrofitting Typestates into Rust," SBLP 2021.**
  doi 10.1145/3475061.3475082. The formal basis for the `typestate` proc-macro
  crate; formalizes encoding typestate automata in Rust's type system.
  *Teaches:* the general typestate-as-types construction and its limits.

- **Chen, Balzer, Toninho — "Ferrite: A Judgmental Embedding of Session Types in
  Rust," ECOOP 2022.** arxiv.org/abs/2205.06921; PDF
  cs.cmu.edu/~balzers/publications/ferrite.pdf; repo github.com/ferrite-rs/ferrite.
  Embeds linear and shared session types so a well-typed program is a proof of
  protocol adherence; addresses Rust's affine (not linear) types via a linearity
  encoding. *Teaches:* compile-time protocol correctness for channels/IPC.

## When types aren't enough (refinement & verification)

- **Lehmann, Lampropoulos, et al. — "Flux: Liquid Types for Rust," PLDI 2023.**
  doi 10.1145/3591283; arxiv.org/abs/2207.04034. Adds refinement (liquid) types
  to Rust as a rustc plugin, with inference that keeps annotation overhead low;
  used to verify process isolation in Tock OS. *Teaches:* the boundary between
  what types express cheaply and what needs refinements; see
  `verification-tools.md` for the tool itself.

## Recommended reading order

1. King, "Parse, don't validate" — the mindset.
2. Wlaschin or Feldman — the philosophy, accessibly.
3. Cliffle's typestate post (linked in `exemplar-codebases.md`) — the workhorse
   Rust pattern.
4. GhostCell paper — the sophisticated end of branded/permission types.
5. Liebow-Feeser RustConf 2024 (in `concurrency-lock-ordering.md`) — the systems
   payoff.
6. Ghosts of Departed Proofs — if you're designing proof-carrying APIs.
