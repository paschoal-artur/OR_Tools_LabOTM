"""Caso 2 - Planejamento de producao automotiva."""
from ortools.linear_solver import pywraplp

# --- Dados base ---
LUCRO_T = 3_600        # lucro unitario Thrillseeker ($)
LUCRO_C = 5_400        # lucro unitario Cruiser ($)
HORAS_T_BASE = 6.0     # horas/unidade Thrillseeker
HORAS_C = 10.5         # horas/unidade Cruiser
PORTAS_T = 4           # portas/unidade Thrillseeker
PORTAS_C = 2           # portas/unidade Cruiser
CAP_HORAS_BASE = 48_000  # horas disponiveis no mes
CAP_PORTAS = 20_000    # portas disponiveis no mes
DEM_C_MAX_BASE = 3_500  # demanda maxima do Cruiser


def _resolver(
    lucro_t=LUCRO_T,
    lucro_c=LUCRO_C,
    horas_t=HORAS_T_BASE,
    cap_horas=CAP_HORAS_BASE,
    dem_c_max=DEM_C_MAX_BASE,
    dem_c_min=0.0,
):
    """Monta e resolve o modelo de producao automotiva.

    Args:
        lucro_t: lucro unitario do Thrillseeker.
        lucro_c: lucro unitario do Cruiser.
        horas_t: horas de montagem por Thrillseeker.
        cap_horas: capacidade total de horas no mes.
        dem_c_max: demanda maxima do Cruiser.
        dem_c_min: demanda minima do Cruiser.

    Returns:
        dict com chaves t, c, lucro; ou None se infactivel.
    """
    solver = pywraplp.Solver.CreateSolver("GLOP")
    t = solver.NumVar(0, solver.infinity(), "T")
    c = solver.NumVar(0, solver.infinity(), "C")

    solver.Add(horas_t * t + HORAS_C * c <= cap_horas)
    solver.Add(PORTAS_T * t + PORTAS_C * c <= CAP_PORTAS)
    solver.Add(c <= dem_c_max)
    if dem_c_min > 0:
        solver.Add(c >= dem_c_min)

    solver.Maximize(lucro_t * t + lucro_c * c)
    st = solver.Solve()

    if st != pywraplp.Solver.OPTIMAL:
        return None
    return {
        "t": t.solution_value(),
        "c": c.solution_value(),
        "lucro": solver.Objective().Value(),
    }


def _exibir(num, titulo, res, obs=None):
    """Exibe o resultado de uma pergunta formatado.

    Args:
        num: numero da pergunta.
        titulo: descricao curta do cenario.
        res: dict retornado por _resolver.
        obs: conclusao de negocio (opcional).

    Returns:
        None
    """
    print("\n[P{}] {}".format(num, titulo))
    if res is None:
        print("  Sem solucao otima.")
        return
    print(
        "  Thrillseeker : {:.0f} un.".format(res["t"])
    )
    print(
        "  Cruiser      : {:.0f} un.".format(res["c"])
    )
    print(
        "  Lucro total  : ${:,.0f}".format(res["lucro"])
    )
    if obs:
        print("  => {}".format(obs))


def executar():
    """Executa o Caso 2: Planejamento de producao automotiva.

    Returns:
        None
    """
    print("=" * 60)
    print("CASO 2 - PLANEJAMENTO DE PRODUCAO AUTOMOTIVA")
    print("=" * 60)
    print("\nDados do problema:")
    print(
        "  Thrillseeker : lucro=${:,}/un | "
        "{:.0f}h/un | {} portas/un".format(
            LUCRO_T, HORAS_T_BASE, PORTAS_T
        )
    )
    print(
        "  Cruiser      : lucro=${:,}/un | "
        "{:.1f}h/un | {} portas/un".format(
            LUCRO_C, HORAS_C, PORTAS_C
        )
    )
    print(
        "  Capacidade   : {:,} horas/mes".format(
            CAP_HORAS_BASE
        )
    )
    print(
        "  Portas       : {:,} unidades/mes".format(
            CAP_PORTAS
        )
    )
    print(
        "  Demanda max. Cruiser: {:,} un".format(
            DEM_C_MAX_BASE
        )
    )

    r1 = _resolver()
    _exibir(1, "Plano base para maximizar lucro", r1)

    dem_camp = int(DEM_C_MAX_BASE * 1.20)
    r2 = _resolver(dem_c_max=dem_camp)
    delta2 = r2["lucro"] - r1["lucro"]
    _exibir(
        2,
        "Campanha de marketing (+20%% demanda Cruiser)",
        r2,
        "Ganho bruto: ${:,.0f} | Custo campanha: $500.000 "
        "| Resultado: ${:,.0f} => {}".format(
            delta2,
            delta2 - 500_000,
            "NAO FAZER" if delta2 < 500_000 else "FAZER",
        ),
    )

    cap_ot = int(CAP_HORAS_BASE * 1.25)
    r3 = _resolver(cap_horas=cap_ot)
    _exibir(3, "Horas extras (+25%% capacidade)", r3)

    val_max_ot = r3["lucro"] - r1["lucro"]
    print("\n[P4] Valor maximo a pagar pelas horas extras")
    print(
        "  Ganho adicional com horas extras: "
        "${:,.0f}".format(val_max_ot)
    )
    print(
        "  => Pagar ate ${:,.0f} pelo pacote "
        "ainda e vantajoso.".format(val_max_ot)
    )

    r5 = _resolver(cap_horas=cap_ot, dem_c_max=dem_camp)
    _exibir(5, "Campanha + horas extras (simultaneo)", r5)

    custo_cen = 500_000 + 1_600_000
    liq5 = r5["lucro"] - custo_cen
    delta6 = liq5 - r1["lucro"]
    print("\n[P6] Viabilidade economica: P5 vs P1")
    print(
        "  Lucro bruto P5  : ${:,.0f}".format(r5["lucro"])
    )
    print(
        "  Custos (camp+OT): -${:,.0f}".format(custo_cen)
    )
    print("  Lucro liquido   : ${:,.0f}".format(liq5))
    print(
        "  Lucro base (P1) : ${:,.0f}".format(r1["lucro"])
    )
    print(
        "  Ganho liquido   : {:+,.0f} => {}".format(
            delta6,
            "VANTAJOSO" if delta6 > 0 else "NAO VANTAJOSO",
        )
    )

    r7 = _resolver(lucro_t=2_800)
    _exibir(
        7, "Lucro Thrillseeker reduzido para $2.800", r7
    )

    r8 = _resolver(horas_t=7.5)
    _exibir(8, "Tempo montagem Thrillseeker: 7,5h/un", r8)

    r9 = _resolver(
        dem_c_max=DEM_C_MAX_BASE,
        dem_c_min=float(DEM_C_MAX_BASE),
    )
    queda9 = r1["lucro"] - r9["lucro"]
    _exibir(
        9,
        "Forcando atendimento total da demanda Cruiser",
        r9,
        "Queda de lucro: ${:,.0f} | "
        "Limite aceitavel: $2.000.000 => {}".format(
            queda9,
            "ACEITAVEL" if queda9 <= 2_000_000
            else "NAO ACEITAVEL",
        ),
    )

    r10 = _resolver(
        lucro_t=2_800,
        horas_t=7.5,
        cap_horas=cap_ot,
        dem_c_max=dem_camp,
    )
    liq10 = r10["lucro"] - custo_cen
    delta10 = liq10 - r1["lucro"]
    _exibir(
        10,
        "Decisao final: campanha+OT com P7 e P8 ativos",
        r10,
        "Lucro bruto: ${:,.0f} | Custos: -${:,.0f} "
        "| Liquido: ${:,.0f} | vs base: {:+,.0f} "
        "=> {}".format(
            r10["lucro"],
            custo_cen,
            liq10,
            delta10,
            "VANTAJOSO" if delta10 > 0
            else "NAO VANTAJOSO",
        ),
    )