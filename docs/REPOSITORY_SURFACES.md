# Repository surfaces

The project deliberately separates the product from its deeper evidence.

## `main`

The public, product-first source tree: application code, required assets,
installation and usage help, licensing, current limitations, profiles, and
small contributor tools.

## `evidence`

Version-matched release evidence: audit output, verification logs, screenshots,
retained source media, detailed provenance, independent reviews, and historical
handoffs. Each release folder records the corresponding product commit and
archive hashes.

## Local/private workspace

Unfinished experiments, raw model handoffs, art source, scratch packages, and
other working material may remain local or private. It is not part of the normal
user path.

The split is about audience, not secrecy. The main branch should be easy to use;
the evidence branch should remain inspectable for people who care.
