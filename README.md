# Sustainable Solar Energy Allocation Using Set Theory and Graph Optimization

An interactive Python + Streamlit application that applies **discrete mathematics**
to a university-campus solar-panel allocation study. It covers set theory, logic and
proofs, counting, pigeonhole and inclusion–exclusion, recurrences, modular arithmetic,
and graph theory (representations, Euler/Hamiltonian, bipartite, colouring, matching,
planarity bounds).

Everything is computed live from the underlying data and algorithms — nothing is
hardcoded. The `algorithms/` package contains pure Python (no Streamlit imports);
`components/` holds the Streamlit UI; `app.py` is a thin router.

## Pages

| Group | Page | What it does |
|---|---|---|
| OVERVIEW | Dashboard | Campus KPIs, eligibility summary, syllabus coverage cards |
| OVERVIEW | Data Management | Edit buildings and candidate connections (validated) |
| SET THEORY | Set Theory | Membership, subsets, unions/intersections, identities |
| LOGIC & PROOFS | Logic & Proofs | Truth tables, tautology checks, equivalence, relations, functions, induction |
| COUNTING | Counting | Permutations, combinations, Pascal's triangle, campus selections |
| COUNTING | Pigeonhole & IE | Pigeonhole, Ramsey/Mantel, inclusion–exclusion, derangements, Euler φ |
| NUMBER THEORY | Recurrences | Fibonacci, Catalan, derangements, Hanoi, partitions, linear recurrences |
| NUMBER THEORY | Modular Arithmetic | Euclid, Bezout, inverses, CRT, Fermat, fast modular exponentiation |
| GRAPH THEORY | Graph Theory | Representations, Euler/Hamiltonian, trees, bipartite, colouring, matching, planarity |
| LEARN | Math Lab | Set identities, degree-sum check, inclusion–exclusion walkthrough |

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

## Run

```bash
python -m streamlit run app.py
```

## Test

```bash
python -m pytest -q
```

## Notes

All pages display the caption **"Illustrative sample data, not real measurements"**.
User-supplied text is escaped before rendering. Every Matplotlib figure is closed
immediately after rendering to avoid leaks.

## Viva Questions and Answers

**Q1. What is the difference between a tautology, a contradiction, and a contingency?**
A tautology is true under every assignment of truth values; a contradiction is false
under every assignment; a contingency is true under at least one and false under at
least one. In the app, `classify_formula` evaluates the truth table and counts the
true rows: all rows true → tautology, no rows true → contradiction, otherwise contingency.

**Q2. Why must `p → q` be equivalent to `¬q → ¬p`?**
They are contrapositives of one another. Directly: `p → q ≡ ¬p ∨ q`, and
`¬q → ¬p ≡ q ∨ ¬p`, which is the same by commutativity. The app's `check_equivalence`
verifies this by comparing the two truth tables column-by-column over all assignments.

**Q3. What makes a relation an equivalence relation?**
It must be reflexive, symmetric, and transitive. The app tests each property on a
user-supplied set and shows a failing pair as a counterexample when a property breaks.
An equivalence relation partitions the set into disjoint classes.

**Q4. Distinguish a partial order from an equivalence relation.**
A partial order is reflexive, antisymmetric, and transitive (e.g. "divides" on the
integers); an equivalence relation replaces antisymmetry with symmetry. Antisymmetry
means `a R b` and `b R a` together force `a = b`.

**Q5. When is a function bijective?**
Exactly when it is both injective (distinct inputs map to distinct outputs) and
surjective (every element of the codomain is hit). The app checks both conditions and
reports each counterexample found; bijective requires both to hold.

**Q6. How does weak induction prove a statement `P(n)` for all `n ≥ 1`?**
Show the base case `P(1)` and the inductive step "if `P(k)` then `P(k+1)`". The app
demonstrates this for five formulas and additionally verifies the claim numerically for
`n = 1..N`. Strong induction (used for the prime factorisation example) may assume all
cases below `k`, not just `k`.

**Q7. State the pigeonhole principle.**
If `n` items are placed into `m` boxes and `n > m`, at least one box holds at least
`⌈n/m⌉` items. The app applies it to the campus data by sorting the buildings into
solar-% bands and reporting the band that must hold at least `⌈n/m⌉` buildings.

**Q8. What does the inclusion–exclusion principle say for three sets?**
`|A∪B∪C| = |A|+|B|+|C| − |A∩B| − |A∩C| − |B∩C| + |A∩B∩C|`. The app computes each term
and verifies the result against the actual union of the campus sets.

**Q9. What is a derangement, and how is `D(n)` computed?**
A derangement is a permutation with no fixed point. The app uses the recurrence
`D(n) = (n−1)(D(n−1) + D(n−2))` with `D(0)=1, D(1)=0`, and cross-checks the value
against brute-force enumeration for `n ≤ 8`. Known values: `D(4)=9`, `D(5)=44`.

**Q10. Count the number of onto functions from a 4-element set to a 3-element set.**
By inclusion–exclusion: `3^4 − C(3,1)·2^4 + C(3,2)·1^4 = 81 − 48 + 3 = 36`.
The app computes the formula and verifies it by brute force for small `m, n`.

**Q11. Give the closed form of the Fibonacci sequence and its generating function.**
`F(n) = (φⁿ − ψⁿ)/√5` with `φ = (1+√5)/2`, `ψ = (1−√5)/2`; the ordinary generating
function of `F(n)` is `x/(1 − x − x²)`, equivalently the coefficients of
`1/(1 − x − x²)` are `1, 1, 2, 3, 5, …`. The app expands the series and matches it
against the iterated terms. `F(20) = 6765`.

**Q12. How do you solve a second-order linear recurrence with constant coefficients?**
For `aₙ = p·aₙ₋₁ + q·aₙ₋₂`, solve the characteristic equation `r² − p·r − q = 0`.
Distinct real roots give `aₙ = A·r₁ⁿ + B·r₂ⁿ`; a repeated root gives `(A + Bn)·rⁿ`;
complex roots give a real form using `ρⁿ cos(nθ)`. The app states the form and verifies
it against the iterated terms.

**Q13. What does the Chinese Remainder Theorem guarantee?**
For pairwise-coprime moduli `m₁, m₂, m₃`, the system `x ≡ aᵢ (mod mᵢ)` has a unique
solution modulo `m₁m₂m₃`. The app raises an error when the moduli are not coprime. It
solves `x ≡ 2 (3), x ≡ 3 (5), x ≡ 2 (7)` and reports `x = 23`.

**Q14. When does `a` have a modular inverse modulo `m`, and how is it found?**
Exactly when `gcd(a, m) = 1`. The extended Euclidean algorithm gives Bezout
coefficients `x, y` with `ax + my = 1`, so `a⁻¹ ≡ x (mod m)`. Example: `3⁻¹ mod 7 = 5`
since `3·5 = 15 ≡ 1 (mod 7)`. There is no inverse for `6 mod 9` because `gcd(6,9)=3`.

**Q15. How do you decide whether a graph has an Euler circuit?**
A connected graph has an Euler circuit iff every vertex has even degree (an Euler path
exists iff exactly zero or two vertices have odd degree). The app tests degree parity
and connectivity, then constructs the circuit by Hierholzer's algorithm when it exists.
The default 3-vertex triangle has an even degree at every vertex, so an Euler circuit
exists; it also has a Hamiltonian cycle and chromatic number 3, but is not bipartite
because it contains a triangle (odd cycle).
