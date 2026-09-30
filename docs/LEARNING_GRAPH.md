# Learning Graph & Mastery Engine — Gayatri AI Platform

## 1. Concept DAG Architecture

The Gayatri Learning Graph models educational domains as Directed Acyclic Graphs (DAGs) of concepts linked by prerequisite dependencies.

```text
                  [ Atomic Structure ]
                           │
                           ▼
                  [ Chemical Bonding ]
                           │
             ┌─────────────┴─────────────┐
             ▼                           ▼
  [ Molecular Geometry ]      [ Thermodynamics Basics ]
             │                           │
             ▼                           ▼
 [ Hybridization Models ]     [ Enthalpy & Hess's Law ]
                                         │
                                         ▼
                             [ Gibbs Free Energy ]
```

### Key Graph Components (`central_platform/learning/graph.py`)
- **Concept Nodes**: Unique concept identifiers with domain, title, difficulty level, and target learning outcomes.
- **Prerequisite Links**: Directed edges indicating prerequisite concept requirements.
- **Recursive DAG Traversal**: Evaluates prerequisite chain completion before advancing student to downstream concepts.
- **Cycle & Missing Prerequisite Detection**: Graph validation suite ensuring DAG structural integrity.

---

## 2. Multi-Factor Evidence-Backed Mastery Engine

Mastery is computed deterministically by the `MasteryEvidenceEngine` (`central_platform/learning/mastery.py`):

$$\text{Mastery} = 0.40 \cdot \text{Acc}_{\text{recent}} + 0.25 \cdot \text{Acc}_{\text{long\_term}} - \text{Pen}_{\text{hints}} - \text{Pen}_{\text{attempts}} - \text{Decay}(t)$$

### Mastery Inputs & Rules
1. **Recent Accuracy ($\text{Acc}_{\text{recent}}$)**: Weighted performance over the 5 most recent attempts.
2. **Long-Term Accuracy ($\text{Acc}_{\text{long\_term}}$)**: Cumulative historical success rate.
3. **Hint Penalty ($\text{Pen}_{\text{hints}}$)**: Subtracts 0.05 per requested hint (up to 0.15 max).
4. **Attempt Diminishing Returns ($\text{Pen}_{\text{attempts}}$)**: Penalizes repeated failures on the same question.
5. **Ebbinghaus Time Decay ($\text{Decay}(t)$)**: Models memory degradation over inactive days:
   $$\text{Decay}(t) = \text{Mastery}_0 \cdot e^{-\lambda \cdot \Delta t}$$
6. **Prerequisite Propagation**: Prerequisite concept mastery below 0.60 caps downstream node mastery.

---

## 3. Spaced Review Progression

Spaced repetition uses an expanding interval schedule:
- **Interval 1**: 1 day post-initial mastery ($M \ge 0.75$)
- **Interval 2**: 3 days
- **Interval 3**: 7 days
- **Interval 4**: 14 days
- **Interval 5**: 30 days

Successful reviews advance the interval stage; failed reviews reset the concept to Interval 1 for immediate remediation.

---

## 4. Next Action Engine & Decision Rules

The `NextActionEngine` (`central_platform/learning/actions.py`) evaluates student state against 9 canonical actions:

| Action Type | Trigger Condition | Pedagogical Goal |
|---|---|---|
| `REMEDIATE` | Active severe misconception code detected | Clear fundamental misconception |
| `HINT` | Failure on first attempt of current item | Provide scaffolding clue |
| `EXPLAIN` | Student explicitly asks "why" or "explain" | Deliver conceptual walkthrough |
| `REVIEW` | Concept due in spaced repetition queue | Reinforce retention |
| `PRACTICE` | Mastery between 0.40 and 0.75 | Build procedural fluency |
| `ASSESS` | Mastery $\ge 0.75$ and assessment due | Formative verification |
| `CHALLENGE` | Mastery $\ge 0.90$ with 3 consecutive correct | Deepen concept application |
| `ADVANCE` | Assessment passed & prerequisites satisfied | Move to next DAG concept |
| `CONTINUE` | Default active learning sequence | Proceed with current topic |
