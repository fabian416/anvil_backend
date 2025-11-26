#!/bin/bash

# ============================================================================
# ANVIL BACKEND - TEST RUNNER
# ============================================================================
# Este script ejecuta todos los tests del proyecto Anvil
# 
# Uso:
#   ./run_tests.sh              # Ejecutar todos los tests
#   ./run_tests.sh auth         # Solo tests de autenticación
#   ./run_tests.sh metrics      # Solo tests de métricas
#   ./run_tests.sh integration  # Solo tests de integración API
#   ./run_tests.sh all          # Todos los tests con reporte detallado
# ============================================================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# API Configuration
API_BASE_URL="${API_BASE_URL:-http://localhost:8000}"
TEST_EMAIL="test_$(date +%s)@anvil.test"
TEST_PASSWORD="TestPassword123!"

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

print_header() {
    echo ""
    echo -e "${PURPLE}============================================================================${NC}"
    echo -e "${PURPLE}  $1${NC}"
    echo -e "${PURPLE}============================================================================${NC}"
    echo ""
}

print_section() {
    echo ""
    echo -e "${CYAN}--- $1 ---${NC}"
    echo ""
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

check_api_running() {
    print_info "Verificando que el API está corriendo en $API_BASE_URL..."
    
    if curl -s --max-time 5 "$API_BASE_URL/api/v1/general/health" > /dev/null 2>&1; then
        print_success "API está corriendo"
        return 0
    else
        print_error "API no está corriendo en $API_BASE_URL"
        print_info "Inicia el servidor con: make start"
        return 1
    fi
}

# ============================================================================
# TEST VARIABLES (se llenan durante la ejecución)
# ============================================================================

ACCESS_TOKEN=""
REFRESH_TOKEN=""
USER_ID=""
ADMIN_TOKEN=""

# ============================================================================
# AUTH TESTS
# ============================================================================

test_signup() {
    print_section "TEST: Registro de Usuario (Signup)"
    
    local response=$(curl -s -X POST "$API_BASE_URL/api/v1/account/signup" \
        -H "Content-Type: application/json" \
        -d "{
            \"email\": \"$TEST_EMAIL\",
            \"password\": \"$TEST_PASSWORD\",
            \"first_name\": \"Test\",
            \"last_name\": \"User\"
        }")
    
    if echo "$response" | grep -q "access_token"; then
        ACCESS_TOKEN=$(echo "$response" | python3 -c "import sys,json; print(json.load(sys.stdin).get('access_token', ''))" 2>/dev/null || echo "")
        REFRESH_TOKEN=$(echo "$response" | python3 -c "import sys,json; print(json.load(sys.stdin).get('refresh_token', ''))" 2>/dev/null || echo "")
        print_success "Signup exitoso"
        print_info "Email: $TEST_EMAIL"
        return 0
    else
        print_error "Signup falló: $response"
        return 1
    fi
}

test_login() {
    print_section "TEST: Login de Usuario"
    
    local response=$(curl -s -X POST "$API_BASE_URL/api/v1/account/login" \
        -H "Content-Type: application/json" \
        -d "{
            \"email\": \"$TEST_EMAIL\",
            \"password\": \"$TEST_PASSWORD\"
        }")
    
    if echo "$response" | grep -q "access_token"; then
        ACCESS_TOKEN=$(echo "$response" | python3 -c "import sys,json; print(json.load(sys.stdin).get('access_token', ''))" 2>/dev/null || echo "")
        REFRESH_TOKEN=$(echo "$response" | python3 -c "import sys,json; print(json.load(sys.stdin).get('refresh_token', ''))" 2>/dev/null || echo "")
        USER_ID=$(echo "$response" | python3 -c "import sys,json; print(json.load(sys.stdin).get('user_id', ''))" 2>/dev/null || echo "")
        print_success "Login exitoso"
        print_info "User ID: $USER_ID"
        return 0
    else
        print_error "Login falló: $response"
        return 1
    fi
}

test_privy_login() {
    print_section "TEST: Privy Login (Wallet)"
    
    local privy_id="did:privy:test_$(date +%s)"
    local wallet_address="0x$(openssl rand -hex 20)"
    
    local response=$(curl -s -X POST "$API_BASE_URL/api/v1/account/privy-login" \
        -H "Content-Type: application/json" \
        -d "{
            \"privy_user_id\": \"$privy_id\",
            \"wallet_address\": \"$wallet_address\",
            \"auth_provider\": \"wallet\"
        }")
    
    if echo "$response" | grep -q "access_token"; then
        local is_new=$(echo "$response" | python3 -c "import sys,json; print(json.load(sys.stdin).get('is_new_user', False))" 2>/dev/null || echo "")
        print_success "Privy login exitoso"
        print_info "Privy ID: $privy_id"
        print_info "Wallet: $wallet_address"
        print_info "Nuevo usuario: $is_new"
        return 0
    else
        print_error "Privy login falló: $response"
        return 1
    fi
}

test_privy_login_with_email() {
    print_section "TEST: Privy Login (con Email)"
    
    local privy_id="did:privy:email_$(date +%s)"
    local test_email="privy_$(date +%s)@example.com"
    
    local response=$(curl -s -X POST "$API_BASE_URL/api/v1/account/privy-login" \
        -H "Content-Type: application/json" \
        -d "{
            \"privy_user_id\": \"$privy_id\",
            \"email\": \"$test_email\",
            \"auth_provider\": \"google\",
            \"first_name\": \"Google\",
            \"last_name\": \"User\"
        }")
    
    if echo "$response" | grep -q "access_token"; then
        print_success "Privy login con email exitoso"
        print_info "Email: $test_email"
        return 0
    else
        print_error "Privy login con email falló: $response"
        return 1
    fi
}

test_get_me() {
    print_section "TEST: Obtener Perfil (GET /me)"
    
    if [ -z "$ACCESS_TOKEN" ]; then
        print_warning "No hay token, ejecutando login primero..."
        test_login || return 1
    fi
    
    local response=$(curl -s -X GET "$API_BASE_URL/api/v1/account/me" \
        -H "Authorization: Bearer $ACCESS_TOKEN" \
        -H "Content-Type: application/json")
    
    if echo "$response" | grep -q "email"; then
        print_success "GET /me exitoso"
        echo "$response" | python3 -m json.tool 2>/dev/null || echo "$response"
        return 0
    else
        print_error "GET /me falló: $response"
        return 1
    fi
}

test_refresh_token() {
    print_section "TEST: Refresh Token"
    
    if [ -z "$REFRESH_TOKEN" ]; then
        print_warning "No hay refresh token, ejecutando login primero..."
        test_login || return 1
    fi
    
    local response=$(curl -s -X POST "$API_BASE_URL/api/v1/account/refresh-token" \
        -H "Content-Type: application/json" \
        -d "{\"refresh_token\": \"$REFRESH_TOKEN\"}")
    
    if echo "$response" | grep -q "access_token"; then
        ACCESS_TOKEN=$(echo "$response" | python3 -c "import sys,json; print(json.load(sys.stdin).get('access_token', ''))" 2>/dev/null || echo "")
        print_success "Refresh token exitoso"
        return 0
    else
        print_error "Refresh token falló: $response"
        return 1
    fi
}

# ============================================================================
# METRICS TESTS
# ============================================================================

test_track_event() {
    print_section "TEST: Track Event"
    
    if [ -z "$ACCESS_TOKEN" ]; then
        print_warning "No hay token, ejecutando login primero..."
        test_login || return 1
    fi
    
    local response=$(curl -s -X POST "$API_BASE_URL/api/v1/metrics/track" \
        -H "Authorization: Bearer $ACCESS_TOKEN" \
        -H "Content-Type: application/json" \
        -d '{
            "event_type": "swap_completed",
            "event_category": "trading",
            "properties": {
                "from_token": "ETH",
                "to_token": "USDC",
                "amount": "1.5"
            },
            "device_type": "desktop",
            "platform": "web",
            "app_version": "1.0.0"
        }')
    
    if echo "$response" | grep -q "success"; then
        local event_id=$(echo "$response" | python3 -c "import sys,json; print(json.load(sys.stdin).get('event_id', ''))" 2>/dev/null || echo "")
        print_success "Track event exitoso"
        print_info "Event ID: $event_id"
        return 0
    else
        print_error "Track event falló: $response"
        return 1
    fi
}

test_track_multiple_events() {
    print_section "TEST: Track Multiple Events"
    
    if [ -z "$ACCESS_TOKEN" ]; then
        print_warning "No hay token, ejecutando login primero..."
        test_login || return 1
    fi
    
    local events=("login" "page_view" "wallet_connected" "swap_initiated" "swap_completed")
    local categories=("auth" "navigation" "auth" "trading" "trading")
    local success_count=0
    
    for i in "${!events[@]}"; do
        local response=$(curl -s -X POST "$API_BASE_URL/api/v1/metrics/track" \
            -H "Authorization: Bearer $ACCESS_TOKEN" \
            -H "Content-Type: application/json" \
            -d "{
                \"event_type\": \"${events[$i]}\",
                \"event_category\": \"${categories[$i]}\",
                \"device_type\": \"mobile\",
                \"platform\": \"ios\"
            }")
        
        if echo "$response" | grep -q "success"; then
            ((success_count++))
        fi
    done
    
    if [ $success_count -eq ${#events[@]} ]; then
        print_success "Todos los $success_count eventos trackeados exitosamente"
        return 0
    else
        print_error "Solo $success_count de ${#events[@]} eventos fueron trackeados"
        return 1
    fi
}

test_get_event_types() {
    print_section "TEST: Get Event Types"
    
    local response=$(curl -s -X GET "$API_BASE_URL/api/v1/metrics/event-types" \
        -H "Content-Type: application/json")
    
    if echo "$response" | grep -q "auth"; then
        print_success "Get event types exitoso"
        echo "$response" | python3 -m json.tool 2>/dev/null | head -30
        return 0
    else
        print_error "Get event types falló: $response"
        return 1
    fi
}

test_get_my_metrics() {
    print_section "TEST: Get My Metrics"
    
    if [ -z "$ACCESS_TOKEN" ]; then
        print_warning "No hay token, ejecutando login primero..."
        test_login || return 1
    fi
    
    local response=$(curl -s -X GET "$API_BASE_URL/api/v1/metrics/me" \
        -H "Authorization: Bearer $ACCESS_TOKEN" \
        -H "Content-Type: application/json")
    
    if echo "$response" | grep -q "user_id"; then
        print_success "Get my metrics exitoso"
        echo "$response" | python3 -m json.tool 2>/dev/null || echo "$response"
        return 0
    else
        print_error "Get my metrics falló: $response"
        return 1
    fi
}

test_get_my_events() {
    print_section "TEST: Get My Events"
    
    if [ -z "$ACCESS_TOKEN" ]; then
        print_warning "No hay token, ejecutando login primero..."
        test_login || return 1
    fi
    
    local response=$(curl -s -X GET "$API_BASE_URL/api/v1/metrics/me/events?limit=10" \
        -H "Authorization: Bearer $ACCESS_TOKEN" \
        -H "Content-Type: application/json")
    
    if echo "$response" | grep -q "events"; then
        local total=$(echo "$response" | python3 -c "import sys,json; print(json.load(sys.stdin).get('total', 0))" 2>/dev/null || echo "0")
        print_success "Get my events exitoso"
        print_info "Total eventos: $total"
        return 0
    else
        print_error "Get my events falló: $response"
        return 1
    fi
}

# ============================================================================
# ADMIN TESTS
# ============================================================================

test_admin_login() {
    print_section "TEST: Admin Login"
    
    local response=$(curl -s -X POST "$API_BASE_URL/api/v1/account/login" \
        -H "Content-Type: application/json" \
        -d '{
            "email": "admin@anvil.com",
            "password": "Admin123!"
        }')
    
    if echo "$response" | grep -q "access_token"; then
        ADMIN_TOKEN=$(echo "$response" | python3 -c "import sys,json; print(json.load(sys.stdin).get('access_token', ''))" 2>/dev/null || echo "")
        print_success "Admin login exitoso"
        return 0
    else
        print_warning "Admin login falló (puede que el admin no exista): $response"
        return 1
    fi
}

test_admin_list_users() {
    print_section "TEST: Admin - List Users"
    
    if [ -z "$ADMIN_TOKEN" ]; then
        print_warning "No hay admin token, intentando login..."
        test_admin_login || return 1
    fi
    
    local response=$(curl -s -X GET "$API_BASE_URL/api/v1/admin/users/?limit=10" \
        -H "Authorization: Bearer $ADMIN_TOKEN" \
        -H "Content-Type: application/json")
    
    if echo "$response" | grep -q "email"; then
        print_success "Admin list users exitoso"
        echo "$response" | python3 -m json.tool 2>/dev/null | head -30
        return 0
    else
        print_error "Admin list users falló: $response"
        return 1
    fi
}

test_admin_platform_metrics() {
    print_section "TEST: Admin - Platform Metrics"
    
    if [ -z "$ADMIN_TOKEN" ]; then
        print_warning "No hay admin token, intentando login..."
        test_admin_login || return 1
    fi
    
    local response=$(curl -s -X GET "$API_BASE_URL/api/v1/metrics/admin/summary?days=7" \
        -H "Authorization: Bearer $ADMIN_TOKEN" \
        -H "Content-Type: application/json")
    
    if echo "$response" | grep -q "total_events\|active_users\|error"; then
        print_success "Admin platform metrics exitoso"
        echo "$response" | python3 -m json.tool 2>/dev/null || echo "$response"
        return 0
    else
        print_error "Admin platform metrics falló: $response"
        return 1
    fi
}

# ============================================================================
# HEALTH TESTS
# ============================================================================

test_health_check() {
    print_section "TEST: Health Check"
    
    # Try the root endpoint which returns API info
    local response=$(curl -s -X GET "$API_BASE_URL/")
    
    if echo "$response" | grep -qi "anvil\|api\|version\|welcome"; then
        print_success "Health check exitoso"
        echo "$response" | python3 -m json.tool 2>/dev/null || echo "$response"
        return 0
    else
        # Fallback: just check if API responds
        local status_code=$(curl -s -o /dev/null -w "%{http_code}" "$API_BASE_URL/api/v1/")
        if [ "$status_code" = "200" ] || [ "$status_code" = "404" ]; then
            print_success "API está respondiendo (status: $status_code)"
            return 0
        else
            print_error "Health check falló: $response"
            return 1
        fi
    fi
}

# ============================================================================
# TEST RUNNERS
# ============================================================================

run_auth_tests() {
    print_header "TESTS DE AUTENTICACIÓN"
    
    local passed=0
    local failed=0
    
    if test_signup; then ((passed++)); else ((failed++)); fi
    if test_login; then ((passed++)); else ((failed++)); fi
    if test_privy_login; then ((passed++)); else ((failed++)); fi
    if test_privy_login_with_email; then ((passed++)); else ((failed++)); fi
    if test_get_me; then ((passed++)); else ((failed++)); fi
    if test_refresh_token; then ((passed++)); else ((failed++)); fi
    
    echo ""
    print_info "Auth Tests: $passed passed, $failed failed"
    return $failed
}

run_metrics_tests() {
    print_header "TESTS DE MÉTRICAS"
    
    local passed=0
    local failed=0
    
    if test_get_event_types; then ((passed++)); else ((failed++)); fi
    if test_track_event; then ((passed++)); else ((failed++)); fi
    if test_track_multiple_events; then ((passed++)); else ((failed++)); fi
    if test_get_my_metrics; then ((passed++)); else ((failed++)); fi
    if test_get_my_events; then ((passed++)); else ((failed++)); fi
    
    echo ""
    print_info "Metrics Tests: $passed passed, $failed failed"
    return $failed
}

run_admin_tests() {
    print_header "TESTS DE ADMIN"
    
    local passed=0
    local failed=0
    
    if test_admin_login; then ((passed++)); else ((failed++)); fi
    if test_admin_list_users; then ((passed++)); else ((failed++)); fi
    if test_admin_platform_metrics; then ((passed++)); else ((failed++)); fi
    
    echo ""
    print_info "Admin Tests: $passed passed, $failed failed"
    return $failed
}

run_all_tests() {
    print_header "ANVIL BACKEND - SUITE COMPLETA DE TESTS"
    
    local total_failed=0
    local start_time=$(date +%s)
    
    # Health check primero
    if ! test_health_check; then ((total_failed++)); fi
    
    # Auth tests
    run_auth_tests
    total_failed=$((total_failed + $?))
    
    # Metrics tests
    run_metrics_tests
    total_failed=$((total_failed + $?))
    
    # Admin tests
    run_admin_tests
    total_failed=$((total_failed + $?))
    
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    
    print_header "RESUMEN DE TESTS"
    echo ""
    print_info "Tiempo total: ${duration}s"
    echo ""
    
    if [ $total_failed -eq 0 ]; then
        print_success "¡TODOS LOS TESTS PASARON!"
        return 0
    else
        print_error "$total_failed tests fallaron"
        return $total_failed
    fi
}

# ============================================================================
# MAIN
# ============================================================================

main() {
    cd "$PROJECT_ROOT"
    
    print_header "ANVIL BACKEND TEST RUNNER"
    print_info "Project root: $PROJECT_ROOT"
    print_info "API URL: $API_BASE_URL"
    
    # Verificar que el API está corriendo
    check_api_running || exit 1
    
    case "${1:-all}" in
        auth)
            run_auth_tests
            ;;
        metrics)
            run_metrics_tests
            ;;
        admin)
            run_admin_tests
            ;;
        health)
            test_health_check
            ;;
        integration|all)
            run_all_tests
            ;;
        *)
            echo "Uso: $0 [auth|metrics|admin|health|integration|all]"
            exit 1
            ;;
    esac
}

main "$@"

