"""Caso 3 - Reducao de custos da cafeteria."""
from ortools.linear_solver import pywraplp

# --- Conversoes de unidades ---
# Variaveis em LIBRAS; custos em $/lb
_LB_G = 453.592    # g por libra
_OZ10_G = 283.495  # g por 10 oncas

# Batata: por 100g -> por lb
POT_PROT = (1.5  / 100) * _LB_G   # g/lb
POT_IRON = (0.3  / 100) * _LB_G   # mg/lb
POT_VITC = (12.0 / 100) * _LB_G   # mg/lb

# Vagem: por 10 oz -> por lb
GB_PROT = (5.67  / _OZ10_G) * _LB_G   # g/lb
GB_IRON = (3.402 / _OZ10_G) * _LB_G   # mg/lb
GB_VITC = (28.35 / _OZ10_G) * _LB_G   # mg/lb

# Feijao-lima: por 10 oz -> por lb (Q5+)
LB_PROT = (22.68 / _OZ10_G) * _LB_G   # g/lb
LB_IRON = (6.804 / _OZ10_G) * _LB_G   # mg/lb
LB_VITC = 0.0                           # sem vitamina C

# Peso minimo do prato: 10 kg em libras
MIN_PESO_LB = 10_000 / _LB_G

# Requisitos base
REQ_PROT = 180    # g
REQ_IRON = 80     # mg
REQ_VITC = 1_050  # mg


def _resolver_pv(req_iron=REQ_IRON, req_vitc=REQ_VITC,
                 req_prot=REQ_PROT, razao_n=5, razao_d=6,
                 custo_vagem=1.0):
    """Resolve o modelo com batata (P) e vagem (G).

    A restricao de sabor e P:G >= razao_d/razao_n, ou seja,
    razao_n * P - razao_d * G >= 0.

    Args:
        req_iron: exigencia minima de ferro (mg).
        req_vitc: exigencia minima de vitamina C (mg).
        req_prot: exigencia minima de proteina (g).
        razao_n: numerador da razao minima P:G.
        razao_d: denominador da razao minima P:G.
        custo_vagem: custo da vagem em $/lb.

    Returns:
        dict com P, G, custo ou None se infactivel.
    """
    solver = pywraplp.Solver.CreateSolver("GLOP")
    P = solver.NumVar(0, solver.infinity(), "P")
    G = solver.NumVar(0, solver.infinity(), "G")

    solver.Add(POT_PROT * P + GB_PROT * G >= req_prot)
    solver.Add(POT_IRON * P + GB_IRON * G >= req_iron)
    solver.Add(POT_VITC * P + GB_VITC * G >= req_vitc)
    solver.Add(P + G >= MIN_PESO_LB)
    # sabor: razao_n * P >= razao_d * G
    solver.Add(razao_n * P - razao_d * G >= 0)

    solver.Minimize(0.40 * P + custo_vagem * G)
    st = solver.Solve()

    if st != pywraplp.Solver.OPTIMAL:
        return None
    return {
        "P": P.solution_value(),
        "G": G.solution_value(),
        "custo": solver.Objective().Value(),
        "tipo_g": "vagem",
    }


def _resolver_pl(req_iron=65, req_vitc=REQ_VITC,
                 req_prot=REQ_PROT, razao_n=5, razao_d=6):
    """Resolve o modelo com batata (P) e feijao-lima (L).

    Args:
        req_iron: exigencia minima de ferro (mg).
        req_vitc: exigencia minima de vitamina C (mg).
        req_prot: exigencia minima de proteina (g).
        razao_n: numerador da razao minima P:L.
        razao_d: denominador da razao minima P:L.

    Returns:
        dict com P, G, custo ou None se infactivel.
    """
    solver = pywraplp.Solver.CreateSolver("GLOP")
    P = solver.NumVar(0, solver.infinity(), "P")
    L = solver.NumVar(0, solver.infinity(), "L")

    solver.Add(POT_PROT * P + LB_PROT * L >= req_prot)
    solver.Add(POT_IRON * P + LB_IRON * L >= req_iron)
    solver.Add(POT_VITC * P + LB_VITC * L >= req_vitc)
    solver.Add(P + L >= MIN_PESO_LB)
    solver.Add(razao_n * P - razao_d * L >= 0)

    solver.Minimize(0.40 * P + 0.60 * L)
    st = solver.Solve()

    if st != pywraplp.Solver.OPTIMAL:
        return None
    return {
        "P": P.solution_value(),
        "G": L.solution_value(),
        "custo": solver.Objective().Value(),
        "tipo_g": "feijao-lima",
    }


def _exibir(num, titulo, res, obs=None):
    """Exibe resultado de uma pergunta.

    Args:
        num: numero da pergunta.
        titulo: descricao do cenario.
        res: dict de resultado ou None.
        obs: conclusao adicional.

    Returns:
        None
    """
    print("\n[P{}] {}".format(num, titulo))
    if res is None:
        print("  Sem solucao otima.")
        return
    label = res["tipo_g"]
    P_kg = res["P"] * _LB_G / 1000
    G_kg = res["G"] * _LB_G / 1000
    print(
        "  Batata      : {:.4f} lb ({:.3f} kg)".format(
            res["P"], P_kg
        )
    )
    print(
        "  {:10s}: {:.4f} lb ({:.3f} kg)".format(
            label.capitalize(), res["G"], G_kg
        )
    )
    print(
        "  Custo total : ${:.4f}".format(res["custo"])
    )
    if obs:
        print("  => {}".format(obs))


def executar():
    """Executa o Caso 3: Reducao de custos da cafeteria.

    Returns:
        None
    """
    print("=" * 60)
    print("CASO 3 - REDUCAO DE CUSTOS DA CAFETERIA")
    print("=" * 60)
    print("\nCoeficientes nutricionais (por lb):")
    print(
        "  Batata   : prot={:.3f}g  ferro={:.3f}mg"
        "  vitC={:.3f}mg".format(
            POT_PROT, POT_IRON, POT_VITC
        )
    )
    print(
        "  Vagem    : prot={:.3f}g  ferro={:.3f}mg"
        "  vitC={:.3f}mg".format(
            GB_PROT, GB_IRON, GB_VITC
        )
    )
    print(
        "  F. Lima  : prot={:.3f}g  ferro={:.3f}mg"
        "  vitC={:.3f}mg".format(
            LB_PROT, LB_IRON, LB_VITC
        )
    )
    print(
        "  Peso min : {:.4f} lb (= 10 kg)".format(
            MIN_PESO_LB
        )
    )

    # --- P1: base ---
    r1 = _resolver_pv()
    _exibir(1, "Plano base (batata + vagem)", r1)

    # --- P2: razao minima 1:2 (P:G >= 1:2 => 2P - G >= 0) ---
    r2 = _resolver_pv(razao_n=2, razao_d=1)
    delta2 = r2["custo"] - r1["custo"] if r2 else None
    _exibir(
        2,
        "Razao minima 1:2 (batata:vagem)",
        r2,
        "Variacao de custo: {:+.4f}".format(delta2)
        if delta2 is not None else None,
    )

    # --- P3: ferro reduzido para 65 mg ---
    r3 = _resolver_pv(req_iron=65)
    delta3 = r3["custo"] - r1["custo"] if r3 else None
    _exibir(
        3,
        "Ferro reduzido para 65 mg",
        r3,
        "Variacao de custo: {:+.4f}".format(delta3)
        if delta3 is not None else None,
    )

    # --- P4: ferro=65mg e vagem=$0.50/lb ---
    r4 = _resolver_pv(req_iron=65, custo_vagem=0.50)
    delta4 = r4["custo"] - r1["custo"] if r4 else None
    _exibir(
        4,
        "Ferro 65mg + vagem a $0.50/lb",
        r4,
        "Variacao de custo: {:+.4f}".format(delta4)
        if delta4 is not None else None,
    )

    # --- P5: substituir vagem por feijao-lima (ferro=65) ---
    r5 = _resolver_pl(req_iron=65)
    _exibir(
        5,
        "Batata + feijao-lima (ferro=65mg)",
        r5,
    )

    # --- P6: analise de sabor da solucao do item 5 ---
    print("\n[P6] Requisito de sabor com feijao-lima")
    if r5:
        P5, L5 = r5["P"], r5["G"]
        ratio = P5 / L5 if L5 > 1e-9 else float('inf')
        atende = ratio >= (6 / 5)
        print(
            "  Ratio P:L = {:.4f} | min = 1.2000"
            " => {}".format(
                ratio,
                "ATENDE" if atende else "NAO ATENDE",
            )
        )
        print(
            "  Observacao: o feijao-lima tem sabor"
            " e textura distintos da vagem."
        )
        print(
            "  A razao 6:5 foi definida para batata:vagem;"
            " para feijao-lima,"
        )
        print(
            "  a aplicabilidade pratica do mesmo criterio"
            " de sabor deve ser reavaliada."
        )

    # --- P7: batata+feijao-lima, ferro>=120, vitC>=500 ---
    r7 = _resolver_pl(req_iron=120, req_vitc=500)
    _exibir(
        7,
        "Novos req: ferro>=120mg e vitC>=500mg"
        " (batata+feijao-lima)",
        r7,
    )