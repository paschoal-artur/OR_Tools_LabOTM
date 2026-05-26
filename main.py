import sys

from src.casos import (
    caso8,
)
from src.casos import caso1, caso2, caso3, caso4, caso5, caso6, caso7

MENU = """
========================================
  PROJETO OR-TOOLS - MENU PRINCIPAL
========================================
  1. Caso 1 - Transporte de cadeiras infantis
  2. Caso 2 - Planejamento de producao automotiva
  3. Caso 3 - Reducao de custos da cafeteria
  4. Caso 4 - Escala de operadores (call center)
  5. Caso 5 - Producao de moda feminina
  6. Caso 6 - Pesquisa de mercado (banco digital)
  7. Caso 7 - Alocacao de estudantes em escolas
  8. Caso 8 - Gestao agricola sob incerteza
  0. Sair
========================================"""

# Mapeia opção do menu para a função executar() do caso
CASOS = {
    "1": caso1.executar,
    "2": caso2.executar,
    "3": caso3.executar,
    "4": caso4.executar,
    "5": caso5.executar,
    "6": caso6.executar,
    "7": caso7.executar,
    "8": caso8.executar,
}

while True:
    print(MENU)
    opcao = input("Selecione um caso (0 para sair): ").strip()

    if opcao == "0":
        print("Encerrando. Ate logo!")
        sys.exit(0)

    if opcao not in CASOS:
        print("Opcao invalida. Tente novamente.")
        continue

    print()
    CASOS[opcao]()
    print()
    input("Pressione Enter para voltar ao menu...")