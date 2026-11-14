"""
logic.py — Propositional logic, relations, functions, and proof by induction.

Public functions
----------------
parse_and_evaluate(formula_str, assignment)  — safe hand-written parser
truth_table(formula_str)                     — full truth table as list of dicts
classify_formula(formula_str)                — tautology/contradiction/contingency
check_equivalence(f1, f2)                    — logical equivalence + counterexample
relation_properties(relation, domain)        — reflexive, symmetric, …
function_properties(mapping, domain, codomain)
induction_verify(formula_name, n_max)        — step-by-step numeric verification
factor_tree(n)                               — prime factorisation for strong induction

No Streamlit imports. No eval().
"""

from __future__ import annotations
import math
from fractions import Fraction
from typing import Any


# ===========================================================================
# 1. Safe propositional formula parser
# ===========================================================================
#
# Grammar (lowest to highest precedence):
#   expr   ::= iff
#   iff    ::= implies ('iff'|'↔' implies)*
#   implies::= xor    (('implies'|'→'|'=>') xor)*     (right-assoc handled by recursion)
#   xor    ::= or     ('xor'|'⊕' or)*
#   or     ::= and    ('or'|'∨' and)*
#   and    ::= not    ('and'|'∧' not)*
#   not    ::= ('not'|'¬') not  |  atom
#   atom   ::= 'p'|'q'|'r'|'T'|'F'  |  '(' expr ')'
#
# Tokens: lower-cased, stripped.

_KEYWORDS = {"not", "and", "or", "implies", "iff", "xor"}
_SYMS = {"¬", "∧", "∨", "→", "↔", "⊕", "=>"}


class ParseError(ValueError):
    """Raised on an invalid formula string."""


def _tokenise(s: str) -> list[str]:
    """Split *s* into a token list."""
    # Normalise unicode operators to ASCII keywords so the parser stays simple.
    s = (s.replace("¬", " not ")
          .replace("∧", " and ")
          .replace("∨", " or ")
          .replace("→", " implies ")
          .replace("↔", " iff ")
          .replace("⊕", " xor ")
          .replace("=>", " implies ")
          .replace("<->", " iff ")
          .replace("->", " implies "))
    tokens: list[str] = []
    i = 0
    while i < len(s):
        c = s[i]
        if c.isspace():
            i += 1
        elif c in "()":
            tokens.append(c)
            i += 1
        else:
            j = i
            while j < len(s) and not s[j].isspace() and s[j] not in "()":
                j += 1
            word = s[i:j].lower()
            tokens.append(word)
            i = j
    return tokens


class _Parser:
    """Recursive-descent parser that builds a nested tuple AST."""

    def __init__(self, tokens: list[str]):
        self._tok = tokens
        self._pos = 0

    def _peek(self) -> str | None:
        return self._tok[self._pos] if self._pos < len(self._tok) else None

    def _consume(self, expected: str | None = None) -> str:
        tok = self._peek()
        if tok is None:
            raise ParseError("Unexpected end of formula.")
        if expected is not None and tok != expected:
            raise ParseError(f"Expected '{expected}', got '{tok}'.")
        self._pos += 1
        return tok

    def parse(self):
        tree = self._expr()
        if self._peek() is not None:
            raise ParseError(f"Unexpected token '{self._peek()}' at end.")
        return tree

    def _expr(self):
        return self._iff()

    def _iff(self):
        left = self._implies()
        while self._peek() == "iff":
            self._consume()
            right = self._implies()
            left = ("iff", left, right)
        return left

    def _implies(self):
        left = self._xor()
        if self._peek() == "implies":
            self._consume()
            right = self._implies()   # right-associative
            return ("implies", left, right)
        return left

    def _xor(self):
        left = self._or()
        while self._peek() == "xor":
            self._consume()
            right = self._or()
            left = ("xor", left, right)
        return left

    def _or(self):
        left = self._and()
        while self._peek() == "or":
            self._consume()
            right = self._and()
            left = ("or", left, right)
        return left

    def _and(self):
        left = self._not()
        while self._peek() == "and":
            self._consume()
            right = self._not()
            left = ("and", left, right)
        return left

    def _not(self):
        if self._peek() == "not":
            self._consume()
            return ("not", self._not())
        return self._atom()

    def _atom(self):
        tok = self._peek()
        if tok is None:
            raise ParseError("Expected an atom but got end of formula.")
        if tok == "(":
            self._consume("(")
            tree = self._expr()
            self._consume(")")
            return tree
        if tok in ("t", "true", "1"):
            self._consume()
            return ("const", True)
        if tok in ("f", "false", "0"):
            self._consume()
            return ("const", False)
        if len(tok) == 1 and tok.islower() and tok.isalpha():
            self._consume()
            return ("var", tok)
        raise ParseError(f"Unknown token '{tok}'.")


def _extract_vars(tree) -> list[str]:
    """Return sorted list of distinct variable names in *tree*."""
    if tree[0] == "var":
        return [tree[1]]
    if tree[0] == "const":
        return []
    if tree[0] == "not":
        return _extract_vars(tree[1])
    return sorted(set(_extract_vars(tree[1])) | set(_extract_vars(tree[2])))


def _eval_tree(tree, assignment: dict[str, bool]) -> bool:
    """Recursively evaluate *tree* under *assignment*."""
    op = tree[0]
    if op == "var":
        return assignment[tree[1]]
    if op == "const":
        return tree[1]
    if op == "not":
        return not _eval_tree(tree[1], assignment)
    a = _eval_tree(tree[1], assignment)
    b = _eval_tree(tree[2], assignment)
    if op == "and":
        return a and b
    if op == "or":
        return a or b
    if op == "implies":
        return (not a) or b
    if op == "iff":
        return a == b
    if op == "xor":
        return a != b
    raise ParseError(f"Unknown operator '{op}'.")


def parse_formula(formula_str: str):
    """
    Parse *formula_str* into an AST tuple.

    Raises ParseError on invalid input.
    """
    tokens = _tokenise(formula_str)
    if not tokens:
        raise ParseError("Empty formula.")
    parser = _Parser(tokens)
    return parser.parse()


def evaluate_formula(formula_str: str, assignment: dict[str, bool]) -> bool:
    """
    Evaluate *formula_str* under the given variable assignment.

    Parameters
    ----------
    formula_str : str
    assignment  : dict mapping variable names to bool values.

    Returns
    -------
    bool
    """
    tree = parse_formula(formula_str)
    return _eval_tree(tree, assignment)


def truth_table(formula_str: str) -> dict:
    """
    Build the full truth table for *formula_str*.

    Returns
    -------
    dict with keys:
        'variables' : list[str]
        'rows'      : list of dicts — each row has variable values + 'result'
        'errors'    : list[str]  — non-empty on parse failure
    """
    try:
        tree = parse_formula(formula_str)
    except ParseError as e:
        return {"variables": [], "rows": [], "errors": [str(e)]}

    variables = _extract_vars(tree)
    if len(variables) > 4:
        return {
            "variables": variables, "rows": [],
            "errors": ["At most 4 variables are supported (p, q, r, s)."],
        }

    rows = []
    n = len(variables)
    for i in range(2 ** n):
        assignment = {
            variables[j]: bool((i >> (n - 1 - j)) & 1)
            for j in range(n)
        }
        result = _eval_tree(tree, assignment)
        row = {v: assignment[v] for v in variables}
        row["result"] = result
        rows.append(row)

    return {"variables": variables, "rows": rows, "errors": []}


def classify_formula(formula_str: str) -> dict:
    """
    Classify *formula_str* as tautology, contradiction, or contingency.

    Returns
    -------
    dict with keys:
        'classification' : 'tautology' | 'contradiction' | 'contingency'
        'all_true'       : bool
        'all_false'      : bool
        'errors'         : list[str]
    """
    tt = truth_table(formula_str)
    if tt["errors"]:
        return {
            "classification": "error",
            "all_true": False, "all_false": False,
            "errors": tt["errors"],
        }
    results = [r["result"] for r in tt["rows"]]
    all_true  = all(results)
    all_false = not any(results)
    if all_true:
        cls = "tautology"
    elif all_false:
        cls = "contradiction"
    else:
        cls = "contingency"
    return {
        "classification": cls,
        "all_true": all_true, "all_false": all_false,
        "errors": [],
    }


def check_equivalence(f1: str, f2: str) -> dict:
    """
    Check whether *f1* and *f2* are logically equivalent.

    Returns
    -------
    dict with keys:
        'equivalent'    : bool
        'counterexample': dict | None  — an assignment where they differ (if any)
        'errors'        : list[str]
    """
    try:
        t1 = parse_formula(f1)
        t2 = parse_formula(f2)
    except ParseError as e:
        return {"equivalent": False, "counterexample": None, "errors": [str(e)]}

    vars1 = _extract_vars(t1)
    vars2 = _extract_vars(t2)
    variables = sorted(set(vars1) | set(vars2))
    if len(variables) > 4:
        return {
            "equivalent": False, "counterexample": None,
            "errors": ["At most 4 variables are supported."],
        }

    n = len(variables)
    for i in range(2 ** n):
        assignment = {
            variables[j]: bool((i >> (n - 1 - j)) & 1)
            for j in range(n)
        }
        r1 = _eval_tree(t1, assignment)
        r2 = _eval_tree(t2, assignment)
        if r1 != r2:
            return {
                "equivalent": False,
                "counterexample": {**assignment, "f1": r1, "f2": r2},
                "errors": [],
            }
    return {"equivalent": True, "counterexample": None, "errors": []}


# ===========================================================================
# 2. Relations on a finite set
# ===========================================================================

def relation_properties(relation: list[tuple], domain: list) -> dict:
    """
    Analyse properties of a relation *R* on *domain*.

    Parameters
    ----------
    relation : list of (a, b) pairs — the relation R.
    domain   : list of elements forming the base set.

    Returns
    -------
    dict with keys:
        'reflexive'      : bool
        'symmetric'      : bool
        'antisymmetric'  : bool
        'transitive'     : bool
        'equivalence'    : bool   (reflexive + symmetric + transitive)
        'partial_order'  : bool   (reflexive + antisymmetric + transitive)
        'counterexamples': dict mapping property name → (a, b) | None
        'errors'         : list[str]
    """
    if not domain:
        return {
            "reflexive": True, "symmetric": True,
            "antisymmetric": True, "transitive": True,
            "equivalence": True, "partial_order": True,
            "counterexamples": {}, "errors": [],
        }

    if len(domain) > 10:
        return {
            "reflexive": False, "symmetric": False,
            "antisymmetric": False, "transitive": False,
            "equivalence": False, "partial_order": False,
            "counterexamples": {},
            "errors": ["Domain must have at most 10 elements."],
        }

    R = set(map(tuple, relation))
    D = list(domain)

    # Reflexive: (a,a) ∈ R for all a ∈ D
    refl_ce = None
    for a in D:
        if (a, a) not in R:
            refl_ce = (a, a)
            break
    reflexive = refl_ce is None

    # Symmetric: (a,b)∈R → (b,a)∈R
    sym_ce = None
    for (a, b) in R:
        if (b, a) not in R:
            sym_ce = (a, b)
            break
    symmetric = sym_ce is None

    # Antisymmetric: (a,b)∈R ∧ (b,a)∈R → a=b
    anti_ce = None
    for (a, b) in R:
        if a != b and (b, a) in R:
            anti_ce = (a, b)
            break
    antisymmetric = anti_ce is None

    # Transitive: (a,b)∈R ∧ (b,c)∈R → (a,c)∈R
    trans_ce = None
    for (a, b) in R:
        for (b2, c) in R:
            if b == b2 and (a, c) not in R:
                trans_ce = (a, b, c)
                break
        if trans_ce:
            break
    transitive = trans_ce is None

    return {
        "reflexive":     reflexive,
        "symmetric":     symmetric,
        "antisymmetric": antisymmetric,
        "transitive":    transitive,
        "equivalence":   reflexive and symmetric and transitive,
        "partial_order": reflexive and antisymmetric and transitive,
        "counterexamples": {
            "reflexive":     refl_ce,
            "symmetric":     sym_ce,
            "antisymmetric": anti_ce,
            "transitive":    trans_ce,
        },
        "errors": [],
    }


# ===========================================================================
# 3. Functions (injective / surjective / bijective)
# ===========================================================================

def function_properties(
    mapping: list[tuple],
    domain: list,
    codomain: list,
) -> dict:
    """
    Analyse a function given as a list of (domain_element, image) pairs.

    Returns
    -------
    dict with keys:
        'valid'      : bool   — every domain element appears exactly once
        'injective'  : bool
        'surjective' : bool
        'bijective'  : bool
        'errors'     : list[str]
        'details'    : str
    """
    errors: list[str] = []
    dom_set = set(map(str, domain))
    cod_set = set(map(str, codomain))

    if not mapping:
        errors.append("Mapping is empty.")
        return {
            "valid": False, "injective": False,
            "surjective": False, "bijective": False,
            "errors": errors, "details": "Empty mapping.",
        }

    # Check it is a valid function
    seen_domain: dict = {}
    images: list = []
    for pair in mapping:
        if len(pair) != 2:
            errors.append(f"Each pair must have exactly 2 elements, got {pair}.")
            continue
        a, b = str(pair[0]), str(pair[1])
        if a not in dom_set:
            errors.append(f"'{a}' is not in the domain.")
        if b not in cod_set:
            errors.append(f"'{b}' is not in the codomain.")
        if a in seen_domain:
            errors.append(f"'{a}' appears more than once in the mapping (not a function).")
        else:
            seen_domain[a] = b
            images.append(b)

    unmapped = dom_set - set(seen_domain.keys())
    if unmapped:
        errors.append(f"Domain elements not mapped: {sorted(unmapped)}.")

    if errors:
        return {
            "valid": False, "injective": False,
            "surjective": False, "bijective": False,
            "errors": errors, "details": "Invalid function.",
        }

    # Injective: all images distinct
    injective = len(images) == len(set(images))
    # Surjective: every codomain element is an image
    surjective = cod_set == set(images)
    bijective = injective and surjective

    details_parts = []
    if not injective:
        from collections import Counter
        cnt = Counter(images)
        dups = [img for img, c in cnt.items() if c > 1]
        details_parts.append(f"Not injective: images {dups} appear more than once.")
    if not surjective:
        missed = sorted(cod_set - set(images))
        details_parts.append(f"Not surjective: codomain elements {missed} have no preimage.")

    return {
        "valid":      True,
        "injective":  injective,
        "surjective": surjective,
        "bijective":  bijective,
        "errors":     [],
        "details":    " ".join(details_parts) or "Valid function.",
    }


# ===========================================================================
# 4. Induction verification
# ===========================================================================

# Supported formula names and their descriptions.
INDUCTION_FORMULAS = {
    "sum_n":       "Sum of first n integers: 1+2+…+n = n(n+1)/2",
    "sum_odd":     "Sum of first n odd numbers: 1+3+…+(2n-1) = n²",
    "sum_squares": "Sum of first n squares: 1²+2²+…+n² = n(n+1)(2n+1)/6",
    "pow2_gt_n":   "2ⁿ > n for all n ≥ 1",
    "div3":        "n³ − n is divisible by 3 for all n ≥ 1",
}


def _closed_form(name: str, n: int) -> Fraction:
    if name == "sum_n":
        return Fraction(n * (n + 1), 2)
    if name == "sum_odd":
        return Fraction(n * n)
    if name == "sum_squares":
        return Fraction(n * (n + 1) * (2 * n + 1), 6)
    if name == "pow2_gt_n":
        return Fraction(2 ** n)           # LHS; RHS = n
    if name == "div3":
        return Fraction(n ** 3 - n)
    raise ValueError(f"Unknown formula '{name}'.")


def _iterated(name: str, n: int) -> Fraction:
    """Compute the LHS by direct summation / iteration."""
    if name == "sum_n":
        return Fraction(sum(range(1, n + 1)))
    if name == "sum_odd":
        return Fraction(sum(2 * k - 1 for k in range(1, n + 1)))
    if name == "sum_squares":
        return Fraction(sum(k * k for k in range(1, n + 1)))
    if name == "pow2_gt_n":
        return Fraction(2 ** n)
    if name == "div3":
        return Fraction(n ** 3 - n)
    raise ValueError(f"Unknown formula '{name}'.")


def induction_verify(formula_name: str, n_max: int) -> dict:
    """
    Show base case, inductive step description, and numeric verification for
    n = 1 … n_max.

    Parameters
    ----------
    formula_name : one of the keys of INDUCTION_FORMULAS
    n_max        : int in [1, 200]

    Returns
    -------
    dict with keys:
        'name'         : str
        'description'  : str
        'base_case'    : dict  — {'n': 1, 'lhs': ..., 'rhs': ..., 'holds': bool}
        'inductive_step': str  — plain-English description
        'verification' : list of {'n': int, 'lhs': Fraction, 'rhs': Fraction|int, 'holds': bool}
        'errors'       : list[str]
    """
    if formula_name not in INDUCTION_FORMULAS:
        return {
            "name": formula_name, "description": "", "base_case": {},
            "inductive_step": "", "verification": [],
            "errors": [f"Unknown formula '{formula_name}'. "
                       f"Choose from: {list(INDUCTION_FORMULAS)}."],
        }
    if not isinstance(n_max, int) or n_max < 1 or n_max > 200:
        return {
            "name": formula_name, "description": "",
            "base_case": {}, "inductive_step": "", "verification": [],
            "errors": ["n_max must be an integer between 1 and 200."],
        }

    desc = INDUCTION_FORMULAS[formula_name]

    # Base case
    lhs1 = _iterated(formula_name, 1)
    if formula_name == "pow2_gt_n":
        rhs1 = Fraction(1)
        holds1 = lhs1 > rhs1
    elif formula_name == "div3":
        rhs1 = Fraction(0)
        holds1 = (lhs1 % 3 == 0)
    else:
        rhs1 = _closed_form(formula_name, 1)
        holds1 = (lhs1 == rhs1)

    base_case = {"n": 1, "lhs": lhs1, "rhs": rhs1, "holds": holds1}

    # Inductive step descriptions
    step_desc = {
        "sum_n":       ("Assume 1+…+k = k(k+1)/2. "
                        "Then 1+…+k+(k+1) = k(k+1)/2 + (k+1) = (k+1)(k+2)/2. ✓"),
        "sum_odd":     ("Assume sum of first k odd numbers = k². "
                        "The (k+1)-th odd number is 2k+1. "
                        "k² + (2k+1) = (k+1)². ✓"),
        "sum_squares": ("Assume sum = k(k+1)(2k+1)/6. "
                        "Add (k+1)²: algebraic simplification gives (k+1)(k+2)(2k+3)/6. ✓"),
        "pow2_gt_n":   ("Assume 2ᵏ > k. "
                        "Then 2^(k+1) = 2·2ᵏ > 2k ≥ k+1 for k ≥ 1. ✓"),
        "div3":        ("Assume 3 | (k³−k). "
                        "(k+1)³−(k+1) = k³+3k²+3k+1−k−1 = (k³−k)+3k²+3k = (k³−k)+3k(k+1). "
                        "Both (k³−k) and 3k(k+1) are divisible by 3. ✓"),
    }

    verification = []
    for n in range(1, n_max + 1):
        lhs = _iterated(formula_name, n)
        if formula_name == "pow2_gt_n":
            rhs = Fraction(n)
            holds = lhs > rhs
        elif formula_name == "div3":
            rhs = Fraction(0)
            holds = (lhs % 3 == 0)
        else:
            rhs = _closed_form(formula_name, n)
            holds = (lhs == rhs)
        verification.append({"n": n, "lhs": lhs, "rhs": rhs, "holds": holds})

    return {
        "name":           formula_name,
        "description":    desc,
        "base_case":      base_case,
        "inductive_step": step_desc[formula_name],
        "verification":   verification,
        "errors":         [],
    }


# ===========================================================================
# 5. Factor tree (strong induction demo)
# ===========================================================================

def factor_tree(n: int) -> dict:
    """
    Prime factorise *n* (2 ≤ n ≤ 10000) for the strong-induction demo.

    Returns
    -------
    dict with keys:
        'n'            : int
        'factors'      : list[int]  — prime factors (with repeats)
        'factorisation': str        — e.g. '60 = 2 × 2 × 3 × 5'
        'steps'        : list[str]  — division steps
        'errors'       : list[str]
    """
    if not isinstance(n, int) or n < 2 or n > 10000:
        return {
            "n": n, "factors": [], "factorisation": "",
            "steps": [],
            "errors": ["n must be an integer between 2 and 10000."],
        }

    factors: list[int] = []
    steps: list[str] = []
    remaining = n
    d = 2
    while d * d <= remaining:
        while remaining % d == 0:
            factors.append(d)
            steps.append(f"{remaining} ÷ {d} = {remaining // d}")
            remaining //= d
        d += 1
    if remaining > 1:
        factors.append(remaining)
        steps.append(f"{remaining} is prime")

    factorisation = f"{n} = " + " × ".join(str(f) for f in factors)
    return {
        "n":            n,
        "factors":      factors,
        "factorisation": factorisation,
        "steps":        steps,
        "errors":       [],
    }
