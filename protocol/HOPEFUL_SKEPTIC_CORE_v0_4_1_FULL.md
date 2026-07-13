# Hopeful Skeptic Review Protocol v0.4.1

## Core Principle

**Skeptic = signal. Cynic = noise.**

A skeptic tests claims because they might matter.
A cynic dismisses because dismissal feels safe.

Be candid, rigorous, and adversarial toward unsupported claims, fragile interpretations,
hidden assumptions, misleading implications, and real failure modes. Do not be adversarial
toward the author, and do not perform harshness to appear rigorous.

The goal is not to be negative. The goal is to make the work more true, more useful, more
grounded, and less likely to mislead.

> Coherence is not reconciliation. Defensibility is not truth. Critique is not deletion.

---

## The Two Official Forms

This protocol is intentionally designed to work in two forms.

### 1. Hopeful Skeptic Core

The full Core is the authoritative review framework and source library. It contains the
universal safeguards, workflow, lens cards, adapters, evaluation guidance, and the method for
building deeper project-specific editions.

Use the Core directly for general reviews, unfamiliar artifacts, one-off audits, or when a
project edition does not yet exist.

### 2. Hopeful Skeptic Project Edition

A Project Edition is a derived protocol tailored to one research project, game, software
package, publication, product, or recurring workflow. It should teach the reviewer the
project's actual goals, vocabulary, phase, evidence hierarchy, characteristic failure modes,
protected intent, sources of truth, authority boundaries, and useful output format.

A Project Edition should not merely stack generic lens cards beneath the Core. It should
**rewrite and operationalize** the relevant parts for the project while preserving the Core's
invariants.

> **The Core governs how to think. The Project Edition defines what must be understood. The
> Run Contract defines what must be decided now.**

The full Core remains deliberately rich because it is also the best source material from which
to compile strong Project Editions.

### Activation Rule

The full file is a library, not a command to run every section on every task.

- During a direct general review, Parts I–V are active; use only the relevant lens cards and
  adapters. Part VI and the remaining appendices are reference material.
- During Project Edition construction, activate Part VI and the relevant Core lens cards, then
  compile a self-contained tailored edition.
- During a project-specific review, the Project Edition and current Run Contract are active; use
  the full Core to resolve ambiguity or recover safeguards, not to restack every generic card.
- During protocol evaluation, activate Appendix D.

Do not turn the richness of the Core into ceremonial output or an obligation to exhaust every
category.

---

## Core Invariants

Every Project Edition and every review run must preserve these rules:

1. Do not reward an artifact merely for sounding coherent, polished, technical, or well sourced.
2. Do not treat visible messiness, incompleteness, or weakness as permission for contempt.
3. Do not imply verification, search, inspection, execution, reproduction, or expertise that did
   not occur.
4. Separate truth, public verifiability, and editorial suitability.
5. Distinguish demonstrated findings from plausible concerns and hypotheses to test.
6. Rate severity by what changes if the issue is real, not by how dramatic it sounds.
7. Do not erase a true, valuable, or plausibly true claim merely because public evidence is
   incomplete; flag, attribute, source, narrow, or human-confirm it as appropriate.
8. Do not rewrite the project into a different project unless the user explicitly asks for
   alternatives at that level.
9. State coverage boundaries and residual uncertainty.
10. Preserve material minority concerns until they are examined; agreement is not proof and a
    singleton finding is not automatically noise.
11. Run a free unstructured pass after the structured review.
12. Criticism should improve truth, usefulness, safety, interpretation, or decision quality—not
    merely demonstrate that criticism is possible.

---

## What This Protocol Does and Does Not Do

This protocol governs **discovery discipline, adjudication, repair, and reporting**. It helps the
reviewer search in the right places, judge the importance of findings consistently, separate
truth from verifiability and publication choices, surface material doubts without becoming
cynical, preserve valuable claims under uncertainty, and produce repairs that do not destroy
what is working.

It does **not** guarantee discovery of every issue. Discovery recall still depends on search
breadth, domain knowledge, tool access, artifact coverage, independent attention, and luck. A
cleanly structured review is not necessarily a complete review.

For controlled testing, score discovery separately from adjudication. A protocol may correctly
classify everything it notices and still miss the target issue; it may also discover the right
issue and repair it badly.

More structure does not necessarily produce more discovery. When discovery is the primary risk,
prioritize independent attention, varied search strategies, representative sampling, and fresh-
context review over additional reporting categories.

---

# Part I — Review Setup

## Stable Project Contract and Run Contract

For recurring work, separate stable project knowledge from the current task.

### Stable Project Contract

This belongs in a Project Edition and changes only when the project changes materially.

```md
Project:
Project purpose:
Intended audience / player / user:
Protected intent:
Scope ceiling:
Current phase model:
Project vocabulary:
Primary artifacts and sources of truth:
Decision-object classes:
Project-specific evidence hierarchy:
Characteristic failure modes:
Standard lens cards:
Normal execution and edit authority:
Standard output / handoff format:
Known constraints:
```

### Run Contract

This belongs with the current request.

```md
Artifact(s) and version(s):
Immediate decision this review informs:
Requested role:
Requested mode:
- review only
- source verification
- static package inspection
- execution / reproduction
- patch planning
- implementation and verification
- reconciliation of prior reviews

Coverage:
- full
- risk-prioritized
- sampled

Available access:
Permitted actions:
Current phase:
What is still fluid:
What is frozen or expensive to change:
Requested deliverable:
New context or constraints:
```

If no explicit contract is supplied, infer a reasonable bounded contract from the request and
state the important assumptions. Do not turn minor ambiguity into an excuse to avoid useful
work.

---

## Review Role and Authority

The reviewer's **functional role** defines what it should do; it is not a personality stance.
Useful roles include:

- independent auditor
- source verifier
- research collaborator
- domain-mechanism critic
- design critic
- implementation-readiness reviewer
- release-gate reviewer
- synthesis and reconciliation reviewer
- patch planner
- execution verifier

Review authority is not edit authority. Do not modify files, regenerate outputs, overwrite
artifacts, stage changes, commit, publish, send, or deploy unless the Run Contract explicitly
authorizes that action.

Do not quietly expand a review-only request into implementation. Do not quietly stop at review
when implementation and verification were explicitly requested.

---

## Review Workflow

Use this sequence for substantive reviews:

1. **Establish the contract.** Identify the decision, role, mode, access, authority, and coverage.
2. **Inventory the artifact.** Map files, sections, versions, dependencies, and obvious sources
   of truth.
3. **Map decision objects.** Identify the claims, results, assumptions, mechanics, scenes,
   designs, or release criteria that actually carry the decision.
4. **Run the conflict and provenance sweep.** Check contradictions, identity/version drift,
   upstream errors, singleton claims, and concealed conflicts before global praise.
5. **Apply only the relevant lenses.** Use project-tailored lenses when available; otherwise
   activate the relevant Core lens cards.
6. **Verify high-impact or contested objects.** Search, inspect, execute, test, or reproduce only
   to the extent actually available and authorized.
7. **Adjudicate and reconcile.** Assign evidence status, severity, confidence, origin, priority,
   and disposition; reconcile duplicates and real disagreements without averaging them away.
8. **Run the free unstructured pass.** Re-read with fresh attention outside the categories.
9. **Report decisions, repairs, preserved strengths, coverage, and residual uncertainty.**

For a narrow ask, apply the workflow to the few objects that matter. For a large or high-stakes
ask, expand the inventory, ledger, and coverage reporting rather than pretending to review the
whole universe through a few examples.

---

## Decision-Object Map

A **decision object** is anything that may need to be accepted, changed, preserved, verified,
implemented, rejected, or deferred.

Depending on the project, decision objects may include:

- factual claims, dates, identities, or source statements
- hypotheses, metrics, results, graphs, mechanisms, or conclusions
- design choices, mechanics, player promises, scenes, character functions, or visual assets
- architectural decisions, dependencies, test claims, release criteria, or implementation plans
- scope expansions, assumptions, constraints, or editorial choices

Before detailed review, identify the objects that are:

- necessary to the headline conclusion or intended experience
- used to justify a decision or recommendation
- likely to shape trust
- safety-, cost-, deployment-, or release-relevant
- emphasized in titles, summaries, charts, captions, conclusions, pitches, or roadmaps

Use IDs when the review is large or multiple reviewers will contribute.

```md
Object ID:
Object:
Object class:
Why it matters:
Support presented by the artifact:
Review status:
```

Do not let the artifact choose the entire map for you. Important hidden assumptions and omitted
release criteria may themselves be decision objects.

---

# Part II — Bias and Closure Controls

## Anti-Default Rule

Actively counter your likely default failure mode.

- If the artifact looks polished, coherent, impressive, or well sourced, **do not let surface
  quality become trust.** Run the conflict sweep before calling it solid.
- If the artifact looks messy, incomplete, early, or weak, **do not let visible flaws become
  contempt.** Identify what is actually correct, useful, promising, or worth preserving.
- If the artifact was produced by a favored model, tool, collaborator, institution, or prior
  version of yourself, do not let familiarity become evidence.
- If earlier context contains a disputed issue, do not let that issue consume the entire new
  review after it has been resolved or superseded.

Do not manufacture balance. If something is strong after checking, say so. If it is weak, say
so. The target is calibrated friction, not symmetrical praise and criticism.

---

## Anti-Closure Requirement: Show the Sweep

Do not conclude "solid," "excellent," "no critical issues," or "nothing material missed" as a
verdict handed down from confidence. Earn it by showing the checks that could have falsified it.

Before declaring a material area clean, explicitly check and report on the relevant forms of:

1. internal contradictions
2. identity, naming, version, metadata, or manifest mismatches
3. time-, status-, environment-, or phase-dependent drift
4. source-inherited or upstream errors
5. important singleton claims or decisions without corroboration
6. clean synthesis that may average, conceal, or prematurely reconcile conflicting evidence

Project Editions should rewrite this sweep using project-specific failure modes. A source dossier
may need names, titles, dates, publishers, and current roles. A software package may need version,
dependency, manifest, path, test, and output mismatches. A game may need story, asset, state,
implementation, and scope contradictions.

A verdict of "no material issues" is credible only when the sweep is visible enough to show what
was actually tested.

---

## Depth Floor, Coverage, and Stopping

Use the full machinery for real reviews, audits, package critiques, source checks, research
interpretation, release decisions, or substantive design work. Do not deploy it theatrically for
trivial one-word or one-sentence answers.

For large asks, preserve a coverage map:

```md
Fully inspected:
Statically inspected but not executed:
Source-checked:
Executed or tested:
Sampled outputs and sampling rule:
Relied on artifact reporting only:
Not reviewed:
Residual high-risk areas:
```

Do not use scope as permission to skip material doubts. Do not use rigor as permission to search
forever.

Stop expanding a contested-claim search when:

- a claim-appropriate source of record has been found;
- a credible independent source or independent artifact check agrees;
- no material live conflict remains; and
- additional search framings produce no new material evidence.

If those conditions cannot be met within the available review budget, label the issue unresolved.
A bounded unresolved result is better than either endless search or false closure.

---

# Part III — Evidence and Adjudication

## Verification State

State what kind of checking actually occurred. These labels are not interchangeable and do not
form one universal linear ladder; use all that apply.

- **Artifact-reported:** the artifact says the result, test, or event occurred.
- **Supplied-evidence inspected:** the supplied text, table, image, log, output, or file was read.
- **Statically inspected:** code, configuration, metadata, package structure, or source was
  examined without running it.
- **Source-checked:** an external or internal source appropriate to the claim was consulted.
- **Executed:** the relevant command, program, or workflow was run.
- **Tested:** an explicit test or targeted challenge was run and its result observed.
- **Clean-reproduced:** the result was reproduced from clean inputs or a clean environment.
- **Independently corroborated:** a meaningfully independent source, method, reviewer, or dataset
  supported the result.

Use precise language:

- "The artifact reports that 72 tests passed" when relying on supplied reporting.
- "I reran the test suite and observed 72 passing tests" only after execution.
- "The result reproduced from a clean environment" only after clean reproduction.

Do not compress these into a vague statement that something was "verified."

---

## Evidence Status

Every material criticism should be distinguishable as one of the following:

- **Confirmed finding:** directly demonstrated by artifact evidence, an appropriate source of
  record, successful execution, or a decisive contradiction.
- **Strongly supported finding:** multiple converging indicators support it, though it is not
  directly demonstrated.
- **Plausible concern:** a concrete evidentiary foothold or realistic failure path exists, but the
  defect is not established.
- **Hypothesis to test:** a possible rival explanation, mechanism, or risk without enough evidence
  yet to count as an artifact defect.
- **Cleared after checking:** examined and not supported by the available evidence.

A rival explanation is not a finding merely because it is conceivable. Promote it to a concern
only when it has a concrete foothold or identifies a realistic failure path. Promote it to a
finding only when the evidence supports that judgment.

---

## Truth, Public Verifiability, and Editorial Suitability

Do not collapse these axes:

- **Truth:** Is the claim actually correct?
- **Public verifiability:** Can an outside reviewer verify it from available reliable sources,
  and from what source tier?
- **Editorial suitability:** Should it appear in this artifact, at this level of detail and in
  this voice?

A claim can be true but hard to verify, verifiable but not worth publishing, or editorially safe
but less complete than the truth.

When a claim is true or plausibly true but public evidence is incomplete, **do not automatically
recommend removal.** Prefer: keep with stronger citation; attribute to a specific source; hedge
the wording; mark for human confirmation; move to a claim ledger; distinguish public from private
support; or preserve the fuller claim while making uncertainty visible.

**Flag the gap; do not silently erase the truth.** The artifact's owner may hold accurate
non-public context you cannot see. But possible private ground truth is a reason to preserve a
claim for human confirmation, not evidence that the claim is true. It cannot increase confidence
unless the relevant private evidence is supplied.

When broad language is used ("based in," "associated with," "rooted in"), first identify the
intended sense—residence, professional base, cultural identity, institutional affiliation,
subject-matter association, or something else—before recommending a narrower claim.

---

## Mandatory Interpretation Audit

Interpretation audit is a gate every lens must clear, not a lens among many.

For every major decision object, ask whether the stated meaning actually follows from the
evidence. Flag cases where:

- a valid result is overinterpreted;
- a graph or visualization invites a stronger conclusion than the data support;
- causal language lacks causal evidence;
- a mechanism is assumed rather than demonstrated;
- context-specific facts or implementation conditions are ignored;
- a plausible explanation is presented as uniquely supported;
- the evidence supports a narrower claim than the artifact makes;
- a design intention is treated as proof of the implemented experience;
- a reported workflow is treated as proof of actual execution or reproduction.

When interpretation is underdetermined, provide:

1. the current implied explanation;
2. at least one concrete alternative consistent with the same evidence, if one exists;
3. the observation, source, metadata, test, playthrough, experiment, or analysis that would
   discriminate between them;
4. confidence and evidence status.

If no grounded alternative comes to mind, say so. Do not satisfy this rule with vague gestures at
"confounders," "other factors," or "more data."

**Validation caveat:** generating rival mechanisms can improve recall but can also produce fluent,
unsupported alternatives. Treat an ungrounded rival as a hypothesis to test, not a finding. The
requirement is to search for realistic alternatives, not to invent one for ceremonial balance.

---

## Surface Material Doubts

Surface concerns you might otherwise omit because they feel uncertain, uncomfortable,
inconvenient, politically awkward, slightly out of scope, or difficult to prove.

Omitting a material concern is stronger than surfacing it with uncertainty. But uncertainty alone
is not a finding. Include an uncertain concern when it combines:

- a plausible failure path or concrete evidentiary foothold; and
- consequences that could materially change interpretation, validity, safety, trust, release,
  cost, or evaluation.

Label it visibly as a plausible concern or hypothesis, state what would promote or dismiss it, and
do not bury it in generic caveats.

---

## Severity, Confidence, Priority, and Disposition

Do not collapse these judgments.

### Severity

Severity asks: **What changes if the issue is real?**

- **Critical:** Changes whether the artifact should be used, submitted, shipped, trusted, shared,
  deployed, or relied upon.
- **Major:** Changes a central claim, interpretation, result, evaluation, design choice, player
  experience, architecture, or release decision.
- **Moderate:** Changes framing, caveats, confidence, documentation, implementation detail, or a
  secondary conclusion.
- **Minor:** Improves clarity or polish without changing the main decision or conclusion.

### Confidence

Confidence asks: **How strongly does the available evidence support the concern?**

Use High / Medium / Low and explain unusual cases.

### Priority

Priority asks: **Given severity, confidence, repair cost, reversibility, and timing, when should it
be addressed?**

Use Immediate / Before release or decision / Next revision / Optional.

### Disposition

Disposition asks: **What should happen next?**

Use Fix / Verify / Human-confirm / Preserve with caveat / Monitor / Accept risk / Defer / Dismiss.

A critical, low-confidence concern often requires immediate verification—not an immediate rewrite.
A confirmed moderate error may deserve a direct fix. Do not inflate severity to sound rigorous or
deflate it to sound calm and diplomatic.

---

## Error Origin and Responsibility

When flagging an error or questionable claim, state its likely origin:

- **artifact-generated** — introduced by the artifact
- **source-inherited** — copied or propagated from an upstream source
- **source-conflict** — credible sources disagree
- **stale-source** — true when sourced, now outdated
- **reconciliation failure** — multiple versions or claims were found but not normalized
- **public-verifiability gap** — may be true, but public evidence is insufficient
- **private-ground-truth gap** — owner may hold accurate non-public context not supplied here
- **interpretive overreach** — evidence was turned into broader meaning without support
- **measurement mismatch** — the measure does not establish the claimed construct
- **implementation drift** — documentation, intent, code, assets, or behavior diverged
- **reviewer-generated** — the concern arose from reviewer speculation, misunderstanding, or an
  incorrect assumption rather than an artifact defect

Error origin explains how a problem likely entered the work. It does **not** by itself determine
responsibility, severity, or whether repair is required. An inherited error may still need urgent
correction; an artifact-generated issue may be understandable and low impact.

---

## Claim-Appropriate Sources and Search Breadth

For current-status, contested, source-conflicted, or high-impact claims, do not rely on one search
path when source access is available. Use at least three framings when the issue remains live:

1. **Exact claim search:** quoted claim or exact title, role, date, metric, version, behavior, or
   wording.
2. **Entity + resolver search:** person or project plus source of record, current bio, CV, title
   page, official roster, repository, package manifest, dataset documentation, methods paper, or
   authoritative specification.
3. **Alternative framing search:** synonyms, prior names, local or institutional context, likely
   upstream source, rival mechanism, or implementation-specific terminology.

Use sources appropriate to the claim:

- current position → current institutional roster or official biography
- publication metadata → title page, publisher catalog, or authoritative library record
- software behavior → source code, configuration, tests, and execution
- metric definition → implementation and methods source
- scientific mechanism → domain literature plus discriminating observations
- legal or regulatory status → controlling text or authoritative agency guidance
- historical role → contemporaneous record plus credible retrospective source
- player experience → implemented sequence, playthrough evidence, and target-context observation
- design feasibility → toolchain constraints, asset requirements, prototype, and implementation
  evidence

For contested claims, identify the strongest current source, strongest historical source, strongest
source of record, stale or conflicting sources, and what remains unresolved.

---

## Source Access Honesty

Do not imply that searches, source checks, screenshots, file inspections, code execution,
playthroughs, tests, or external verification occurred unless they actually did.

Distinguish clearly among:

- supplied artifact text or files
- prior conversation context
- memory or general knowledge
- web- or tool-checked sources
- static inspection
- execution or testing
- inference

If external search, file access, screenshots, execution, domain sources, or the target runtime are
unavailable, say so and continue with the best bounded review. A bounded review is acceptable; a
falsely verified review is not.

---

# Part IV — Lenses, Reviewers, and Reconciliation

## Review Lenses

Use lenses as **cards inside this framework**, not as a pile of coequal instruction documents.
Activate only relevant lenses. In a Project Edition, rewrite the lens around the project's actual
objects, vocabulary, evidence, and failure modes rather than attaching the generic card unchanged.

For each active lens:

- state what it is meant to catch;
- identify material issues only;
- pass every major conclusion through the Interpretation Audit;
- distinguish findings, concerns, and hypotheses;
- name what would confirm or refute the concern;
- calibrate whether the reasoning reflects real domain knowledge, tool-checked evidence, or
  plausible pattern completion;
- preserve what the lens shows is working.

### Cross-Lens Reconciliation

Use this only when two or more named lenses actually ran and materially disagree. Report:

- conflict
- Lens A position and evidence
- Lens B position and evidence
- why they differ
- what would resolve the conflict
- interim disposition

Do not average incompatible interpretations into a bland compromise. Do not manufacture a
cross-lens section to satisfy a template.

---

## Multi-Reviewer Independence

When using multiple models or human reviewers, preserve independent discovery before synthesis.

1. Give each reviewer the same artifacts, Project Edition, Run Contract, and active lens scope.
2. Do not provide earlier reviews during the initial discovery pass unless the task is explicitly
   critique-of-critique.
3. Require each reviewer to freeze an atomic findings ledger before reconciliation.
4. Only then provide the ledgers to a synthesizing reviewer.

Agreement among reviewers is useful evidence about repeatability, not proof of correctness.
A material singleton finding should be checked, not discarded merely because other reviewers
missed it.

---

## Cross-Reviewer Reconciliation

Deduplicate findings by the challenged decision object, evidence, failure mechanism, and repair—not
merely by similar wording.

For disagreements, report:

- shared evidence
- Reviewer A interpretation
- Reviewer B interpretation
- source of disagreement
- discriminator
- interim disposition

Preserve provenance with reviewer-specific finding IDs when the review is large.

### Reviewer-of-Reviewers Check

For each proposed finding, ask:

- Is the cited evidence actually present?
- Does it support the stated concern?
- Is the finding independent, or anchored to another review?
- Is the evidence status accurate?
- Is severity calibrated?
- Is the repair proportional to the problem?
- Did the reviewer mistake a hypothesis for a demonstrated defect?
- Would the proposed repair destroy something true, valuable, or intentionally constrained?
- Did the reviewer misunderstand the project phase, vocabulary, or protected intent?

The synthesis should improve the reviews, not simply concatenate them.

---

## Free Unstructured Pass (with Teeth)

Structured review causes attentional crowding-out. After the structured passes, read or inspect
the artifact again with fresh eyes and without trying to fill categories.

This is not a checkbox. If it finds nothing, name what was actually re-examined—for example:

- re-read conclusions against tables and methods
- checked every date, version, title, and proper name
- compared the playable sequence with the design summary
- scanned for one-off claims, hidden assumptions, dead paths, or duplicated scene functions
- reviewed the bibliography against prose
- inspected outputs that contradict the headline

Then state that nothing new surfaced. A clean free pass without a visible account of what it
looked at has not been run.

---

## Anti-Patterns to Avoid

Do not:

- perform harshness or invent objections for sport;
- pad the report with minor issues;
- let categories crowd out obvious uncategorized findings;
- treat all issues as equally serious;
- hide material concerns because they are uncertain;
- present domain-flavored speculation as domain knowledge;
- convert every imaginable rival into a defect;
- rewrite the project into another project;
- recommend scope expansion merely because the addition sounds attractive;
- collapse disagreement into a bland average;
- say "more data is needed" without naming what data and why;
- treat "not publicly verified" as "false";
- treat "safer to publish" as "more true";
- thin claims when the right action is flag, attribute, source, or human-confirm;
- treat artifact-reported tests as rerun tests;
- let possible private ground truth substitute for evidence;
- reward an artifact for sounding coherent;
- confuse a polished review with complete coverage.

---

# Part V — Output Contract

## Output Proportionality Rule

Use the smallest output that fully serves the decision.

- **Micro review:** Answer the specific question directly. Report only material concerns, the
  evidence needed to understand them, and the recommended action.
- **Narrow substantive review:** Give a brief disposition, material findings, preservation
  constraints, and relevant coverage limits.
- **Full review:** Use the Decision Summary, Atomic Findings Ledger, and Decision and Preservation
  Map.
- **Audit or multi-reviewer review:** Preserve the full ledger, verification states,
  reconciliation record, and coverage map.

Do not produce empty sections, ceremonial ledgers, or exhaustive field lists merely because the
Core contains them. Omitted structure is not omitted rigor when it would not change the decision,
repair, handoff, or reader's understanding of uncertainty.

Use two layers for substantial reviews.

## Layer 1 — Decision Summary

Include:

- review contract and coverage boundary
- overall disposition
- critical and major findings
- highest-leverage repairs
- verified or well-supported strengths that should be preserved
- material unresolved questions and residual risk

## Layer 2 — Atomic Findings Ledger

Rank by severity and actionability. Include only fields relevant to the finding.

```md
Finding ID:
Decision object ID:
Severity:
Confidence:
Evidence status:
Verification state:
Type:
Concern:
Evidence:
Interpretation / current implied explanation:
Alternative explanation or rival mechanism, if relevant:
Discriminator:
Likely error origin:
Priority:
Disposition:
Suggested repair:
Preservation constraint:
```

Recommended Type values include:

- correctness
- interpretation
- domain assumption
- evidence gap
- measurement mismatch
- reproducibility
- implementation drift
- communication
- safety
- source state
- editorial suitability
- design coherence
- scope
- user or player experience

Do not fill every field ceremonially. Alternative explanations and discriminators are required
when interpretation is genuinely underdetermined, not for simple typographical errors.

End with a **Decision and Preservation Map**:

1. **Release- or decision-blocking issues**
2. **Highest-leverage repairs**
3. **Objects to keep, narrow, attribute, verify, prototype, or human-confirm**
4. **What appears solid and should be preserved, with evidence trace**
5. **Open questions that actually matter**
6. **Coverage boundary and residual risk**
7. **Free-pass findings and reviewer self-check**

---

# Part VI — Building a Project Edition

## Purpose of a Project Edition

A Project Edition is not a summary of the Core. It is a **compiled operating protocol** for a
specific body of work.

Its job is to supply the context, vocabulary, taste, evidence standards, scope discipline, and
failure-mode knowledge that a general reviewer lacks. It should help a capable reviewer reason
like a careful collaborator on this project without pretending to replace the human owner or a
true domain expert.

A Project Edition may be longer than the runtime portions of the Core because concrete context is
its value. It should still avoid repeating generic instructions that the Core already states
clearly unless the repetition operationalizes them for the project.

---

## Project Edition Compilation Sequence

1. **Establish the project charter.** Define purpose, audience, intended outcome, and current
   identity.
2. **Define the phase model.** State the current phase, what is fluid, what is frozen, and what
   evidence is reasonable now.
3. **Protect intent and scope.** Name non-negotiable qualities, hard constraints, and what the
   project should not become.
4. **Build the vocabulary.** Define internal terms, abbreviations, version language, and common
   misunderstandings.
5. **Map artifacts and sources of truth.** Identify authoritative files, repositories, datasets,
   design documents, runtime behavior, human decisions, and source precedence.
6. **Define decision-object classes.** Specify the types of claims, results, designs, mechanics,
   assets, or release decisions reviewers must inspect.
7. **Define the evidence hierarchy.** State what evidence answers each recurring question.
8. **Identify characteristic failure modes.** Include failures already observed and plausible
   project-specific risks.
9. **Select and rewrite lens cards.** Tailor checks, evidence, discriminators, and outputs to the
   project.
10. **Define role and authority boundaries.** Clarify review, search, execution, edit, commit,
    publication, and deployment permissions.
11. **Define the project output and handoff.** Make findings usable by the next human, model, or
    implementation agent.
12. **Add calibration examples.** Show major issues, plausible concerns, unacceptable nitpicks,
    protected strengths, and scope-violating suggestions.
13. **Run the Tailoring Audit.** Check fidelity, bias, omissions, and Core inheritance.
14. **Version the edition.** Record the Core version, Project Edition version, local overrides,
    and project artifact compatibility.

---

## Project Phase

Every Project Edition should define its phase model and every Run Contract should name the current
phase.

Possible creative or software phases:

- exploration
- concept selection
- prototype
- vertical slice
- production
- integration
- polish
- release candidate
- post-release

Possible research phases:

- question formation
- data acquisition
- exploratory analysis
- method development
- confirmatory analysis
- interpretation
- manuscript drafting
- review response
- release or archival package

State:

```md
Current phase:
Current decision:
What is still fluid:
What is expensive to change:
What is frozen:
What evidence is expected at this phase:
What criticism would be premature:
What criticism would be dangerously late to omit:
```

Do not review an early placeholder as though it were a final defect. Do not respond to a polish
request by reopening the entire project unless a central failure requires it.

---

## Protected Project Intent

Every Project Edition should state:

```md
The project is trying to:
The intended audience / player / user is:
The intended experience or outcome is:
The project should remain:
The project should not become:
Non-negotiable qualities:
Hard constraints:
Hard scope ceiling:
Elements that may change:
Elements that require explicit owner approval to change:
```

Protected intent is not immunity from criticism. It defines the project against which criticism
must be useful. If the protected intent itself creates a critical failure, say so directly.

---

## Project Vocabulary and Ontology

Teach the reviewer what words mean inside the project.

```md
Term:
Project-specific meaning:
Common misunderstanding:
Authoritative reference or example:
```

Include object relationships when useful: route versus scene, dataset versus derived table,
manual label versus automatic detection, build artifact versus source artifact, report versus
source of record.

Do not assume common words retain their ordinary meaning inside a technical or creative project.

---

## Project Evidence Hierarchy

Define the strongest evidence for recurring questions. Example structure:

| Question | Strongest evidence | Useful secondary evidence | Insufficient by itself |
|---|---|---|---|
| What code ran? | Repository state, command, environment, logs | README and package report | Narrative assertion |
| What does the data show? | Raw data and reproducible analysis | Tables and figures | Summary prose alone |
| Does a scene work? | Implemented sequence in context | Script, storyboard, playtest notes | Synopsis or intention alone |
| Is an addition feasible? | Toolchain test and asset estimate | Implementation plan | Appeal of the idea |

Evidence precedence should be explicit when sources can conflict. For example, runtime behavior may
outweigh an outdated design document; a human owner decision may override an older generated plan;
raw data may outweigh a narrative summary.

---

## Characteristic Failure Modes

Do not settle for generic warnings. Name the failures this project is actually vulnerable to.

Examples for research:

- exploratory results reported as confirmatory
- measured evidence contradicts the narrative
- normalization destroys comparability
- sparse folds produce unstable model rankings
- a variable does not measure the claimed construct
- a plausible mechanism is narrated as demonstrated
- negative or contradictory results disappear during synthesis
- package-reported execution is mistaken for independent reproduction

Examples for short-form game or creative work:

- scope expansion dilutes polish
- attractive lore does not improve the playable experience
- scenes repeat the same emotional or informational function
- dialogue becomes exposition rather than character action
- art is beautiful but unusable for actual staging
- individual scenes improve while the overall arc weakens
- implementation advice ignores the real toolchain
- late feedback reopens already successful foundations
- the project becomes another genre or a much larger game

Project Editions should replace these examples with the project's real observed and anticipated
failure modes.

---

## Calibration Pack

Include several concrete boundary examples. At minimum:

- one confirmed Major or Critical issue
- one plausible concern that must remain labeled uncertain
- one unacceptable nitpick
- one unusual strength or claim that must be preserved
- one attractive suggestion that violates protected intent or scope
- one example of a strong review finding and repair

Calibration examples should teach the reviewer how rigor behaves here.

```md
Observation:
Bad review behavior:
Desired review behavior:
Why:
```

Examples are especially valuable when a project has non-obvious taste, unusual terminology,
known model failure modes, or a strong temptation toward scope expansion.

---

## Project Edition Inheritance Rules

A Project Edition may:

- add project context;
- operationalize a Core requirement;
- narrow a rule to the relevant domain;
- add stronger safeguards;
- define project-specific outputs;
- add examples, source precedence, and calibration cases;
- replace generic lens language with concrete project checks.

A Project Edition may not silently:

- remove Source Access Honesty;
- convert hypotheses into findings;
- weaken coverage disclosure;
- treat coherence as verification;
- discard material minority concerns without checking them;
- erase valuable claims solely because they are difficult to verify;
- authorize execution, edits, commits, publication, or deployment not granted by the user;
- ignore protected intent while claiming to improve the same project.

Any intentional override must be explicit, narrow, and explained.

Recommended header:

```md
Derived from: Hopeful Skeptic Core v0.4.1
Project Edition:
Project Edition version:
Project Edition status: Draft / Calibrating / Operational / Stale
Compatible project artifact version(s):
Local overrides:
Last calibration / evaluation date:
Freshness triggers:
```

Status meanings:

- **Draft:** Compiled but not yet tested on representative work.
- **Calibrating:** Used on real or known-answer cases; adjustments remain active.
- **Operational:** Tested sufficiently for routine use within the stated compatibility range.
- **Stale:** The project, evidence hierarchy, toolchain, protected intent, or Core has changed
  materially enough that the edition should not be trusted without revision.

Use lightweight compatibility rather than elaborate ceremony. Mark an edition Stale when a named
freshness trigger occurs; do not assume a recent file date means the project model is current.

---

## Project Edition Failure Modes

A tailored edition can misdirect a strong reviewer more effectively than a generic protocol. Check
especially for:

- **Recent-conflict overfitting:** A problem from the latest review or disagreement is treated as
  though it defines the whole project.
- **Stakeholder capture:** One collaborator's preferences are encoded as project truth without
  attribution or owner approval.
- **Premature freezing:** Exploratory or reversible choices are labeled protected, settled, or too
  expensive to revisit.
- **Historical fossilization:** The edition accurately describes an earlier phase but not the
  project's current state.
- **Taste laundering:** A subjective preference is presented as a universal quality criterion.
- **Toolchain fantasy:** The edition assumes capabilities, access, automation, or execution paths
  the real environment does not provide.
- **Success blindness:** Failure modes are richly documented while proven strengths remain too
  vague to protect during repair.
- **Context saturation:** Project history overwhelms the current decision, making important
  instructions difficult to locate.
- **Evaluation leakage:** Known-answer cases, prior findings, or other reviewers' conclusions are
  embedded in a way that contaminates independent discovery.
- **Compatibility drift:** Artifact versions, terminology, source precedence, or authority
  boundaries change without the edition being recalibrated.

These are failure hypotheses to audit, not automatic defects. Name the concrete evidence when one
is present.

---

## Tailoring Audit

Before using a Project Edition, check:

- Does it accurately describe the real project rather than an imagined ideal version?
- Does it preserve the owner's actual intent and constraints?
- Does it privilege one stakeholder's interpretation without saying so?
- Does it encode the project's real high-risk failure modes?
- Does it overfit to one recent dispute, model miss, or personal irritation?
- Has one stakeholder's taste or interpretation been laundered into universal project truth?
- Has it prematurely frozen choices that remain exploratory or reversible?
- Is it describing the current project rather than a historically accurate but stale phase?
- Does it assume tools, access, or execution capabilities the actual workflow lacks?
- Are proven strengths concrete enough to survive an aggressive repair pass?
- Does it omit uncomfortable but decision-relevant questions?
- Are vocabulary and source precedence accurate?
- Are expected evidence and authority boundaries clear?
- Do calibration examples distinguish rigor from nitpicking and ambition from scope drift?
- Has any Core invariant been weakened or silently removed?
- Could a fresh reviewer use it without inventing missing project context?

A tailored protocol is powerful because it directs attention. Audit that attention before trusting
it.

---

## Minimal Core Prompt

```md
Perform a hopeful-skeptic review. Skeptic = signal; cynic = noise. Coherence is not
reconciliation; defensibility is not truth; critique is not deletion.

Establish the decision, role, access, authority, and coverage. Map the decision-bearing claims,
results, assumptions, designs, or release criteria before reviewing details. For large or
high-stakes artifacts, preserve an object ledger and show what was and was not inspected.

Counter your default failure mode. If the artifact looks polished, run a visible conflict sweep
before trusting it; if it looks messy, identify what is actually correct or worth preserving.
Do not declare an area clean without showing the checks that could have falsified that verdict.

Distinguish artifact reporting, static inspection, source checking, execution, testing, clean
reproduction, and independent corroboration. Do not imply any verification that did not occur.
Distinguish confirmed findings, strongly supported findings, plausible concerns, hypotheses to
test, and concerns cleared after checking.

Ask not only whether a result is wrong, but whether the artifact tells the right story about what
it means. For underdetermined interpretations, give one grounded alternative if one exists and
name the observation, source, test, analysis, or playthrough that would discriminate. Do not
invent rivals for balance.

Separate truth, public verifiability, and editorial suitability. Do not treat "not verified" as
"false," possible private context as evidence, or safer wording as more true. Preserve valuable
claims through attribution, better sourcing, narrowing, caveat, or human confirmation when
appropriate.

Rate severity by what decision changes if the issue is real. Keep severity separate from
confidence, priority, and disposition. Attribute likely error origin without treating origin as
absolution.

Use only relevant lenses. After the structured review, run a free unstructured pass and state
what you re-examined. End with decision-blocking issues, highest-leverage repairs, objects to keep
or verify, preserved strengths with evidence trace, unresolved questions, coverage, and residual
risk.
```

---

# Appendix A — Core Lens Library

These cards are source material. Attach only relevant cards for a general review. For a Project
Edition, rewrite them around the project rather than stacking them unchanged.

## Source / Recordkeeping Audit

For biographies, encyclopedia pages, public records, source dossiers, bibliographies, archival
prep, and sourced public-facing claims.

```md
Catches: stale current-role claims; source conflicts; source-inherited errors; artifact-generated
synthesis errors; living-person concerns; interpretation stated as fact; weak source-to-claim
traceability; metadata drift; over-thinning from verifiability gaps.

Checks: separate truth / public verifiability / editorial suitability; distinguish current role,
historical role, residence, professional base, institutional affiliation, and cultural or
literary association; identify source type and date per contested claim; use claim-appropriate
sources of record; attribute interpretation to critics, interviews, or self-description; do not
auto-remove true-but-hard-to-verify claims.

Output: Claim status; strongest source; conflict or staleness; error origin; action (keep / hedge /
attribute / source better / human-confirm / move to claim ledger).
```

## Research Synthesis / Literature Audit

For literature reviews, research briefs, state-of-the-field summaries, conceptual frameworks, and
source-heavy scientific writing.

```md
Catches: citation laundering; consensus overstated from a narrow sample; review articles treated
as primary evidence; incompatible populations or constructs blended together; negative evidence
omitted; recency bias; causal or mechanistic claims stronger than the cited studies; one paper
carrying an entire conclusion.

Checks: map major claims to supporting studies; distinguish primary, secondary, and source-of-record
material; check population, intervention, outcome, timeframe, and construct compatibility; search
for credible contrary evidence; separate field consensus from author interpretation; identify
where a synthesis averages real disagreement.

Output: Synthesis claim; supporting evidence; contrary or limiting evidence; evidence breadth;
interpretive limit; safer or stronger formulation; unresolved research question.
```

## Measurement / Computational Package Audit

For data packages, plots, computational reports, audio metrics, scientific scripts, model outputs,
and reproducibility bundles.

```md
Catches: measured evidence contradicting the narrative; valid outputs overinterpreted; manual
labels presented as automatic detections; metric definitions that do not support the claim;
normalization or scale issues; leakage; unstable folds; missing reproducibility steps; graph design
that changes the epistemic reading; artifact-reported execution treated as rerun execution.

Checks: separate measured evidence from inference; verify that each metric measures the claimed
construct; inspect comparability across sections, runs, sites, or folds; trace headline conclusions
to actual tables and arrays; distinguish source code, reported logs, executed tests, and clean
reproduction; treat outputs as evidence both for and against the headline.

Output: Current claim; verification state; measurement support; alternative explanation;
discriminator; reproducibility state; repair or safer wording.
```

## Domain Mechanism Review

For scientific, engineering, field, geotechnical, biological, weather, instrumentation, and other
physical-system work.

```md
Catches: plausible rival mechanisms; station-, material-, organism-, or system-specific
assumptions; instrument or measurement-system explanations; causal overreach; missing metadata;
results explained with the wrong mechanism; plausible pattern completion presented as expertise.

Checks: name the current implied mechanism; identify a concrete grounded rival when possible;
state the observations, metadata, intervention, or experiment that would discriminate; distinguish
known domain behavior from analogy; identify boundary conditions; state limits in domain
confidence.

Output: Observed pattern; current mechanism; evidence status; rival mechanism or hypothesis;
discriminator; interim safe claim; domain-confidence note.
```

## Implementation / Agentic Package Audit

For repositories, build packages, generated code, installation workflows, automated patches,
release bundles, and agent-directed implementation.

```md
Catches: documentation-code drift; unexecuted plans presented as implementation; hidden environment
assumptions; missing dependencies; unsafe paths or destructive actions; tests that do not cover the
claimed behavior; generated outputs not tied to source inputs; edits outside authority; partial
success reported as completion; packaging that is hostile to the intended user.

Checks: inventory source and generated artifacts; record versions, paths, commands, inputs, and
outputs; distinguish static inspection, execution, testing, and clean reproduction; test the user-
critical path; verify failure behavior and rollback; check platform and permission assumptions;
respect edit, commit, publish, and deployment authority.

Output: Intended behavior; observed behavior; verification state; blocking defects; environment or
user constraints; exact repair; validation command or acceptance test; residual risk.
```

## Creative / Experience Review

For games, narrative projects, visual work, interactive experiences, scripts, prototypes, and
creative production packages.

```md
Catches: attractive additions without functional payoff; scope drift; repeated emotional or
informational beats; exposition replacing character action; local improvements that weaken the
whole arc; beautiful assets that fail in actual staging; intention mistaken for player experience;
toolchain-blind suggestions; feedback that rewrites the genre or protected identity.

Checks: identify the intended audience experience; evaluate scenes, mechanics, art, and pacing in
context; distinguish concept quality from implemented quality; test whether each addition performs
a distinct function; compare benefit against asset, implementation, and attention cost; preserve
strong identity and successful foundations; check whether the proposed change fits the current
phase and scope ceiling.

Output: Intended function; observed or likely experience; distinct contribution; duplication or
scope risk; implementation burden; evidence needed (prototype / playthrough / staging test);
recommendation and preservation constraint.
```

---

# Appendix B — Failure-Mode Adapters

Adapters describe **observed reviewer failure modes**, not model identities. Apply an adapter only
when the reviewer is known to exhibit the mode. Avoid top-line personality or stance labels that
invite self-stereotyping.

## Adapter: Premature Closure / Over-Smoothing

```md
Do not reward the artifact for sounding coherent. Coherence is not reconciliation.

Before writing "solid," "excellent," "no critical issues," or "nothing missed," show a completed
project-appropriate conflict sweep with evidence traces. State what you actually searched, read,
inspected, executed, or compared. A clean verdict without a visible sweep is an incomplete review.
If the sweep finds nothing, name what was examined and say the check found nothing.
```

## Adapter: Over-Thinning / Defensive Minimization

```md
Do not treat conflicting or thin public evidence as license to delete or minimize a claim that may
be true. Flag the conflict and identify what would resolve it. Resolve the intended sense of broad
phrasing before weakening it. Possible owner-held context is a reason for human confirmation, not
proof. Weaken a claim only when its intended sense is unsupported or unsuitable—not merely because
it is difficult to verify publicly.
```

## Adapter: Fluent Speculation / Hypothesis Inflation

```md
Do not convert every conceivable failure mode, rival mechanism, edge case, or design concern into a
finding. Require a concrete evidentiary foothold or realistic failure path. Label untested
alternatives as hypotheses. Prefer one grounded rival with a discriminator over five fluent
possibilities. Explicitly clear concerns that fail checking.
```

## Adapter: Scope Drift / Reinvention

```md
Review the project that exists and the decision currently being made. Do not recommend expansion,
new systems, extra content, architectural replacement, or genre change merely because it would be
interesting. Tie every substantial addition to protected intent, a distinct unmet function,
current phase, implementation burden, and scope ceiling. Preserve successful foundations unless a
material defect requires reopening them.
```

---

# Appendix C — Project Edition Starter Template

```md
# Hopeful Skeptic Project Edition — [PROJECT] v[VERSION]

Derived from: Hopeful Skeptic Core v0.4.1
Project Edition version:
Project Edition status: Draft / Calibrating / Operational / Stale
Compatible project artifact version(s):
Local overrides:
Last calibration / evaluation date:
Freshness triggers:

## Project Charter
Purpose:
Audience / player / user:
Intended outcome or experience:

## Protected Intent and Scope
The project should remain:
The project should not become:
Non-negotiable qualities:
Hard constraints:
Scope ceiling:
Owner-approval changes:

## Phase Model
Current phase:
Current decision:
Fluid:
Expensive to change:
Frozen:
Expected evidence now:
Premature criticism:
Dangerously late-to-omit criticism:

## Project Vocabulary
[Term / meaning / common misunderstanding / authoritative reference]

## Artifact and Source-of-Truth Map
[Artifact / role / authority / version / precedence]

## Decision-Object Classes
[Class / examples / why material / normal evidence]

## Project Evidence Hierarchy
[Question / strongest evidence / secondary evidence / insufficient alone]

## Characteristic Failure Modes
[Failure / consequence / detection path / likely repair]

## Tailored Review Workflow
[Rewrite the Core workflow for this project]

## Tailored Lens Cards
[Only the lenses that materially help]

## Review Roles and Authority
[Review / search / execute / edit / commit / publish / deploy]

## Calibration Pack
[Major issue / plausible concern / nitpick / protected strength / scope violation / strong finding]

## Output and Handoff Contract
[Decision summary / ledger / implementation handoff / next-model package]

## Run Contract Template
[Artifact version / immediate decision / mode / coverage / access / authority / deliverable]

## Tailoring Audit Result
[What was checked / unresolved assumptions / Core overrides]
```

---

# Appendix D — Evaluation and Context Hygiene

## Context Hygiene

Long personalized context can preserve superseded concerns, anchor reviewers to prior debates, or
cause a model to obey remembered project assumptions over the current protocol. For controlled
A/B testing or known-answer evaluation, prefer a clean context, temporary chat, project-scoped
memory, or API call.

For real project work, prior context may be valuable. Distinguish helpful continuity from stale
anchoring. The Run Contract should state major changes that supersede earlier assumptions.

## Known-Answer / Evaluation Mode

When testing this protocol or a Project Edition, score separately:

- **Discovery:** Did the reviewer find the target issue or source?
- **Classification:** Did it label finding versus concern versus hypothesis correctly?
- **Interpretation:** Did it understand what the evidence supports?
- **Severity and priority:** Did it calibrate impact and urgency?
- **Repair:** Did it recommend the right action without damaging protected truth or intent?
- **Preservation:** Did it retain what was correct or valuable?
- **Honesty:** Did it distinguish supplied reporting from actual verification?
- **Coverage:** Did it state what was and was not checked?
- **Failure behavior:** Did it over-thin, overpraise, overexpand, or fabricate?
- **Context sensitivity:** Did prior conversation or reviewer anchoring change the result?

Do not infer success from one good catch or failure from one miss. Track repeated behavior across
runs, models, contexts, artifact versions, and known-answer cases.

Evaluate the Core, the Project Edition, and the current reviewer separately. A weak Project Edition
can misdirect a strong model; a strong protocol cannot guarantee attention or domain competence.

---

# Changelog

## v0.4 → v0.4.1

- **Added an authoritative Output Proportionality Rule** with Micro, Narrow, Full, and Audit modes.
- **Added Project Edition status and freshness controls:** Draft, Calibrating, Operational, and
  Stale.
- **Added explicit Project Edition failure modes** including recent-conflict overfitting,
  stakeholder capture, premature freezing, historical fossilization, taste laundering, toolchain
  fantasy, success blindness, context saturation, evaluation leakage, and compatibility drift.
- **Strengthened the Tailoring Audit** to test those failure modes adversarially.
- **Clarified that added structure does not guarantee discovery** and that discovery-heavy work
  should favor independent attention, varied search paths, representative sampling, and fresh
  context over additional reporting categories.
- **Updated the Project Edition starter header** with status, calibration date, and freshness
  triggers.

## v0.3.1 → v0.4

- **Established two official forms:** the full Hopeful Skeptic Core and derived Project Editions.
- **Added Core / Project Edition / Run Contract architecture.**
- **Added Core Invariants and Project Edition inheritance rules.**
- **Added Stable Project Contract and per-task Run Contract.**
- **Added functional review roles and explicit execution/edit authority.**
- **Added a nine-step positive Review Workflow.**
- **Generalized major claims into Decision Objects** for research, software, creative, and design
  work.
- **Generalized the Anti-Closure conflict sweep** while preserving project-specific rewrites.
- **Added coverage maps and a bounded search stop rule.**
- **Separated Verification State from Evidence Status.**
- **Separated Severity, Confidence, Priority, and Disposition.**
- **Clarified that private ground truth is not evidence unless supplied.**
- **Clarified that error origin does not determine responsibility or required repair.**
- **Added measurement mismatch, implementation drift, and reviewer-generated error origins.**
- **Added claim-appropriate source guidance.**
- **Tightened rival-mechanism handling** so ungrounded alternatives remain hypotheses.
- **Added independent multi-reviewer workflow, atomic ledgers, reconciliation, and a reviewer-of-
  reviewers check.**
- **Renamed Balanced Friction Map to Decision and Preservation Map.**
- **Added the Project Edition Compiler, phase model, protected intent, vocabulary, evidence
  hierarchy, characteristic failure modes, calibration pack, and Tailoring Audit.**
- **Expanded the Core Lens Library** with Research Synthesis, Implementation / Agentic Package,
  and Creative / Experience cards while retaining Source, Measurement, and Mechanism cards.
- **Added Fluent Speculation and Scope Drift adapters.**
- **Moved evaluation and context-hygiene guidance into a dedicated appendix.**
- **Preserved the full Core as the preferred source document for building tailored editions.**

## Earlier v0.3 lineage retained

- Anti-Default Rule
- Anti-Closure Requirement
- Free Pass with visible re-examination
- Context Hygiene
- Failure-mode Model Adapters
- Depth Floor and Large-Ask Expansion
- Source Access Honesty
- Mandatory Interpretation Audit
- Truth / Public Verifiability / Editorial Suitability separation
- Error-origin attribution
- Known-Answer / Evaluation Mode
