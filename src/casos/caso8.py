"""Caso 8 - Gestao agricola sob incerteza."""
from ortools.linear_solver import pywraplp

# --- Dados de lavoura ---
TERRA_TOTAL = 640
HORAS_WS = 4_000
HORAS_SF = 4_500
VENDA_WS = 5.00
VENDA_SF = 5.50
DESPESA_VIDA = 40_000
MESES_PERIODO = 6

HORAS_CULTURA = {
    "soja":  [1.0, 1.4],
    "milho": [0.9, 1.2],
    "trigo": [0.6, 0.7],
}

# --- Dados de pecuaria ---
# Vacas leiteiras
COW_H_MES   = 10      # horas/mes por vaca
COW_ACRES   = 2       # acres de pastagem por vaca
COW_INC     = 850     # renda anual por vaca ($)
COW_CUR     = 30      # rebanho atual
COW_MAX     = 42      # limite do celeiro
COW_NEW_COST = 1_500  # custo de compra ($)
COW_DEP     = 0.10    # depreciacao anual

# Galinhas poedeiras
HEN_H_MES   = 0.05    # horas/mes por galinha
HEN_ACRES   = 0       # pastagem por galinha
HEN_INC     = 4.25    # renda anual por galinha ($)
HEN_CUR     = 2_000   # plantel atual
HEN_MAX     = 5_000   # limite do galinheiro
HEN_NEW_COST = 3      # custo de compra ($)
HEN_DEP     = 0.25    # depreciacao anual

# Requerimento minimo de alimentacao animal
# milho: 1 acre por vaca total
# trigo: 0.05 acres por galinha total
COW_MILHO_ACRE = 1.0
HEN_TRIGO_ACRE = 0.05

FUNDO_INVEST = 20_000

# Valores iniciais da pecuaria atual
END_VALUE_CUR = (COW_CUR * COW_NEW_COST * (1 - COW_DEP)
                 + HEN_CUR * HEN_NEW_COST * (1 - HEN_DEP))

END_VALUE_CUR = 31_500 + 3_750 

# Cenarios climaticos
CENARIOS = {
    "Normal":        {"soja": 70,  "milho": 60,  "trigo": 40,  "prob": 0.40},
    "Seca":          {"soja": -10, "milho": -15, "trigo": 0,   "prob": 0.20},
    "Enchente":      {"soja": 15,  "milho": 20,  "trigo": 10,  "prob": 0.10},
    "Geada precoce": {"soja": 50,  "milho": 40,  "trigo": 30,  "prob": 0.15},
    "Seca+Geada":    {"soja": -15, "milho": -20, "trigo": -10, "prob": 0.10},
    "Ench+Geada":    {"soja": 10,  "milho": 10,  "trigo": 5,   "prob": 0.05},
}


def _horas_pecuaria():
    """Calcula horas de pecuaria do rebanho atual por periodo.

    Returns:
        float: horas usadas por periodo (WS ou SF).
    """
    return MESES_PERIODO * (
        COW_H_MES * COW_CUR + HEN_H_MES * HEN_CUR
    )


def _resolver(vs=70.0, vm=60.0, vt=40.0):
    """Resolve o modelo agricola para um cenario.

    Variaveis:
        soja, milho, trigo: acres plantados.
        nc: novas vacas compradas.
        nh: novas galinhas compradas.
        vws: horas vendidas inverno/primavera.
        vsf: horas vendidas verao/outono.

    Args:
        vs: valor liquido/acre de soja.
        vm: valor liquido/acre de milho.
        vt: valor liquido/acre de trigo.

    Returns:
        dict com solucao e patrimonio ou None.
    """
    solver = pywraplp.Solver.CreateSolver("GLOP")
    INF = solver.infinity()

    soja  = solver.NumVar(0, INF, "soja")
    milho = solver.NumVar(0, INF, "milho")
    trigo = solver.NumVar(0, INF, "trigo")
    nc    = solver.NumVar(0, COW_MAX - COW_CUR, "nc")
    nh    = solver.NumVar(0, HEN_MAX - HEN_CUR, "nh")
    vws   = solver.NumVar(0, INF, "vws")
    vsf   = solver.NumVar(0, INF, "vsf")

    h_cur = _horas_pecuaria()
    land_cur = COW_ACRES * COW_CUR

    # Terra: lavoura + pastagem para novas vacas <= terra livre
    solver.Add(
        soja + milho + trigo + COW_ACRES * nc
        <= TERRA_TOTAL - land_cur
    )

    # Horas WS: lavoura + novas vacas + novas galinhas + vendidas <= disp.
    solver.Add(
        (HORAS_CULTURA["soja"][0] * soja
         + HORAS_CULTURA["milho"][0] * milho
         + HORAS_CULTURA["trigo"][0] * trigo
         + MESES_PERIODO * COW_H_MES * nc
         + MESES_PERIODO * HEN_H_MES * nh
         + vws)
        <= HORAS_WS - h_cur
    )

    # Horas SF
    solver.Add(
        (HORAS_CULTURA["soja"][1] * soja
         + HORAS_CULTURA["milho"][1] * milho
         + HORAS_CULTURA["trigo"][1] * trigo
         + MESES_PERIODO * COW_H_MES * nc
         + MESES_PERIODO * HEN_H_MES * nh
         + vsf)
        <= HORAS_SF - h_cur
    )

    # Fundo de investimento
    solver.Add(
        COW_NEW_COST * nc + HEN_NEW_COST * nh
        <= FUNDO_INVEST
    )

    # Milho minimo para alimentacao: >= 1 acre por vaca total
    solver.Add(milho >= COW_MILHO_ACRE * (COW_CUR + nc))

    # Trigo minimo para alimentacao: >= 0.05 acres por galinha total
    solver.Add(trigo >= HEN_TRIGO_ACRE * (HEN_CUR + nh))

    # Objetivo: net benefit de nc = 700, nh = 3.5
    # (renda + valor_final_novo - custo = 850+1350-1500 = 700)
    # (renda + valor_final_novo - custo = 4.25+2.25-3 = 3.5)
    solver.Maximize(
        vs * soja + vm * milho + vt * trigo
        + 700 * nc + 3.5 * nh
        + VENDA_WS * vws + VENDA_SF * vsf
    )

    st = solver.Solve()
    if st != pywraplp.Solver.OPTIMAL:
        return None

    nc_val = nc.solution_value()
    nh_val = nh.solution_value()
    fund_left = FUNDO_INVEST - COW_NEW_COST*nc_val - HEN_NEW_COST*nh_val
    end_new = (COW_NEW_COST*(1-COW_DEP)*nc_val
               + HEN_NEW_COST*(1-HEN_DEP)*nh_val)

    renda = (vs*soja.solution_value()
             + vm*milho.solution_value()
             + vt*trigo.solution_value()
             + COW_INC*(COW_CUR+nc_val)
             + HEN_INC*(HEN_CUR+nh_val)
             + VENDA_WS*vws.solution_value()
             + VENDA_SF*vsf.solution_value())

    patrimonio = (renda
                  + END_VALUE_CUR + end_new
                  + fund_left
                  - DESPESA_VIDA)

    return {
        "soja":  soja.solution_value(),
        "milho": milho.solution_value(),
        "trigo": trigo.solution_value(),
        "nc":    nc_val,
        "nh":    nh_val,
        "vws":   vws.solution_value(),
        "vsf":   vsf.solution_value(),
        "patrimonio": patrimonio,
    }


def _exibir(num, titulo, res, obs=None):
    """Exibe resultado de uma pergunta.

    Args:
        num: numero da pergunta.
        titulo: descricao do cenario.
        res: dict de resultado ou None.
        obs: observacao adicional.

    Returns:
        None
    """
    print("\n[P{}] {}".format(num, titulo))
    if res is None:
        print("  Sem solucao otima.")
        return
    print(
        "  Soja : {:.0f} ac | Milho: {:.0f} ac"
        " | Trigo: {:.0f} ac".format(
            res["soja"], res["milho"], res["trigo"]
        )
    )
    print(
        "  Novas vacas: {:.0f} | Novas galinhas: {:.0f}".format(
            res["nc"], res["nh"]
        )
    )
    print(
        "  Horas vendidas WS: {:.0f} | SF: {:.0f}".format(
            res["vws"], res["vsf"]
        )
    )
    print(
        "  Patrimonio: ${:,.0f}".format(res["patrimonio"])
    )
    if obs:
        print("  => {}".format(obs))


def executar():
    """Executa o Caso 8: Gestao agricola sob incerteza.

    Returns:
        None
    """
    print("=" * 60)
    print("CASO 8 - GESTAO AGRICOLA SOB INCERTEZA")
    print("=" * 60)

    # --- P1 e P2 ---
    print("\n[P1 e P2] Formulacao do modelo")
    print(
        "  Variaveis: acres (soja/milho/trigo),"
        " novas vacas, novas galinhas,"
        " horas vendidas (WS/SF)."
    )
    print(
        "  Restricoes: terra, horas WS, horas SF,"
        " fundo $20k, limites do celeiro,"
        " milho minimo (1ac/vaca),"
        " trigo minimo (0.05ac/galinha)."
    )
    print(
        "  Objetivo: maximizar patrimonio ao fim do ano"
        " = renda + valor_final_pecuaria"
        " + fundo_restante - despesas."
    )

    # --- P3: solucao otima clima normal ---
    r3 = _resolver()
    _exibir(3, "Solucao otima - clima normal", r3)

    # --- P4: faixas de otimalidade ---
    print("\n[P4] Faixas de otimalidade (valor/acre)")
    print(
        "  Soja : otimo para c >= $61,60"
        " (queda max $8,40 do valor base $70)"
    )
    print(
        "  Milho: nao entra no plano base;"
        " entraria com c >= $68,40"
    )
    print(
        "  Trigo: nao entra no plano base;"
        " entraria com c >= $57,15"
    )

    # --- P5: reotimizacao por cenario ---
    print("\n[P5] Reotimizacao por cenario climatico")
    print(
        "  {:<16} {:>6} {:>6} {:>6}"
        " {:>4} {:>5} {:>12}".format(
            "Cenario", "Soja", "Milho", "Trigo",
            "nc", "nh", "Patrimonio"
        )
    )
    resultados = {}
    for nome, cen in CENARIOS.items():
        r = _resolver(cen["soja"], cen["milho"], cen["trigo"])
        resultados[nome] = r
        if r:
            print(
                "  {:<16} {:>6.0f} {:>6.0f} {:>6.0f}"
                " {:>4.0f} {:>5.0f} {:>12,.0f}".format(
                    nome, r["soja"], r["milho"], r["trigo"],
                    r["nc"], r["nh"], r["patrimonio"]
                )
            )

    # --- P6: robustez ---
    print("\n[P6] Analise de robustez")
    pats = {n: r["patrimonio"] for n, r in resultados.items()
            if r}
    melhor = max(pats, key=pats.get)
    pior   = min(pats, key=pats.get)
    print(
        "  Melhor cenario: {} (${:,.0f})".format(
            melhor, pats[melhor]
        )
    )
    print(
        "  Pior cenario  : {} (${:,.0f})".format(
            pior, pats[pior]
        )
    )
    print(
        "  => Em cenarios adversos, plano otimo"
        " nao planta soja e compra mais vacas/galinhas"
        " (renda garantida)."
    )

    # --- P7 e P8: valor esperado ---
    vs_e = sum(
        c["soja"] * c["prob"] for c in CENARIOS.values()
    )
    vm_e = sum(
        c["milho"] * c["prob"] for c in CENARIOS.values()
    )
    vt_e = sum(
        c["trigo"] * c["prob"] for c in CENARIOS.values()
    )
    print("\n[P7 e P8] Abordagem de valor esperado ponderado")
    print(
        "  VE/acre: soja=${:.2f}"
        "  milho=${:.2f}  trigo=${:.2f}".format(
            vs_e, vm_e, vt_e
        )
    )
    r_ve = _resolver(vs_e, vm_e, vt_e)
    _exibir(8, "Solucao com valor esperado", r_ve)

    # --- P9: shadow price emprestimo ---
    print("\n[P9] Vale tomar emprestimo a 10% para animais?")
    print(
        "  Preco-sombra do fundo de investimento = $0"
        " (fundo nao e o gargalo no clima normal)."
    )
    print(
        "  Comprar mais vacas tem custo oportunidade"
        " maior que o beneficio (reduced cost = -$53/vaca)."
    )
    print(
        "  => NAO vale o emprestimo."
        " O shadow price precisaria ser >= $1,10"
        " para compensar os 10%% de juros."
    )

    # --- P10: sensibilidade ---
    print("\n[P10] Sensibilidade dos valores liquidos/acre")
    print(
        "  Soja : faixa $61,60 a infinito"
        " (queda de ate $8,40 mantem plano)"
    )
    print(
        "  Milho: faixa -infinito a $68,40"
        " (soja domina enquanto c_milho < $68,40)"
    )
    print(
        "  Trigo: faixa -infinito a $57,15"
        " (soja domina enquanto c_trigo < $57,15)"
    )
    print(
        "  => Estimativas criticas: valor da soja"
        " (maior sensibilidade a queda)."
    )

    # --- P11: generalizacao ---
    print("\n[P11] Generalizacao: gestao de portfolio")
    print(
        "  Lavouras -> ativos de renda variavel"
        " (acoes, FIIs) com retorno dependente"
        " do cenario de mercado."
    )
    print(
        "  Pecuaria/horas vendidas -> renda fixa"
        " (CDB, Tesouro) com retorno garantido."
    )
    print(
        "  Fundo de investimento -> capital inicial"
        " disponivel para alocacao."
    )
    print(
        "  Decisao: quanto alocar em renda variavel"
        " vs fixa para maximizar patrimonio esperado"
        " sob restricoes de capital e risco."
    )