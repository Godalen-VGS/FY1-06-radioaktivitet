"""Automatisk retting av FY1-06-radioaktivitet.

Hver sjekk i SJEKKER er én deltest, og poengene fordeles likt på dem.
De samme sjekkene ligger i "Test løsningen din"-cellen nederst i notebooken.
"""
import pytest

from notebook_loader import last_notebook

def naer(a, b, rel=1e-3):
    """Sant hvis tallet a er innenfor rel (relativt) av b."""
    try:
        a, b = float(a), float(b)
    except (TypeError, ValueError):
        return False
    if b == 0:
        return abs(a) < 1e-9
    return abs(a - b) <= rel * abs(b)


def S(tekst):
    """Gjør tekst om til et sympy-uttrykk, f.eks. S("x**2 - 1")."""
    import sympy
    return sympy.sympify(tekst, locals={n: sympy.Symbol(n) for n in ("N", "O", "Q", "S")})


def lik(a, b):
    """Sant hvis a og b er matematisk like.

    Lister og mengder sammenlignes uten hensyn til rekkefølge, tupler (koordinater) i rekkefølge.
    """
    import sympy
    if a is None:
        return False
    if isinstance(b, tuple):
        if not isinstance(a, (tuple, list, sympy.Tuple)) or len(a) != len(b):
            return False
        return all(lik(x, y) for x, y in zip(a, b))
    if isinstance(b, (list, set)):
        if isinstance(a, sympy.FiniteSet):
            a = list(a)
        if not isinstance(a, (list, tuple, set)) or len(a) != len(b):
            return False
        rest = list(a)
        for y in b:
            for i, x in enumerate(rest):
                if lik(x, y):
                    del rest[i]
                    break
            else:
                return False
        return True
    if isinstance(b, dict):
        if not isinstance(a, dict) or len(a) != len(b):
            return False
        a = {str(k): v for k, v in a.items()}
        return all(str(k) in a and lik(a[str(k)], v) for k, v in b.items())
    try:
        a, b = sympy.sympify(a), sympy.sympify(b)
    except (sympy.SympifyError, TypeError):
        return False
    vanlige = lambda u: u.subs({s: sympy.Symbol(s.name) for s in u.free_symbols})
    a, b = vanlige(a), vanlige(b)
    if isinstance(a, sympy.Set) or isinstance(b, sympy.Set):
        return a == b
    if getattr(b, "is_Relational", False):
        return a == b
    try:
        return sympy.simplify(a - b) == 0
    except TypeError:
        return a == b

oppgave = last_notebook("oppgave")

SJEKKER = [
    ('1_lengde', 'simuler_henfall(1000, 0.1, 10) skal gi 11 tall og starte med 1000', 'len(simuler_henfall(1000, 0.1, 10)) == 11 and simuler_henfall(1000, 0.1, 10)[0] == 1000'),
    ('1_avtar', 'antallet skal aldri øke', '(lambda L: all(a >= b for a, b in zip(L, L[1:])) and L[-1] < 500)(simuler_henfall(500, 0.2, 15))'),
    ('1_statistikk', 'med 100 000 kjerner og p = 0.1 skal det være ca. 34 900 igjen etter 10 steg', 'naer(simuler_henfall(100000, 0.1, 10)[-1], 100000 * 0.9**10, rel=0.03)'),
    ('2', 'halveringstid_fra_p(0.5) skal gi 1, og halveringstid_fra_p(1/6) ca. 3.80', 'naer(halveringstid_fra_p(0.5), 1) and naer(halveringstid_fra_p(1/6), 3.8018, rel=1e-4)'),
    ('3_eksakt', 'halveringstid_fra_data skal gi 2 for data med T½ = 2 og bakgrunn 20', 'naer(halveringstid_fra_data([0, 1, 2, 3, 4], [20 + 1000 * 0.5**(t/2) for t in [0, 1, 2, 3, 4]], 20), 2)'),
    ('3_barium', 'halveringstiden fra barium.csv skal være ca. 2.55 min', "naer(halveringstid_fra_data(*__import__('numpy').loadtxt('barium.csv', delimiter=',', skiprows=1, unpack=True), 18), 2.55, rel=0.05)"),
    ('4', 'aktivitet(1000, 2) skal gi ln(2)/2 · 1000 ≈ 346.6', 'naer(aktivitet(1000, 2), 1000 * 0.6931471805599453 / 2)'),
]


@pytest.mark.parametrize(
    "beskrivelse,uttrykk", [s[1:] for s in SJEKKER], ids=[s[0] for s in SJEKKER]
)
def test_sjekk(beskrivelse, uttrykk):
    navnerom = {**vars(oppgave), "naer": naer, "lik": lik, "S": S}
    assert eval(uttrykk, navnerom), beskrivelse
