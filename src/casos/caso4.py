"""Caso 4 - Escala de operadores em central de atendimento."""
import math
from ortools.sat.python import cp_model

# --- Dados base ---
# Turnos de 2h: S1=7-9, S2=9-11, S3=11-13, S4=13-15,
#               S5=15-17, S6=17-19, S7=19-21
CHAMADAS = [40, 85, 70, 95, 80, 35, 10]  # por hora/slot
PROD = 6          # chamadas/hora por operador
PCT_ESP = 0.20    # fracao em espanhol

# Padrao "telefone primeiro" para integrais:
# start 7  -> fone slots 1,3  | start 9  -> slots 2,4
# start 11 -> fone slots 3,5  | start 13 -> slots 4,6
# PT start 15 -> slots 5,6   | PT start 17 -> slots 6,7

# Custo por trabalhador (somente tempo em telefone):
# EFT7 : 2h@$10 + 2h@$10 = $40
# EFT9 : 2h@$10 + 2h@$10 = $40
# EFT11: 2h@$10 + 2h@$10 = $40
# EFT13: 2h@$10(slot4) + 2h@$12(slot6) = $44
# EPT15: 2h@$10(slot5) + 2h@$12(slot6) = $44
# EPT17: 2h@$12 + 2h@$12 = $48
CUSTO_EFT = [40, 40, 40, 44]  # start 7,9,11,13
CUSTO_SFT = [40, 40, 40, 44]  # start 7,9,11,13
CUSTO_PT  = [44, 48]          # start 15,17


def _necessarios(pct=1.0):
    """Calcula operadores necessarios por slot.

    Args:
        pct: fracao do volume de chamadas (1.0=total,
             0.8=ingles, 0.2=espanhol).

    Returns:
        list com ceil(chamadas*pct/PROD) para cada slot.
    """
    return [
        math.ceil(ch * pct / PROD) for ch in CHAMADAS
    ]


def _resolver_mono(eft13_max=None):
    """Resolve o modelo monolingual com CP-SAT.

    Variaveis: EFT7,9,11,13 (ingles), SFT7,9,11,13
    (espanhol), EPT15,17 (ingles parcial).

    Args:
        eft13_max: limite superior para EFT13 (P4).

    Returns:
        dict com quantidades e custo, ou None.
    """
    mdl = cp_model.CpModel()
    INF = 50

    eft = [mdl.NewIntVar(0, INF, "EFT{}".format(t))
           for t in [7, 9, 11, 13]]
    sft = [mdl.NewIntVar(0, INF, "SFT{}".format(t))
           for t in [7, 9, 11, 13]]
    ept = [mdl.NewIntVar(0, INF, "EPT{}".format(t))
           for t in [15, 17]]

    nE = _necessarios(1 - PCT_ESP)
    nS = _necessarios(PCT_ESP)

    # Cobertura ingles por slot
    mdl.Add(eft[0] >= nE[0])                          # S1
    mdl.Add(eft[1] >= nE[1])                          # S2
    mdl.Add(eft[0] + eft[2] >= nE[2])                 # S3
    mdl.Add(eft[1] + eft[3] >= nE[3])                 # S4
    mdl.Add(eft[2] + ept[0] >= nE[4])                 # S5
    mdl.Add(eft[3] + ept[0] + ept[1] >= nE[5])        # S6
    mdl.Add(ept[1] >= nE[6])                           # S7

    # Cobertura espanhol por slot (S7 sem cobertura)
    mdl.Add(sft[0] >= nS[0])                          # S1
    mdl.Add(sft[1] >= nS[1])                          # S2
    mdl.Add(sft[0] + sft[2] >= nS[2])                 # S3
    mdl.Add(sft[1] + sft[3] >= nS[3])                 # S4
    mdl.Add(sft[2] >= nS[4])                           # S5
    mdl.Add(sft[3] >= nS[5])                           # S6
    # S7 espanhol: sem operador disponivel (gap estrutural)

    if eft13_max is not None:
        mdl.Add(eft[3] <= eft13_max)

    custo = sum(CUSTO_EFT[i] * eft[i] for i in range(4))
    custo += sum(CUSTO_SFT[i] * sft[i] for i in range(4))
    custo += sum(CUSTO_PT[i] * ept[i] for i in range(2))
    mdl.Minimize(custo)

    solver = cp_model.CpSolver()
    st = solver.Solve(mdl)

    if st not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        return None
    return {
        "EFT7": solver.Value(eft[0]),
        "EFT9": solver.Value(eft[1]),
        "EFT11": solver.Value(eft[2]),
        "EFT13": solver.Value(eft[3]),
        "SFT7": solver.Value(sft[0]),
        "SFT9": solver.Value(sft[1]),
        "SFT11": solver.Value(sft[2]),
        "SFT13": solver.Value(sft[3]),
        "EPT15": solver.Value(ept[0]),
        "EPT17": solver.Value(ept[1]),
        "custo": solver.ObjectiveValue(),
    }


def _resolver_bili():
    """Resolve o modelo com todos os operadores bilingues.

    Returns:
        dict com quantidades e custo, ou None.
    """
    mdl = cp_model.CpModel()
    INF = 50

    bft = [mdl.NewIntVar(0, INF, "BFT{}".format(t))
           for t in [7, 9, 11, 13]]
    bpt = [mdl.NewIntVar(0, INF, "BPT{}".format(t))
           for t in [15, 17]]

    nB = _necessarios(1.0)

    mdl.Add(bft[0] >= nB[0])
    mdl.Add(bft[1] >= nB[1])
    mdl.Add(bft[0] + bft[2] >= nB[2])
    mdl.Add(bft[1] + bft[3] >= nB[3])
    mdl.Add(bft[2] + bpt[0] >= nB[4])
    mdl.Add(bft[3] + bpt[0] + bpt[1] >= nB[5])
    mdl.Add(bpt[1] >= nB[6])

    custo = sum(CUSTO_EFT[i] * bft[i] for i in range(4))
    custo += sum(CUSTO_PT[i] * bpt[i] for i in range(2))
    mdl.Minimize(custo)

    solver = cp_model.CpSolver()
    st = solver.Solve(mdl)

    if st not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        return None
    return {
        "BFT7": solver.Value(bft[0]),
        "BFT9": solver.Value(bft[1]),
        "BFT11": solver.Value(bft[2]),
        "BFT13": solver.Value(bft[3]),
        "BPT15": solver.Value(bpt[0]),
        "BPT17": solver.Value(bpt[1]),
        "custo": solver.ObjectiveValue(),
    }


def _print_mono(num, titulo, res, obs=None):
    """Exibe resultado do modelo monolingual.

    Args:
        num: numero da pergunta.
        titulo: descricao do cenario.
        res: dict de resultado.
        obs: observacao adicional.

    Returns:
        None
    """
    print("\n[P{}] {}".format(num, titulo))
    if res is None:
        print("  Sem solucao.")
        return
    print(
        "  Integrais ingles : "
        "EFT7={EFT7} EFT9={EFT9}"
        " EFT11={EFT11} EFT13={EFT13}".format(**res)
    )
    print(
        "  Integrais esp.   : "
        "SFT7={SFT7} SFT9={SFT9}"
        " SFT11={SFT11} SFT13={SFT13}".format(**res)
    )
    print(
        "  Parciais ingles  : "
        "EPT15={EPT15} EPT17={EPT17}".format(**res)
    )
    print(
        "  Custo total      : ${:.0f}".format(res["custo"])
    )
    if obs:
        print("  => {}".format(obs))


def executar():
    """Executa o Caso 4: Escala de operadores.

    Returns:
        None
    """
    print("=" * 60)
    print("CASO 4 - ESCALA DE OPERADORES (CALL CENTER)")
    print("=" * 60)

    nE = _necessarios(1 - PCT_ESP)
    nS = _necessarios(PCT_ESP)
    nB = _necessarios(1.0)

    # --- P1: operadores necessarios por slot ---
    print("\n[P1] Operadores necessarios por turno de 2h")
    header = "{:>6}".format("Turno") + "".join(
        "{:>5}".format("S{}".format(i+1))
        for i in range(7)
    )
    print(header)
    print(
        "{:>6}".format("Ingles") + "".join(
            "{:>5}".format(v) for v in nE
        )
    )
    print(
        "{:>6}".format("Esp.") + "".join(
            "{:>5}".format(v) for v in nS
        )
    )
    print(
        "  OBS: slot 7 (19-21) precisa de {} esp."
        " mas nenhum turno de integral cobre"
        " esse slot -> gap estrutural.".format(nS[6])
    )

    # --- P2: formulacao (descritiva) ---
    print("\n[P2] Formulacao do modelo (resumo)")
    print(
        "  Variaveis: EFT7/9/11/13 (integrais ingles),"
        " SFT7/9/11/13 (espanhol),"
    )
    print(
        "  EPT15/17 (parciais ingles)."
    )
    print(
        "  Objetivo: minimizar custo de telefone."
    )
    print(
        "  Restricoes: cobertura >= demanda em cada slot"
        " para cada idioma."
    )

    # --- P3: solucao otima ---
    r3 = _resolver_mono()
    _print_mono(3, "Solucao otima monolingual", r3)

    # --- P4: EFT13 <= 1 ---
    r4 = _resolver_mono(eft13_max=1)
    obs4 = (
        "Plano identico ao P3 (EFT13=0 ja era otimo,"
        " restricao nao vinculante)"
        if r4 and abs(r4["custo"] - r3["custo"]) < 0.5
        else "Custo aumentou para ${:.0f}".format(
            r4["custo"]
        )
    )
    _print_mono(4, "Maximo 1 integral ingles inicio 13h",
                r4, obs4)

    # --- P5: operadores bilingues por slot ---
    print("\n[P5] Operadores bilingues necessarios por slot")
    print(header)
    print(
        "{:>6}".format("Bili.") + "".join(
            "{:>5}".format(v) for v in nB
        )
    )

    # --- P6: modelo bilingue ---
    r6 = _resolver_bili()
    print("\n[P6] Solucao otima bilingue")
    if r6:
        print(
            "  Integrais: BFT7={BFT7} BFT9={BFT9}"
            " BFT11={BFT11} BFT13={BFT13}".format(**r6)
        )
        print(
            "  Parciais : BPT15={BPT15}"
            " BPT17={BPT17}".format(**r6)
        )
        print(
            "  Custo total: ${:.0f}".format(r6["custo"])
        )

    # --- P7: aumento max. salarial bilingue ---
    print("\n[P7] Aumento percentual max. para bilingues")
    if r3 and r6:
        pct = (r3["custo"] / r6["custo"] - 1) * 100
        print(
            "  Custo mono : ${:.0f}".format(r3["custo"])
        )
        print(
            "  Custo bili : ${:.0f}".format(r6["custo"])
        )
        print(
            "  Aumento max: {:.2f}%".format(pct)
        )
        print(
            "  => Bilingues podem custar ate {:.2f}%"
            " a mais sem elevar custo total.".format(pct)
        )

    # --- P8: melhorias operacionais ---
    print("\n[P8] Melhorias operacionais sugeridas")
    melhorias = [
        "Operadores bilingues (coberto em P5-P7).",
        "IVR/chatbot para triagem de chamadas"
        " simples, reduzindo volume.",
        "Callback agendado nos picos (13-15h)"
        " para suavizar demanda.",
        "Turno parcial extra cobrindo slot 7 em"
        " espanhol (gap estrutural atual).",
        "Escala dinamica ajustada semanalmente"
        " com dados reais de volume.",
    ]
    for m in melhorias:
        print("  - {}".format(m))