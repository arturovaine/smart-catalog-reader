#!/bin/bash
# Script para processar todos os catálogos PDF em lote
# Uso: ./scripts/process_all_catalogs.sh [--resume]

set -e

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Diretórios
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
CATALOGS_DIR="$PROJECT_DIR/data/catalogs"
OUTPUT_DIR="$PROJECT_DIR/data/output"

# Flag de resume
RESUME_FLAG=""
if [[ "$1" == "--resume" ]]; then
    RESUME_FLAG="--resume"
    echo -e "${YELLOW}Modo resume ativado - tentará retomar extrações incompletas${NC}"
fi

# Função para extrair ciclo do nome do arquivo
get_cycle() {
    local filename="$1"
    echo "$filename" | grep -oE 'c[0-9]+' | sed 's/c/Ciclo /'
}

# Função para verificar se já foi processado
is_processed() {
    local pdf_name="$1"
    local base_name=$(basename "$pdf_name" .pdf)
    # Verifica se existe algum JSON com esse nome base
    if ls "$OUTPUT_DIR"/*"$base_name"* 2>/dev/null | grep -q ".json"; then
        return 0
    fi
    return 1
}

# Catálogos do Boticário
BOTICARIO_CATALOGS=(
    "boticario-c01.pdf"
    "boticario-c02.pdf"
    "boticario-c04.pdf"
    "boticario-c05.pdf"
    "boticario-c06.pdf"
    "boticario-c07.pdf"
    "boticario-c08.pdf"
    "boticario-c09.pdf"
    "boticario-c10.pdf"
    "boticario-c11.pdf"
    "boticario-c12.pdf"
    "boticario-c13.pdf"
    "boticario-c14.pdf"
    "boticario-c15.pdf"
    "boticario-c16.pdf"
    "boticario-c17.pdf"
)

# Catálogos da Natura
NATURA_CATALOGS=(
    "natura-c04.pdf"
    "natura-c05.pdf"
    "natura-c06.pdf"
    "natura-c07.pdf"
    "natura-c08.pdf"
    "natura-c09.pdf"
    "natura-c10.pdf"
    "natura-c12.pdf"
    "natura-c13.pdf"
    "natura-c14.pdf"
    "natura-c15.pdf"
    "natura-c16.pdf"
    "natura-c17.pdf"
    "natura-c18.pdf"
    "natura-c19.pdf"
)

# Contadores
TOTAL_CATALOGS=$((${#BOTICARIO_CATALOGS[@]} + ${#NATURA_CATALOGS[@]}))
PROCESSED=0
SKIPPED=0
FAILED=0

echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}       Smart Catalog Reader - Processamento em Lote         ${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "Total de catálogos a processar: ${YELLOW}$TOTAL_CATALOGS${NC}"
echo -e "Diretório de catálogos: $CATALOGS_DIR"
echo -e "Diretório de output: $OUTPUT_DIR"
echo ""

# Ativar ambiente virtual
cd "$PROJECT_DIR"
source .venv/bin/activate

# Processar Boticário
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}  Processando catálogos O Boticário (${#BOTICARIO_CATALOGS[@]} catálogos)${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

for catalog in "${BOTICARIO_CATALOGS[@]}"; do
    PDF_PATH="$CATALOGS_DIR/$catalog"
    CYCLE=$(get_cycle "$catalog")

    if [[ ! -f "$PDF_PATH" ]]; then
        echo -e "${YELLOW}[SKIP]${NC} $catalog - Arquivo não encontrado"
        ((SKIPPED++))
        continue
    fi

    # Verificar se já foi processado (apenas se não estiver em modo resume)
    if [[ -z "$RESUME_FLAG" ]] && is_processed "$catalog"; then
        echo -e "${YELLOW}[SKIP]${NC} $catalog - Já processado"
        ((SKIPPED++))
        continue
    fi

    echo ""
    echo -e "${BLUE}[$(($PROCESSED + $SKIPPED + $FAILED + 1))/$TOTAL_CATALOGS]${NC} Processando: $catalog"
    echo -e "  Nome: O Boticário - $CYCLE"

    if catalog-extractor extract "$PDF_PATH" \
        --name "O Boticário - $CYCLE" \
        --brand "O Boticário" \
        $RESUME_FLAG; then
        echo -e "${GREEN}[OK]${NC} $catalog processado com sucesso"
        ((PROCESSED++))
    else
        echo -e "${RED}[ERRO]${NC} Falha ao processar $catalog"
        ((FAILED++))
    fi

    # Pequena pausa entre catálogos para evitar rate limiting
    sleep 5
done

# Processar Natura
echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}  Processando catálogos Natura (${#NATURA_CATALOGS[@]} catálogos)${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

for catalog in "${NATURA_CATALOGS[@]}"; do
    PDF_PATH="$CATALOGS_DIR/$catalog"
    CYCLE=$(get_cycle "$catalog")

    if [[ ! -f "$PDF_PATH" ]]; then
        echo -e "${YELLOW}[SKIP]${NC} $catalog - Arquivo não encontrado"
        ((SKIPPED++))
        continue
    fi

    # Verificar se já foi processado (apenas se não estiver em modo resume)
    if [[ -z "$RESUME_FLAG" ]] && is_processed "$catalog"; then
        echo -e "${YELLOW}[SKIP]${NC} $catalog - Já processado"
        ((SKIPPED++))
        continue
    fi

    echo ""
    echo -e "${BLUE}[$(($PROCESSED + $SKIPPED + $FAILED + 1))/$TOTAL_CATALOGS]${NC} Processando: $catalog"
    echo -e "  Nome: Natura - $CYCLE"

    if catalog-extractor extract "$PDF_PATH" \
        --name "Natura - $CYCLE" \
        --brand "Natura" \
        $RESUME_FLAG; then
        echo -e "${GREEN}[OK]${NC} $catalog processado com sucesso"
        ((PROCESSED++))
    else
        echo -e "${RED}[ERRO]${NC} Falha ao processar $catalog"
        ((FAILED++))
    fi

    # Pequena pausa entre catálogos para evitar rate limiting
    sleep 5
done

# Resumo final
echo ""
echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}                    RESUMO FINAL                            ${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
echo -e "  Processados com sucesso: ${GREEN}$PROCESSED${NC}"
echo -e "  Ignorados (já existem): ${YELLOW}$SKIPPED${NC}"
echo -e "  Falhas:                  ${RED}$FAILED${NC}"
echo ""
echo -e "Arquivos de output em: $OUTPUT_DIR"
echo ""

# Listar arquivos gerados
echo -e "${BLUE}Arquivos JSON gerados:${NC}"
ls -lh "$OUTPUT_DIR"/*.json 2>/dev/null | tail -20

exit $FAILED
