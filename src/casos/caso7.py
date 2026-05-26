"""Caso 7 - Alocacao de estudantes em escolas."""
from ortools.linear_solver import pywraplp

# --- Dados do problema ---
AREAS = ["Area 1", "Area 2", "Area 3", "Area 4", "Area 5", "Area 6"]
ESCOLAS = ["Escola 1", "Escola 2", "Escola 3"]

ESTUDANTES = [450, 600, 550, 350, 500, 450]
CAPACIDADE = [900, 1100, 1000]

# Proporção por série [6º, 7º, 8º] para cada área
PCT_SERIES = [
    [0.32, 0.38, 0.30],
    [0.37, 0.28, 0.35],
    [0.30, 0.32, 0.38],
    [0.28, 0.40, 0.32],
    [0.39, 0.34, 0.27],
    [0.34, 0.28, 0.38]
]

# Custos de transporte ($) por estudante da Area i para a Escola j.
# None representa rotas inviáveis.
CUSTOS_BASE = [
    [300, 0, 700],
    [None, 400, 500],
    [600, 300, 200],
    [200, 500, None],
    [0, None, 400],
    [500, 300, 0]
]

def _ajustar_custos(custos_originais, remover_valores):
    """Cria uma nova matriz zerando os custos de rotas eliminadas."""
    novos_custos = []
    for i in range(len(AREAS)):
        linha = []
        for j in range(len(ESCOLAS)):
            v = custos_originais[i][j]
            if v in remover_valores:
                linha.append(0)
            else:
                linha.append(v)
        novos_custos.append(linha)
    return novos_custos


def _resolver(custos=CUSTOS_BASE, alocacao_inteira_por_area=False):
    """Monta e resolve o modelo de designacao escolar.

    Args:
        custos: matriz de custos de transporte.
        alocacao_inteira_por_area: se True, uma area inteira vai para apenas 1 escola.

    Returns:
        dict com resultado ou None.
    """
    # Usa SCIP para MIP (inteiros) e GLOP para PL contínua
    tipo_solver = "SCIP" if alocacao_inteira_por_area else "GLOP"
    solver = pywraplp.Solver.CreateSolver(tipo_solver)
    if not solver:
        return None

    n_a = len(AREAS)
    n_e = len(ESCOLAS)

    x = {}
    y = {} # Variável binária usada apenas para alocação de área inteira

    # Criar variáveis
    for i in range(n_a):
        for j in range(n_e):
            if custos[i][j] is not None:
                if alocacao_inteira_por_area:
                    y[i, j] = solver.IntVar(0, 1, f"y_{i}_{j}")
                    x[i, j] = solver.NumVar(0, ESTUDANTES[i], f"x_{i}_{j}")
                    solver.Add(x[i, j] == y[i, j] * ESTUDANTES[i])
                else:
                    x[i, j] = solver.NumVar(0, ESTUDANTES[i], f"x_{i}_{j}")
            else:
                # Se for inviável, forçamos a 0
                x[i, j] = solver.NumVar(0, 0, f"x_{i}_{j}")

    # Restrição: Demanda total da área deve ser alocada
    if alocacao_inteira_por_area:
        for i in range(n_a):
            solver.Add(sum(y[i, j] for j in range(n_e) if custos[i][j] is not None) == 1)
    else:
        for i in range(n_a):
            solver.Add(sum(x[i, j] for j in range(n_e)) == ESTUDANTES[i])

    # Restrição: Capacidade das escolas não pode ser excedida
    for j in range(n_e):
        solver.Add(sum(x[i, j] for i in range(n_a)) <= CAPACIDADE[j])

    # Restrições de Equilíbrio das Séries (entre 30% e 36%)
    for j in range(n_e):
        T_j = sum(x[i, j] for i in range(n_a))  # Total de alunos na escola j
        for g in range(3):  # 6º, 7º, 8º
            alunos_na_serie = sum(x[i, j] * PCT_SERIES[i][g] for i in range(n_a))
            solver.Add(alunos_na_serie >= 0.30 * T_j)
            solver.Add(alunos_na_serie <= 0.36 * T_j)

    # Função Objetivo: Minimizar Custo de Transporte
    custo_total = 0
    for i in range(n_a):
        for j in range(n_e):
            if custos[i][j] is not None:
                custo_total += x[i, j] * custos[i][j]

    solver.Minimize(custo_total)
    status = solver.Solve()

    if status != pywraplp.Solver.OPTIMAL:
        return None

    matriz_res = [[0]*n_e for _ in range(n_a)]
    for i in range(n_a):
        for j in range(n_e):
            if custos[i][j] is not None:
                matriz_res[i][j] = x[i, j].solution_value()

    return {"custo": solver.Objective().Value(), "alocacao": matriz_res}


def _exibir_tabela(res):
    """Exibe o plano de alocacao formatado em matriz."""
    cabecalho = "{:<12}".format("") + "".join(f"{e:>12}" for e in ESCOLAS)
    print(cabecalho)
    for i, area in enumerate(AREAS):
        linha = "{:<12}".format(area)
        for j in range(len(ESCOLAS)):
            linha += "{:>12.0f}".format(res["alocacao"][i][j])
        print(linha)


def executar():
    """Executa o Caso 7: Alocacao de estudantes em escolas."""
    print("=" * 60)
    print("CASO 7 - ALOCACAO DE ESTUDANTES EM ESCOLAS")
    print("=" * 60)

    # --- P1, P2 e P3: Modelo Base ---
    r_base = _resolver()
    print("\n[P1, P2 e P3] Recomendacao de Alocacao Base (Permite divisao)")
    if r_base:
        print("  Custo Anual Total de Transporte: ${:,.2f}".format(r_base["custo"]))
        print("\n  Plano de Alocacao (Estudantes):")
        _exibir_tabela(r_base)
    else:
        print("  Modelo inviável.")

    # --- P4: Alocacao integral por area ---
    r_int = _resolver(alocacao_inteira_por_area=True)
    print("\n[P4] Alocacao forcando as areas inteiras para apenas uma escola")
    if r_int:
        print("  Novo Custo Anual Total: ${:,.2f}".format(r_int["custo"]))
        print("  Aumento do custo      : ${:,.2f}".format(r_int["custo"] - r_base["custo"]))
        print("  => Ao retirar a flexibilidade de dividir areas, o solver precisa")
        print("     alocar blocos inteiros de estudantes para escolas mais caras")
        print("     para satisfazer as restricoes rigidas de 30%-36% das series.")
        print("\n  Plano Inteiro:")
        _exibir_tabela(r_int)
    else:
        print("  Inviavel: Nao e possivel atender aos percentuais de series sem dividir areas.")

    # --- P5: Opcao 1 - Zerar custos de 1 a 1.5 milha ($200) ---
    custos_p5 = _ajustar_custos(CUSTOS_BASE, [200])
    r_p5 = _resolver(custos=custos_p5)
    print("\n[P5] Opcao 1: Eliminar transporte para $200 (alunos vao andando)")
    if r_p5:
        print("  Novo Custo ao Distrito: ${:,.2f}".format(r_p5["custo"]))
        print("  Reducao vs Base       : ${:,.2f}".format(r_base["custo"] - r_p5["custo"]))
    else:
        print("  Modelo inviavel.")

    # --- P6: Opcao 2 - Zerar custos ate 2 milhas ($200 e $300) ---
    custos_p6 = _ajustar_custos(CUSTOS_BASE, [200, 300])
    r_p6 = _resolver(custos=custos_p6)
    print("\n[P6] Opcao 2: Eliminar transporte para $200 e $300 (ate 2 milhas)")
    if r_p6:
        print("  Novo Custo ao Distrito: ${:,.2f}".format(r_p6["custo"]))
        print("  Reducao vs Base       : ${:,.2f}".format(r_base["custo"] - r_p6["custo"]))

    # --- P7 e P8: Trade-offs e Recomendacao Final ---
    print("\n[P7 e P8] Analise de Trade-off e Recomendacao Final")
    print("  Opcao Base : Custo total suportado pelo distrito (Seguranca Alta).")
    print("  Opcao 1    : Reducao consideravel de custos, exigindo caminhada de ate 1.5 milhas.")
    print("  Opcao 2    : Maior reducao, exigindo caminhada de ate 2 milhas (Seguranca Baixa).")
    print("\n  RECOMENDACAO:")
    print("  A Opcao 1 (eliminar transporte de $200) e o cenario mais recomendado.")
    print("  Ela atinge uma reducao significativa de gastos publicos mantendo o esforco")
    print("  fisico e a seguranca dos estudantes em um limite razoavel (1.5 milhas).")
    print("  Obrigar os jovens do fundamental II a caminhar ate 2 milhas sob qualquer clima")
    print("  (Opcao 2) pode gerar atrito com os pais e evasao, nao compensando a economia extra.")