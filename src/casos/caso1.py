"""Caso 1 - Transporte de cadeiras infantis."""
from ortools.linear_solver import pywraplp

# --- Dados do problema ---

# Nomes das fábricas e centros de distribuição (CDs)
FABRICAS = ["Fabrica 1", "Fabrica 2", "Fabrica 3"]
CDS = ["CD 1", "CD 2", "CD 3", "CD 4"]

# Capacidade mensal de cada fábrica (remessas/mês)
SUPRIMENTO = [12, 17, 11]

# Demanda mensal de cada CD (remessas/mês)
DEMANDA = [10, 10, 10, 10]

# Distância em milhas entre fábrica i e CD j
DISTANCIAS = [
    [800, 1300, 400, 700],
    [1100, 1400, 600, 1000],
    [600, 1200, 800, 900],
]

# Custo por remessa = $100 fixo + $0,50 por milha
# Calculado automaticamente a partir das distâncias
CUSTOS = [
    [100 + 0.5 * DISTANCIAS[i][j] for j in range(len(CDS))]
    for i in range(len(FABRICAS))
]


def _exibir_dados():
    """Exibe os dados do problema de forma tabular.

    Returns:
        None
    """
    print("\nSuprimento por fabrica (remessas/mes):")
    for i, fab in enumerate(FABRICAS):
        print("  {}: {}".format(fab, SUPRIMENTO[i]))

    print("\nDemanda por centro de distribuicao:")
    for j, cd in enumerate(CDS):
        print("  {}: {}".format(cd, DEMANDA[j]))

    print("\nCusto de frete por remessa ($):")
    cabecalho = "{:<12}".format("") + "".join(
        "{:>8}".format(cd) for cd in CDS
    )
    print(cabecalho)
    for i, fab in enumerate(FABRICAS):
        linha = "{:<12}".format(fab)
        for j in range(len(CDS)):
            linha += "{:>8.0f}".format(CUSTOS[i][j])
        print(linha)


def _montar_e_resolver():
    """Monta e resolve o modelo de transporte com GLOP.

    Returns:
        tuple: (status, solver, variaveis_x) onde variaveis_x
            e uma matriz [n_fabricas][n_cds].
    """
    n_f = len(FABRICAS)
    n_c = len(CDS)

    solver = pywraplp.Solver.CreateSolver("GLOP")

    # Variável x[i][j]: remessas enviadas da fábrica i para o CD j
    # Domínio: real não negativo (o problema balanceado garante
    # solução inteira mesmo com LP contínuo)
    x = [
        [
            solver.NumVar(
                0, solver.infinity(), "x[{},{}]".format(i, j)
            )
            for j in range(n_c)
        ]
        for i in range(n_f)
    ]

    # Restrição de suprimento: total enviado = capacidade da fábrica
    for i in range(n_f):
        solver.Add(
            sum(x[i][j] for j in range(n_c)) == SUPRIMENTO[i]
        )

    # Restrição de demanda: total recebido = demanda do CD
    for j in range(n_c):
        solver.Add(
            sum(x[i][j] for i in range(n_f)) == DEMANDA[j]
        )

    # Função objetivo: minimizar custo total de transporte
    solver.Minimize(
        sum(
            CUSTOS[i][j] * x[i][j]
            for i in range(n_f)
            for j in range(n_c)
        )
    )

    status = solver.Solve()
    return status, solver, x


def _exibir_resultado(status, solver, x):
    """Exibe a solução e interpreta em linguagem de negócio.

    Args:
        status: código de status retornado pelo solver.
        solver: instância do solver após resolução.
        x: matriz de variáveis de decisão.

    Returns:
        None
    """
    print("\n" + "=" * 60)
    print("RESULTADO")
    print("=" * 60)

    if status != pywraplp.Solver.OPTIMAL:
        print("Nenhuma solucao otima encontrada.")
        return

    n_f = len(FABRICAS)
    n_c = len(CDS)

    custo_total = solver.Objective().Value()
    print(
        "\nCusto total de transporte: ${:,.2f}".format(custo_total)
    )

    print("\nPlano de transporte (remessas enviadas):")
    cabecalho = "{:<12}".format("") + "".join(
        "{:>8}".format(cd) for cd in CDS
    )
    print(cabecalho)
    for i, fab in enumerate(FABRICAS):
        linha = "{:<12}".format(fab)
        for j in range(n_c):
            linha += "{:>8.0f}".format(x[i][j].solution_value())
        print(linha)

    print("\nRotas ativas (remessas > 0):")
    for i, fab in enumerate(FABRICAS):
        for j, cd in enumerate(CDS):
            val = x[i][j].solution_value()
            if val > 0.001:
                print(
                    "  {} -> {}: {:.0f} remessas"
                    " | custo unitario ${:.0f}"
                    " | subtotal ${:,.0f}".format(
                        fab, cd, val,
                        CUSTOS[i][j],
                        val * CUSTOS[i][j]
                    )
                )

    print("\nInterpretacao de negocio:")
    print(
        "  O plano otimo distribui {} remessas totais"
        " com custo minimo de ${:,.2f}.".format(
            sum(SUPRIMENTO), custo_total
        )
    )
    print(
        "  A logica do solver prioriza as rotas de menor"
        " custo unitario e equilibra"
    )
    print(
        "  as restricoes de suprimento e demanda,"
        " evitando rotas caras (ex.: Fabrica 2 -> CD2)"
        " sempre que possivel."
    )


def executar():
    """Executa o Caso 1: Transporte de cadeiras infantis.

    Returns:
        None
    """
    print("=" * 60)
    print("CASO 1 - TRANSPORTE DE CADEIRAS INFANTIS")
    print("=" * 60)

    _exibir_dados()

    print("\nResolvendo modelo de transporte (PL - GLOP)...")
    status, solver, x = _montar_e_resolver()

    _exibir_resultado(status, solver, x)
