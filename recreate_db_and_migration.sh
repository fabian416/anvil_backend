#!/bin/bash
set -e

echo "🔄 Recreando base de datos y generando migración inicial"
echo "========================================================"

# Colores
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 1. Dropear y recrear la base de datos
echo -e "\n${BLUE}📦 Paso 1: Dropeando y recreando base de datos...${NC}"
PGPASSWORD=changethis psql -h localhost -U anvil -d postgres << EOF
DROP DATABASE IF EXISTS anvil_db;
CREATE DATABASE anvil_db OWNER anvil;
EOF

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Base de datos recreada${NC}"
else
    echo -e "${YELLOW}⚠️  Error al recrear la base de datos${NC}"
    exit 1
fi

# 2. Eliminar migraciones existentes
echo -e "\n${BLUE}📦 Paso 2: Limpiando migraciones anteriores...${NC}"
rm -f src/app/infrastructure/persistence_sqla/alembic/versions/*.py
echo -e "${GREEN}✅ Migraciones anteriores eliminadas${NC}"

# 3. Generar nueva migración con autogenerate
echo -e "\n${BLUE}📦 Paso 3: Generando migración inicial...${NC}"
source env/bin/activate
alembic revision --autogenerate -m "initial_schema"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Migración generada exitosamente${NC}"
else
    echo -e "${YELLOW}⚠️  Error al generar la migración${NC}"
    exit 1
fi

# 4. Mostrar el archivo generado
echo -e "\n${BLUE}📄 Migración generada:${NC}"
MIGRATION_FILE=$(ls -t src/app/infrastructure/persistence_sqla/alembic/versions/*.py | head -1)
echo -e "${GREEN}$MIGRATION_FILE${NC}"

# 5. Verificar que NO tiene DROP TABLE
echo -e "\n${BLUE}🔍 Verificando que NO tenga DROP TABLE...${NC}"
DROP_COUNT=$(grep -c "op.drop_table" "$MIGRATION_FILE" || echo "0")
if [ "$DROP_COUNT" -gt 0 ]; then
    echo -e "${YELLOW}⚠️  ADVERTENCIA: La migración contiene $DROP_COUNT DROP TABLE${NC}"
    grep -n "op.drop_table" "$MIGRATION_FILE" | head -5
else
    echo -e "${GREEN}✅ Perfecto! La migración NO tiene DROP TABLE${NC}"
fi

# 6. Contar operaciones CREATE TABLE
CREATE_COUNT=$(grep -c "op.create_table" "$MIGRATION_FILE" || echo "0")
echo -e "\n${BLUE}📊 Estadísticas:${NC}"
echo -e "  - ${GREEN}CREATE TABLE: $CREATE_COUNT${NC}"
echo -e "  - ${GREEN}DROP TABLE: $DROP_COUNT${NC}"

if [ "$CREATE_COUNT" -eq 0 ]; then
    echo -e "\n${YELLOW}⚠️  ERROR: La migración está vacía (0 CREATE TABLE)${NC}"
    echo -e "${YELLOW}Esto indica que hay un problema con la detección de tablas${NC}"
    exit 1
fi

# 7. Aplicar migración localmente para testear
echo -e "\n${BLUE}📦 Paso 4: Aplicando migración localmente...${NC}"
alembic upgrade head

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Migración aplicada exitosamente en local${NC}"
else
    echo -e "${YELLOW}⚠️  Error al aplicar la migración${NC}"
    exit 1
fi

# 8. Verificar que las tablas se crearon
echo -e "\n${BLUE}🔍 Verificando tablas creadas...${NC}"
TABLE_COUNT=$(PGPASSWORD=changethis psql -h localhost -U anvil -d anvil_db -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public' AND table_type = 'BASE TABLE';" | xargs)
echo -e "${GREEN}✅ Tablas creadas: $TABLE_COUNT${NC}"

# 9. Verificar versión de Alembic
echo -e "\n${BLUE}🔍 Verificando versión de Alembic...${NC}"
ALEMBIC_VERSION=$(PGPASSWORD=changethis psql -h localhost -U anvil -d anvil_db -t -c "SELECT version_num FROM alembic_version;" | xargs)
echo -e "${GREEN}✅ Versión actual: $ALEMBIC_VERSION${NC}"

echo -e "\n${GREEN}=============================================="
echo -e "✅ PROCESO COMPLETADO EXITOSAMENTE"
echo -e "=============================================="
echo -e "${NC}"
echo -e "Próximos pasos:"
echo -e "1. Revisa el archivo de migración generado"
echo -e "2. Haz commit: git add . && git commit -m 'feat(db): add initial schema migration'"
echo -e "3. Push a staging: git push origin staging"
