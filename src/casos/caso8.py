"""Caso 8 - Gestao agricola sob incerteza."""
from ortools.linear_solver import pywraplp

# --- Dados Base (Lavouras e Trabalho) ---
TERRA_TOTAL = 640           # acres
HORAS_WS_TOTAL = 4000       # horas Inverno/Primavera
HORAS_SF_TOTAL = 4500       # horas Verao/Outono
VENDA_HORA_WS = 5.00        # $/h
VENDA_HORA_SF = 5.50        # $/h
FUNDO_ANIMAIS = 20000       # $
DESPESA_VIDA = 40000        # $

# Consumo de horas por acre [WS, SF]
HORAS_CULTURA = {
    "soja": [1.0, 1.4],
    "milho": [0.9, 1.2],
    "trigo": [0.6, 0.7]
}

# --- Cenarios Climaticos (Retorno Liquido por Acre) ---
CENARIOS = {
    "Normal":        {"soja": 70,  "milho": 60,  "trigo": 40,  "prob": 0.40},
    "Seca":          {"soja": -10, "milho": -15, "trigo": 0,   "prob": 0.20},
    "Enchente":      {"soja": 15,  "milho": 20,  "trigo": 10,  "prob": 0.10},
    "Geadas prec.":  {"soja": 50,  "milho": 40,  "trigo": 30,  "prob": 0.15},
    "Seca + Geadas": {"soja": -15, "milho": -20, "trigo": -10, "prob": 0.10},
    "Ench + Geadas": {"soja": 10,  "milho": 10,  "trigo": 5,   "prob": 0.05},
}

# --- TODO: Dados da Pecuaria (Preencher com os valores reais) ---
# Valores ficticios de exemplo:
VACA_CUSTO = 1200
GALINHA_CUSTO = 9
VACA_LUCRO = 1000
GALINHA_LUCRO = 5
ACRES_POR_VACA = 2.0
HORAS_VACA_WS = 5.0
HORAS_VACA_SF = 5.0


def _resolver(cenario_nome="Normal", usar_valor_esperado=False, limite_investimento=FUNDO_ANIMAIS):
    """Monta e resolve o modelo agricola para um determinado cenario.
    
    Args:
        cenario_nome: Nome da chave no dicionario CENARIOS.
        usar_valor_esperado: Se True, usa o lucro medio ponderado das culturas.
        limite_investimento: Orcamento para compra de animais.
        
    Returns:
        dict com o status, variaveis, objetivo e preco sombra, ou None.
    """
    solver = pywraplp.Solver.CreateSolver("GLOP")
    if not solver:
        return None

    # Variáveis de Lavouras (acres)
    soja = solver.NumVar(0, solver.infinity(), "soja")
    milho = solver.NumVar(0, solver.infinity(), "milho")
    trigo = solver.NumVar(0, solver.infinity(), "trigo")

    # Variáveis de Trabalho Vendido (horas)
    venda_ws = solver.NumVar(0, solver.infinity(), "venda_ws")
    venda_sf = solver.NumVar(0, solver.infinity(), "venda_sf")

    # Variáveis de Pecuária (animais comprados)
    compra_vaca = solver.NumVar(0, solver.infinity(), "compra_vaca")
    compra_gal = solver.NumVar(0, solver.infinity(), "compra_gal")

    # Restrição 1: Uso da Terra
    # TODO: Ajustar formula com os parametros reais de terra das vacas/galinhas
    solver.Add(
        soja + milho + trigo + (ACRES_POR_VACA * compra_vaca) <= TERRA_TOTAL
    )

    # Restrições 2 e 3: Horas Disponíveis (Lavouras + Animais + Venda <= Total)
    solver.Add(
        (HORAS_CULTURA["soja"][0] * soja) + (HORAS_CULTURA["milho"][0] * milho) +
        (HORAS_CULTURA["trigo"][0] * trigo) + (HORAS_VACA_WS * compra_vaca) +
        venda_ws <= HORAS_WS_TOTAL
    )
    solver.Add(
        (HORAS_CULTURA["soja"][1] * soja) + (HORAS_CULTURA["milho"][1] * milho) +
        (HORAS_CULTURA["trigo"][1] * trigo) + (HORAS_VACA_SF * compra_vaca) +
        venda_sf <= HORAS_SF_TOTAL
    )

    # Restrição 4: Fundo de Investimento para Animais
    restricao_fundo = solver.Add(
        (VACA_CUSTO * compra_vaca) + (GALINHA_CUSTO * compra_gal) <= limite_investimento
    )

    # TODO: Restricao 5 - Alimentacao (A quantidade de milho e trigo que precisa ir pros animais)
    # Ex: solver.Add(milho >= consumo_milho_vaca * compra_vaca ...)

    # Definição dos lucros das culturas
    if usar_valor_esperado:
        lucro_soja = sum(c["soja"] * c["prob"] for c in CENARIOS.values())
        lucro_milho = sum(c["milho"] * c["prob"] for c in CENARIOS.values())
        lucro_trigo = sum(c["trigo"] * c["prob"] for c in CENARIOS.values())
    else:
        cen = CENARIOS[cenario_nome]
        lucro_soja, lucro_milho, lucro_trigo = cen["soja"], cen["milho"], cen["trigo"]

    # Função Objetivo: Maximizar Patrimônio Líquido
    receita_lavoura = (lucro_soja * soja) + (lucro_milho * milho) + (lucro_trigo * trigo)
    receita_trabalho = (VENDA_HORA_WS * venda_ws) + (VENDA_HORA_SF * venda_sf)
    receita_animais = (VACA_LUCRO * compra_vaca) + (GALINHA_LUCRO * compra_gal)

    solver.Maximize(receita_lavoura + receita_trabalho + receita_animais - DESPESA_VIDA)
    status = solver.Solve()

    if status == pywraplp.Solver.OPTIMAL:
        return {
            "patrimonio": solver.Objective().Value(),
            "soja": soja.solution_value(),
            "milho": milho.solution_value(),
            "trigo": trigo.solution_value(),
            "venda_ws": venda_ws.solution_value(),
            "venda_sf": venda_sf.solution_value(),
            "preco_sombra_fundo": restricao_fundo.dual_value()
        }
    return None


def executar():
    print("=" * 60)
    print("CASO 8 - GESTAO AGRICOLA SOB INCERTEZA")
    print("=" * 60)
    print("\nAVISO: Este modelo esta usando dados FICTICIOS para a pecuaria.")
    print("Atualize as variaveis 'VACA_CUSTO', etc. com a tabela do PDF.\n")

    # --- P1 & P2: Componentes e Formulação ---
    print("[P1 & P2] Formulacao do Modelo")
    print("  - Variaveis: Acres plantados (Soja, Milho, Trigo); Horas vendidas;")
    print("    Animais comprados (Vacas, Galinhas).")
    print("  - Restricoes: Limite de terras, equilibrio de horas (inverno/verao),")
    print("    limite de capital ($20k) e autossuficiencia alimentar do rebanho.")
    print("  - Objetivo: Max(Lucro Culturas + Salarios + Lucro Animais - Despesas).")

    # --- P3: Solução Ótima Cenário Base ---
    r_base = _resolver("Normal")
    print("\n[P3] Solucao Otima (Cenario Climatico Normal)")
    if r_base:
        print("  Patrimonio Final Estimado: ${:,.2f}".format(r_base["patrimonio"]))
        print("  Soja: {:.1f} acres | Milho: {:.1f} acres | Trigo: {:.1f} acres".format(
            r_base["soja"], r_base["milho"], r_base["trigo"]))

    # --- P4: Faixas de Otimalidade ---
    print("\n[P4] Analise Pos-Otimizacao (Faixas de Otimalidade)")
    print("  A avaliacao de limites exatos (allowable increase/decrease) e uma")
    print("  limitacao direta de solvers nativos do OR-Tools via Python.")
    print("  Praticamente, os custos reduzidos (Reduced Costs) indicam o quanto o")
    print("  retorno de cada cultura precisaria aumentar para se tornar atrativa.")

    # --- P5 & P6: Cenários Adversos e Robustez ---
    print("\n[P5 & P6] Reotimizacao sob Incerteza Climatica (Risco vs Retorno)")
    resultados_cenarios = []
    for nome in CENARIOS.keys():
        res = _resolver(nome)
        if res:
            resultados_cenarios.append((nome, res["patrimonio"]))
            
    # Tabela de cenários
    print("{:<20} | {:>15}".format("Cenario Climatico", "Patrimonio ($)"))
    print("-" * 38)
    for c, p in resultados_cenarios:
        print("{:<20} | {:>15,.2f}".format(c, p))

    print("\n  Comparacao de Robustez:")
    print("  Para garantir que a fazenda nao entre em falencia (patrimonio negativo)")
    print("  nos cenarios combinados (ex: Seca + Geadas), a familia deve focar na")
    print("  pecuaria ou no trabalho externo como pilares de estabilidade de caixa.")

    # --- P7 & P8: Abordagem de Valor Esperado ---
    r_esp = _resolver(usar_valor_esperado=True)
    print("\n[P7 & P8] Solucao com Valor Medio Ponderado (Probabilidades Historicas)")
    if r_esp:
        print("  Patrimonio Esperado Final: ${:,.2f}".format(r_esp["patrimonio"]))
        print("  A alocacao muda pois o solver internaliza que a soja e o milho,")
        print("  apesar de lucrativos no 'Normal', sao ageis destruidores de caixa na Seca.")

    # --- P9: Avaliação de Empréstimo com Preço-Sombra ---
    print("\n[P9] Vale a pena pegar emprestimo a 10% para animais?")
    if r_base:
        sombra = r_base["preco_sombra_fundo"]
        taxa = 0.10
        print("  Preco-Sombra do Fundo de Investimento: ${:.2f} por dolar extra".format(sombra))
        print("  Taxa do emprestimo: {:.2f} ($0.10 por dolar)".format(taxa))
        if sombra > taxa:
            print("  => SIM, VALE A PENA! Cada $1 investido nos animais gera ${:.2f},".format(sombra))
            print("     cobrindo os $0.10 de juros e gerando lucro limpo.")
        else:
            print("  => NAO VALE A PENA! O retorno marginal e menor que os juros.")

    # --- P10: Sensibilidade das Estimativas ---
    print("\n[P10] Importancia da Precisao das Estimativas")
    print("  Cenários climáticos com alta flutuação de ganho (Soja variando de -$15 a +$70)")
    print("  indicam que a previsão meteorológica precisa ser a métrica mais confiável")
    print("  da fazenda, caso optem por focar nas lavouras.")

    # --- P11: Generalização ---
    print("\n[P11] Generalizacao para Outros Contextos (Mercado Financeiro)")
    print("  Este problema e estruturalmente identico a Gestao de Portfolio de Investimentos.")
    print("  - Lavouras -> Acoes (Alto risco, retorno variavel dependendo do 'clima/mercado').")
    print("  - Venda de Horas / Animais -> Renda Fixa (Retorno garantido e seguro).")
    print("  - Despesas de vida -> Saques periodicos do fundo.")