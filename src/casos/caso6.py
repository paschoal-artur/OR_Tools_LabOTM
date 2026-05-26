"""Caso 6 - Pesquisa de mercado para banco digital."""
from ortools.linear_solver import pywraplp

# --- Dados do problema ---

REGIOES = ["Silicon Valley", "Big cities", "Small towns"]
FAIXAS = ["18 a 25", "26 a 40", "41 a 50", "51 ou mais"]

N_TOTAL = 2000

# Custos base por entrevistado ($)
CUSTOS_BASE = [
    [4.75, 6.50, 6.50, 5.00],  # Silicon Valley
    [5.25, 5.75, 6.25, 6.25],  # Big cities
    [6.50, 7.50, 7.50, 7.25]   # Small towns
]

# Custos atualizados para o item 5 ($)
CUSTOS_ATUALIZADOS = [
    [6.50, 6.50, 6.50, 5.00],
    [6.75, 5.75, 6.25, 6.25],
    [7.00, 7.50, 7.50, 7.25]
]

# Cotas mínimas percentuais (Modelo Base)
COTA_FAIXA_BASE = [0.20, 0.275, 0.15, 0.15]
COTA_REGIAO_BASE = [0.15, 0.35, 0.20]

# Cotas fixas exatas do item 6
COTA_FAIXA_FIXA = [0.25, 0.35, 0.20, 0.20]
COTA_REGIAO_FIXA = [0.20, 0.50, 0.30]


def _resolver(
    custos=CUSTOS_BASE,
    min_por_celula=0,
    max_18_25=None,
    max_silicon=None,
    usar_percentuais_fixos=False
):
    """Monta e resolve o modelo de otimização de amostragem com GLOP.

    Returns:
        dict: Resultado com custo, lance e matriz de alocação se ótimo, ou None.
    """
    solver = pywraplp.Solver.CreateSolver("GLOP")
    if not solver:
        return None

    n_r = len(REGIOES)
    n_f = len(FAIXAS)

    # Variáveis de decisão: x[i][j] = número de pessoas na região i da faixa j
    x = [
        [
            solver.NumVar(0, solver.infinity(), f"x[{i},{j}]")
            for j in range(n_f)
        ]
        for i in range(n_r)
    ]

    # Restrição 1: Total de entrevistados igual a 2000
    solver.Add(sum(x[i][j] for i in range(n_r) for j in range(n_f)) == N_TOTAL)

    # Restrições de amostragem (Mínimas ou Fixas Exatas)
    if usar_percentuais_fixos:
        # Item 6: Exige igualdade estrita com as novas proporções
        for j in range(n_f):
            solver.Add(sum(x[i][j] for i in range(n_r)) == COTA_FAIXA_FIXA[j] * N_TOTAL)
        for i in range(n_r):
            solver.Add(sum(x[i][j] for j in range(n_f)) == COTA_REGIAO_FIXA[i] * N_TOTAL)
    else:
        # Modelo Base e variações (Itens 1 a 5)
        for j in range(n_f):
            solver.Add(sum(x[i][j] for i in range(n_r)) >= COTA_FAIXA_BASE[j] * N_TOTAL)
        for i in range(n_r):
            solver.Add(sum(x[i][j] for j in range(n_f)) >= COTA_REGIAO_BASE[i] * N_TOTAL)

    # Restrição do Item 3: Exigência mínima por cruzamento (célula)
    if min_por_celula > 0:
        for i in range(n_r):
            for j in range(n_f):
                solver.Add(x[i][j] >= min_por_celula)

    # Restrições do Item 4: Limites máximos específicos
    if max_18_25 is not None:
        solver.Add(sum(x[i][0] for i in range(n_r)) <= max_18_25)
    if max_silicon is not None:
        solver.Add(sum(x[0][j] for j in range(n_f)) <= max_silicon)

    # Função Objetivo: Minimizar Custo de Coleta
    solver.Minimize(
        sum(custos[i][j] * x[i][j] for i in range(n_r) for j in range(n_f))
    )

    status = solver.Solve()

    if status != pywraplp.Solver.OPTIMAL:
        return None

    matriz_res = [[x[i][j].solution_value() for j in range(n_f)] for i in range(n_r)]
    custo_total = solver.Objective().Value()
    lance = custo_total * 1.15  # Margem de lucro de 15%

    return {"custo": custo_total, "lance": lance, "alocacao": matriz_res}


def _exibir_tabela(res):
    """Exibe o plano de amostragem formatado em matriz."""
    cabecalho = "{:<16}".format("") + "".join(f"{f:>12}" for f in FAIXAS)
    print(cabecalho)
    for i, reg in enumerate(REGIOES):
        linha = "{:<16}".format(reg)
        for j in range(len(FAIXAS)):
            linha += "{:>12.1f}".format(res["alocacao"][i][j])
        print(linha)


def executar():
    """Executa o Caso 6: Pesquisa de mercado para banco digital."""
    print("=" * 60)
    print("CASO 6 - PESQUISA DE MERCADO (BANCO DIGITAL)")
    print("=" * 60)

    # --- P1 & P2: Formulação Base e Lance ---
    r1 = _resolver()
    print("\n[P1 e P2] Modelo Base Otimizado")
    if r1:
        print("  Custo Total de Coleta : ${:,.2f}".format(r1["custo"]))
        print("  Lance com 15% de Margem: ${:,.2f}".format(r1["lance"]))
        print("\n  Plano de Amostragem (Pessoas):")
        _exibir_tabela(r1)
    else:
        print("  Erro ao resolver o modelo base.")

    # --- P3: Mínimo de 50 pessoas por célula ---
    r3 = _resolver(min_por_celula=50)
    print("\n[P3] Adição de Cota Mínima de 50 Pessoas por Célula")
    if r3:
        print("  Novo Custo Total      : ${:,.2f}".format(r3["custo"]))
        print("  Novo Lance Sugerido   : ${:,.2f}".format(r3["lance"]))
        print("  => Impacto financeiro : ${:,.2f}".format(r3["lance"] - r1["lance"]))
    else:
        print("  Infactível com as restrições informadas.")

    # --- P4: Restrições de Máximo Cumulativas ---
    r4 = _resolver(min_por_celula=50, max_18_25=600, max_silicon=650)
    print("\n[P4] Limite Máximo (18-25 anos <= 600 e Silicon Valley <= 650)")
    if r4:
        print("  Novo Custo Total      : ${:,.2f}".format(r4["custo"]))
        print("  Novo Lance Sugerido   : ${:,.2f}".format(r4["lance"]))
        print("  => Diferença para P3   : ${:,.2f}".format(r4["lance"] - r3["lance"]))
    else:
        print("  Infactível: restrições de máximo entram em conflito com as cotas mínimas.")

    # --- P5: Custos Atualizados para o Grupo de 18-25 anos ---
    r5 = _resolver(custos=CUSTOS_ATUALIZADOS, min_por_celula=50, max_18_25=600, max_silicon=650)
    print("\n[P5] Atualização de Custos na Faixa de 18-25 Anos")
    if r5:
        print("  Novo Custo com Reajuste: ${:,.2f}".format(r5["custo"]))
        print("  Novo Lance Calculado   : ${:,.2f}".format(r5["lance"]))
        print("\n  Nova Configuração do Plano:")
        _exibir_tabela(r5)
    else:
        print("  Modelo sem solução viável.")

    # --- P6: Proporções Populacionais Fixas Rigorosas ---
    r6 = _resolver(usar_percentuais_fixos=True)
    print("\n[P6] Restrições Rígidas de Proporção Populacional Estrita")
    if r6:
        print("  Custo com Proporção Fixa: ${:,.2f}".format(r6["custo"]))
        print("  Lance Final com Proporção: ${:,.2f}".format(r6["lance"]))
        print("  Aumento do custo base (P6 vs P1): ${:,.2f}".format(r6["custo"] - r1["custo"]))
        print("\n  Plano de Amostragem Perfeito:")
        _exibir_tabela(r6)
    else:
        print("  Infactível: As proporções fixas de linhas e colunas não se equilibram matematicamente.")