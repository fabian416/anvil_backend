#!/bin/bash
set -e

echo "🔄 Reset Database y Generar Migración Inicial"
echo "=============================================="

# Colores
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 1. Limpiar base de datos local (como superuser postgres)
echo -e "\n${BLUE}📦 Paso 1: Limpiando base de datos local...${NC}"
echo -e "${YELLOW}Se necesita la contraseña del usuario postgres${NC}"
sudo -u postgres psql -d anvil_db << EOF
DROP SCHEMA public CASCADE;
CREATE SCHEMA public;
GRANT ALL ON SCHEMA public TO anvil;
GRANT ALL ON SCHEMA public TO public;
EOF

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Base de datos limpiada${NC}"
else
    echo -e "${YELLOW}⚠️  Error al limpiar la base de datos${NC}"
    exit 1
fi

# 2. Limpiar tabla alembic_version si existe (como superuser postgres)
echo -e "\n${BLUE}📦 Paso 2: Limpiando versiones de Alembic...${NC}"
sudo -u postgres psql -d anvil_db -c "DROP TABLE IF EXISTS alembic_version CASCADE;" 2>/dev/null || true
echo -e "${GREEN}✅ Versiones de Alembic limpiadas${NC}"

# 3. Crear directorio de versiones si no existe
echo -e "\n${BLUE}📦 Paso 3: Preparando directorio de migraciones...${NC}"
mkdir -p src/app/infrastructure/persistence_sqla/alembic/versions
echo -e "${GREEN}✅ Directorio preparado${NC}"

# 4. Generar nueva migración con autogenerate
echo -e "\n${BLUE}📦 Paso 4: Generando migración inicial con autogenerate...${NC}"
source env/bin/activate
alembic revision --autogenerate -m "initial_schema"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Migración generada exitosamente${NC}"
else
    echo -e "${YELLOW}⚠️  Error al generar la migración${NC}"
    exit 1
fi

# 5. Mostrar el archivo generado
echo -e "\n${BLUE}📄 Migración generada:${NC}"
MIGRATION_FILE=$(ls -t src/app/infrastructure/persistence_sqla/alembic/versions/*.py | head -1)
echo -e "${GREEN}$MIGRATION_FILE${NC}"

# 6. Verificar que NO tiene DROP TABLE
echo -e "\n${BLUE}🔍 Verificando que NO tenga DROP TABLE...${NC}"
if grep -q "op.drop_table" "$MIGRATION_FILE"; then
    echo -e "${YELLOW}⚠️  ADVERTENCIA: La migración contiene DROP TABLE${NC}"
    echo -e "${YELLOW}Esto indica que tu DB local tenía tablas. Verifica el contenido.${NC}"
    grep -n "op.drop_table" "$MIGRATION_FILE" | head -5
else
    echo -e "${GREEN}✅ Perfecto! La migración solo tiene CREATE TABLE${NC}"
fi

# 7. Contar operaciones CREATE TABLE
CREATE_COUNT=$(grep -c "op.create_table" "$MIGRATION_FILE" || echo "0")
echo -e "\n${BLUE}📊 Estadísticas:${NC}"
echo -e "  - ${GREEN}CREATE TABLE: $CREATE_COUNT${NC}"

# 8. Aplicar migración localmente para testear
echo -e "\n${BLUE}📦 Paso 5: Aplicando migración localmente...${NC}"
alembic upgrade head

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Migración aplicada exitosamente en local${NC}"
else
    echo -e "${YELLOW}⚠️  Error al aplicar la migración${NC}"
    exit 1
fi

# 9. Verificar que las tablas se crearon
echo -e "\n${BLUE}🔍 Verificando tablas creadas...${NC}"
TABLE_COUNT=$(PGPASSWORD=changethis psql -h localhost -U anvil -d anvil_db -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';" | xargs)
echo -e "${GREEN}✅ Tablas creadas: $TABLE_COUNT${NC}"

# 10. Verificar versión de Alembic
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
echo -e "3. Push a staging y verifica el deployment"
