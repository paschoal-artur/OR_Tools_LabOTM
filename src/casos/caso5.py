"""Caso 5 - Producao de moda feminina."""
from ortools.linear_solver import pywraplp

# --- Dados base ---
CUSTO_FIXO_TOTAL = 860_000 + (3 * 2_700_000)

ITEMS = [
    "wool_slacks", "cashmere_sweater", "silk_blouse", "silk_camisole",
    "tailored_skirt", "wool_blazer", "velvet_pants", "cotton_sweater",
    "cotton_miniskirt", "velvet_shirt", "button_down_blouse"
]

PRECO = {
    "wool_slacks": 300, "cashmere_sweater": 450, "silk_blouse": 180,
    "silk_camisole": 120, "tailored_skirt": 270, "wool_blazer": 320,
    "velvet_pants": 350, "cotton_sweater": 130, "cotton_miniskirt": 75,
    "velvet_shirt": 200, "button_down_blouse": 120
}

CUSTO_MO = {
    "wool_slacks": 160, "cashmere_sweater": 150, "silk_blouse": 100,
    "silk_camisole": 60, "tailored_skirt": 120, "wool_blazer": 140,
    "velvet_pants": 175, "cotton_sweater": 60, "cotton_miniskirt": 40,
    "velvet_shirt": 160, "button_down_blouse": 90
}

CONSUMO = {
    "wool_slacks": {"wool": 3.0, "acetate": 2.0},
    "cashmere_sweater": {"cashmere": 1.5},
    "silk_blouse": {"silk": 1.5},
    "silk_camisole": {"silk": 0.5},
    "tailored_skirt": {"rayon": 2.0, "acetate": 1.5},
    "wool_blazer": {"wool": 2.5, "acetate": 1.5},
    "velvet_pants": {"velvet": 3.0, "acetate": 2.0},
    "cotton_sweater": {"cotton": 1.5},
    "cotton_miniskirt": {"cotton": 0.5},
    "velvet_shirt": {"velvet": 1.5},
    "button_down_blouse": {"rayon": 1.5}
}

CAP_TECIDO_BASE = {
    "wool": 45000, "acetate": 28000, "cashmere": 9000,
    "silk": 18000, "rayon": 30000, "velvet": 20000, "cotton": 30000
}

CUSTO_TECIDO = {
    "wool": 9.00, "acetate": 1.50, "cashmere": 60.00,
    "silk": 13.00, "rayon": 2.25, "velvet": 12.00, "cotton": 2.50
}

DEMANDA_MAX = {
    "velvet_pants": 5500, "velvet_shirt": 6000,
    "cashmere_sweater": 4000, "silk_blouse": 12000,
    "silk_camisole": 15000, "wool_slacks": 7000,
    "wool_blazer": 5000
}

DEMANDA_MIN = {
    "wool_slacks": 4200,   # 60% de 7000
    "wool_blazer": 3000,   # 60% de 5000
    "tailored_skirt": 2800
}


def _resolver(cap_tecido=None, mod_mo=None, veludo_reembolsavel=True, permite_excesso_nov=False):
    """Monta e resolve o modelo do Caso 5.
    
    Args:
        cap_tecido: dict com capacidades de tecido.
        mod_mo: dict com modificadores de custo de mao de obra.
        veludo_reembolsavel: bool, define se o veludo nao usado pode ser devolvido.
        permite_excesso_nov: bool, permite produzir acima da demanda maxima a 60% do preco.
        
    Returns:
        dict com quantidades, lucro e consumo, ou None.
    """
    if cap_tecido is None:
        cap_tecido = CAP_TECIDO_BASE.copy()
    if mod_mo is None:
        mod_mo = {}

    solver = pywraplp.Solver.CreateSolver("GLOP")

    x = {}
    x_excesso = {}

    for p in ITEMS:
        limite_normal = DEMANDA_MAX.get(p, solver.infinity())
        x[p] = solver.NumVar(0, limite_normal, f"x_{p}")
        
        if permite_excesso_nov and p in DEMANDA_MAX:
            x_excesso[p] = solver.NumVar(0, solver.infinity(), f"x_excesso_{p}")
        else:
            x_excesso[p] = solver.NumVar(0, 0, f"x_excesso_{p}")

    # Total de cada peça produzida
    prod = {p: x[p] + x_excesso[p] for p in ITEMS}

    # Demandas minimas obrigatórias
    for p, v_min in DEMANDA_MIN.items():
        solver.Add(prod[p] >= v_min)

    # Regra de sobra de material (sucata não reembolsável)
    # A sucata da blusa faz a camisole. A do suéter faz a minissaia.
    solver.Add(prod["silk_camisole"] >= prod["silk_blouse"])
    solver.Add(prod["cotton_miniskirt"] >= prod["cotton_sweater"])

    # Uso e capacidade de tecido
    uso_tecido = {t: sum(CONSUMO[p].get(t, 0) * prod[p] for p in ITEMS) for t in cap_tecido}
    for t, cap in cap_tecido.items():
        solver.Add(uso_tecido[t] <= cap)

    # Calculo Financeiro
    receita = sum(PRECO[p] * x[p] + (0.6 * PRECO[p]) * x_excesso[p] for p in ITEMS)
    custo_mo = sum((CUSTO_MO[p] + mod_mo.get(p, 0)) * prod[p] for p in ITEMS)

    custo_mat = 0
    for t, cap in cap_tecido.items():
        if t == "velvet" and not veludo_reembolsavel:
            custo_mat += cap * CUSTO_TECIDO[t]  # Custo afundado de toda a capacidade
        else:
            custo_mat += uso_tecido[t] * CUSTO_TECIDO[t]  # Paga só pelo que consome

    lucro_bruto = receita - custo_mo - custo_mat

    solver.Maximize(lucro_bruto)
    st = solver.Solve()

    if st != pywraplp.Solver.OPTIMAL:
        return None

    res = {p: prod[p].solution_value() for p in ITEMS}
    res["lucro_bruto"] = solver.Objective().Value()
    res["lucro_liquido"] = res["lucro_bruto"] - CUSTO_FIXO_TOTAL
    return res


def _exibir(num, titulo, res, obs=None):
    """Exibe o resultado de uma pergunta formatado."""
    print("\n[P{}] {}".format(num, titulo))
    if res is None:
        print("  Sem solucao otima.")
        return

    print("  Lucro Bruto (Margem) : ${:,.2f}".format(res["lucro_bruto"]))
    print("  Lucro Liquido Final  : ${:,.2f}".format(res["lucro_liquido"]))
    
    print("  Producao:")
    for p in ITEMS:
        val = res[p]
        if val > 0.001:
            print("    - {:<20}: {:,.0f} un".format(p, val))
            
    if obs:
        print("  => {}".format(obs))


def executar():
    """Executa o Caso 5: Producao de moda feminina."""
    print("=" * 60)
    print("CASO 5 - PRODUCAO DE MODA FEMININA")
    print("=" * 60)

    # --- P1: Avaliação Teórica ---
    print("\n[P1] Argumentacao sobre as camisas de veludo")
    print("  A argumentacao de nao produzir a camisa esta INCORRETA.")
    print("  Em Pesquisa Operacional, o custo fixo do desenvolvimento e desfiles")
    print("  ($8.96M) e um custo afundado (sunk cost) e irrelevante para o mix.")
    print("  Como a margem de contribuicao unitaria da camisa e positiva ($22),")
    print("  cada unidade ajuda a diluir esse custo fixo e aumenta o lucro.")

    # --- P2: Modelo Base ---
    r2 = _resolver()
    _exibir(2, "Plano base para maximizar lucro", r2)

    # --- P3: Veludo nao reembolsavel ---
    r3 = _resolver(veludo_reembolsavel=False)
    _exibir(3, "Veludo nao reembolsavel", r3)

    # --- P4: Explicacao Economica ---
    print("\n[P4] Explicacao economica da diferenca (P2 vs P3)")
    print("  Quando o veludo da reembolso (P2), economizar veludo gera caixa")
    print("  ($12/jarda). Quando NAO da reembolso (P3), o valor ja foi gasto.")
    print("  O custo marginal do veludo cai para zero, tornando as pecas de veludo")
    print("  artificialmente 'mais baratas' de produzir. O solver entao aumenta a")
    print("  producao dessas pecas para extrair qualquer margem sobre a mao de obra.")

    # --- P5: Aumento do custo MO do Blazer ---
    r5 = _resolver(mod_mo={"wool_blazer": 80})
    _exibir(5, "Custo do blazer de la aumentado em $80", r5,
            "A margem do blazer despenca. O solver produz apenas o minimo "
            "obrigatorio (3.000) e aloca o acetato/la para as calcas.")

    # --- P6: Mais 10.000 jardas de Acetato ---
    cap6 = CAP_TECIDO_BASE.copy()
    cap6["acetate"] += 10000
    r6 = _resolver(cap_tecido=cap6)
    _exibir(6, "Mais 10.000 jardas de acetato", r6,
            "O acetato era o grande gargalo da colecao. A producao de pecas que "
            "usam esse forro (como calcas de la e saias) dispara consideravelmente.")

    # --- P7: Sobras vendidas a 60% ---
    r7 = _resolver(permite_excesso_nov=True)
    _exibir(7, "Venda de sobras em novembro por 60% do preco", r7,
            "O solver produz alem da demanda maxima para pecas cuja margem de "
            "contribuicao ainda e positiva mesmo a 60% do preco original "
            "(como a camisole de seda, que custa ~$66 para fazer e vende por $72).")