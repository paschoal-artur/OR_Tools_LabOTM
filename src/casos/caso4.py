"""Caso 4 - Escala de operadores em central de atendimento."""
import math
from ortools.sat.python import cp_model

CHAMADAS = [40, 85, 70, 95, 80, 35, 10]
PROD = 6
PCT_ESP = 0.20

# Tipos de operador e seus custos (tempo em telefone):
# EFT7 : fone slots 1,3  -> 2h@$10 + 2h@$10 = $40
# EFT9 : fone slots 2,4  -> 2h@$10 + 2h@$10 = $40
# EFT11: fone slots 3,5  -> 2h@$10 + 2h@$10 = $40
# EFT13: fone slots 4,6  -> 2h@$10 + 2h@$12 = $44
# EFT5 : fone slots 5,7  -> 2h@$10 + 2h@$12 = $44
#         (inicia 13h, admin primeiro -> fone 15-17 e 19-21)
# EPT15: fone slots 5,6  -> 2h@$10 + 2h@$12 = $44
# EPT17: fone slots 6,7  -> 2h@$12 + 2h@$12 = $48

CUSTO_EFT = [40, 40, 40, 44, 44]   # starts: 7,9,11,13,FT5
CUSTO_SFT = [40, 40, 40, 44, 44]   # starts: 7,9,11,13,FT5
CUSTO_PT  = [44, 48]                # starts: 15,17


def _necessarios(pct=1.0):
    """Calcula operadores necessarios por slot.

    Args:
        pct: fracao do volume de chamadas.

    Returns:
        list com ceil por slot.
    """
    return [math.ceil(ch * pct / PROD) for ch in CHAMADAS]


def _resolver_mono(eft5_max=None):
    """Resolve o modelo monolingual.

    Inclui o 5o tipo de integral (EFT5/SFT5):
    operador que inicia trabalho as 13h pelo bloco
    administrativo, com fone nos slots 5 (15-17h)
    e 7 (19-21h).

    Args:
        eft5_max: limite superior para EFT5 (P4).

    Returns:
        dict com quantidades e custo, ou None.
    """
    mdl = cp_model.CpModel()
    INF = 50

    # Ingles: 5 integrais + 2 parciais
    eft = [mdl.NewIntVar(0, INF, "EFT{}".format(t))
           for t in [7, 9, 11, 13, 5]]
    ept = [mdl.NewIntVar(0, INF, "EPT{}".format(t))
           for t in [15, 17]]

    # Espanhol: 5 integrais (sem parciais)
    sft = [mdl.NewIntVar(0, INF, "SFT{}".format(t))
           for t in [7, 9, 11, 13, 5]]

    nE = _necessarios(1 - PCT_ESP)
    nS = _necessarios(PCT_ESP)

    # Cobertura ingles por slot
    # slot1: EFT7
    mdl.Add(eft[0] >= nE[0])
    # slot2: EFT9
    mdl.Add(eft[1] >= nE[1])
    # slot3: EFT7 + EFT11
    mdl.Add(eft[0] + eft[2] >= nE[2])
    # slot4: EFT9 + EFT13
    mdl.Add(eft[1] + eft[3] >= nE[3])
    # slot5: EFT11 + EFT5 + EPT15
    mdl.Add(eft[2] + eft[4] + ept[0] >= nE[4])
    # slot6: EFT13 + EPT15 + EPT17
    mdl.Add(eft[3] + ept[0] + ept[1] >= nE[5])
    # slot7: EFT5 + EPT17
    mdl.Add(eft[4] + ept[1] >= nE[6])

    # Cobertura espanhol por slot
    mdl.Add(sft[0] >= nS[0])
    mdl.Add(sft[1] >= nS[1])
    mdl.Add(sft[0] + sft[2] >= nS[2])
    mdl.Add(sft[1] + sft[3] >= nS[3])
    mdl.Add(sft[2] + sft[4] >= nS[4])
    mdl.Add(sft[3] >= nS[5])
    mdl.Add(sft[4] >= nS[6])

    if eft5_max is not None:
        mdl.Add(eft[4] <= eft5_max)

    custo = sum(CUSTO_EFT[i] * eft[i] for i in range(5))
    custo += sum(CUSTO_SFT[i] * sft[i] for i in range(5))
    custo += sum(CUSTO_PT[i] * ept[i] for i in range(2))
    mdl.Minimize(custo)

    solver = cp_model.CpSolver()
    st = solver.Solve(mdl)
    if st not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        return None

    return {
        "EFT7":  solver.Value(eft[0]),
        "EFT9":  solver.Value(eft[1]),
        "EFT11": solver.Value(eft[2]),
        "EFT13": solver.Value(eft[3]),
        "EFT5":  solver.Value(eft[4]),
        "EPT15": solver.Value(ept[0]),
        "EPT17": solver.Value(ept[1]),
        "SFT7":  solver.Value(sft[0]),
        "SFT9":  solver.Value(sft[1]),
        "SFT11": solver.Value(sft[2]),
        "SFT13": solver.Value(sft[3]),
        "SFT5":  solver.Value(sft[4]),
        "custo": solver.ObjectiveValue(),
    }


def _resolver_bili():
    """Resolve o modelo com todos os operadores bilingues.

    Inclui o 5o tipo de integral bilingue (BFT5).

    Returns:
        dict com quantidades e custo, ou None.
    """
    mdl = cp_model.CpModel()
    INF = 50

    bft = [mdl.NewIntVar(0, INF, "BFT{}".format(t))
           for t in [7, 9, 11, 13, 5]]
    bpt = [mdl.NewIntVar(0, INF, "BPT{}".format(t))
           for t in [15, 17]]

    nB = _necessarios(1.0)

    mdl.Add(bft[0] >= nB[0])
    mdl.Add(bft[1] >= nB[1])
    mdl.Add(bft[0] + bft[2] >= nB[2])
    mdl.Add(bft[1] + bft[3] >= nB[3])
    mdl.Add(bft[2] + bft[4] + bpt[0] >= nB[4])
    mdl.Add(bft[3] + bpt[0] + bpt[1] >= nB[5])
    mdl.Add(bft[4] + bpt[1] >= nB[6])

    custo = sum(CUSTO_EFT[i] * bft[i] for i in range(5))
    custo += sum(CUSTO_PT[i] * bpt[i] for i in range(2))
    mdl.Minimize(custo)

    solver = cp_model.CpSolver()
    st = solver.Solve(mdl)
    if st not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        return None

    return {
        "BFT7":  solver.Value(bft[0]),
        "BFT9":  solver.Value(bft[1]),
        "BFT11": solver.Value(bft[2]),
        "BFT13": solver.Value(bft[3]),
        "BFT5":  solver.Value(bft[4]),
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
        "  Integrais ingles : EFT7={EFT7} EFT9={EFT9}"
        " EFT11={EFT11} EFT13={EFT13}"
        " EFT5(15+21h)={EFT5}".format(**res)
    )
    print(
        "  Integrais esp.   : SFT7={SFT7} SFT9={SFT9}"
        " SFT11={SFT11} SFT13={SFT13}"
        " SFT5(15+21h)={SFT5}".format(**res)
    )
    print(
        "  Parciais ingles  : EPT15={EPT15}"
        " EPT17={EPT17}".format(**res)
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

    # --- P1 ---
    print("\n[P1] Operadores necessarios por turno de 2h")
    header = "{:>6}".format("Turno") + "".join(
        "{:>5}".format("S{}".format(i + 1))
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

    # --- P2 ---
    print("\n[P2] Formulacao do modelo (resumo)")
    print(
        "  5 tipos de integral (ingles e espanhol):"
        " inicio de fone as 7,9,11,13h e o 5o tipo"
    )
    print(
        "  que inicia o dia as 13h pelo bloco"
        " administrativo (fone as 15h e 19h)."
    )
    print(
        "  2 tipos de parcial (so ingles): inicio as 15h"
        " ou 17h."
    )
    print(
        "  Objetivo: minimizar custo de telefone."
    )

    # --- P3 ---
    r3 = _resolver_mono()
    _print_mono(3, "Solucao otima monolingual", r3)

    # --- P4 ---
    r4 = _resolver_mono(eft5_max=1)
    delta4 = r4["custo"] - r3["custo"] if r4 else 0
    obs4 = "Custo aumenta ${:.0f} (EFT5 forcado de 2 para 1)".format(
        delta4
    )
    _print_mono(
        4,
        "Max 1 integral ingles iniciando as 13h"
        " (com admin primeiro)",
        r4, obs4
    )

    # --- P5 ---
    print("\n[P5] Operadores bilingues necessarios por slot")
    print(header)
    print(
        "{:>6}".format("Bili.") + "".join(
            "{:>5}".format(v) for v in nB
        )
    )

    # --- P6 ---
    r6 = _resolver_bili()
    print("\n[P6] Solucao otima bilingue")
    if r6:
        print(
            "  Integrais: BFT7={BFT7} BFT9={BFT9}"
            " BFT11={BFT11} BFT13={BFT13}"
            " BFT5={BFT5}".format(**r6)
        )
        print(
            "  Parciais : BPT15={BPT15}"
            " BPT17={BPT17}".format(**r6)
        )
        print(
            "  Custo total: ${:.0f}".format(r6["custo"])
        )

    # --- P7 ---
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
            " mais por hora sem elevar o custo"
            " total.".format(pct)
        )

    # --- P8 ---
    print("\n[P8] Melhorias operacionais sugeridas")
    melhorias = [
        "Operadores bilingues (coberto em P5-P7).",
        "IVR/chatbot para triagem de chamadas"
        " simples, reduzindo volume nos picos.",
        "Callback agendado nos picos (13-15h)"
        " para suavizar demanda.",
        "Escala dinamica ajustada semanalmente"
        " com dados reais de volume.",
        "Investigar produtividade: elevar de 6"
        " para 7+ chamadas/h reduz numero de"
        " operadores necessarios.",
    ]
    for m in melhorias:
        print("  - {}".format(m))