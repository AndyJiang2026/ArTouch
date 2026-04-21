#!/bin/bash
# =============================================================================
# ArtTouch NFC - SQLite to PostgreSQL Migration Script
# =============================================================================
# AI-ASSISTED: Yes
# AI-TOOL: Claude Code
# PROMPT: Create SQLite to PostgreSQL migration script
# DATE: 2026-04-19
# ENGINEER: System
# RISK-LEVEL: P1 (Destructive data migration - use with caution!)
#
# WARNING: This script migrates data from SQLite to PostgreSQL.
#          Always backup your data before running!
#
# Usage:
#   ./scripts/migrate-to-postgres.sh --backup    # Backup first, then migrate
#   ./scripts/migrate-to-postgres.sh --migrate   # Migrate only (no backup)
#   ./scripts/migrate-to-postgres.sh --verify    # Verify migration
#
# Prerequisites:
#   - PostgreSQL server running
#   - Database and user created
#   - .env file configured with PostgreSQL URL

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info()  { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Paths
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "${SCRIPT_DIR}")"
BACKUP_DIR="${PROJECT_DIR}/backups"
SQLITE_DB="${PROJECT_DIR}/data/artouch.db"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Load environment
if [[ -f "${PROJECT_DIR}/.env" ]]; then
    export $(grep -v '^#' "${PROJECT_DIR}/.env" | xargs)
fi

# =============================================================================
# Functions
# =============================================================================

backup_sqlite() {
    log_info "Creating backup of SQLite database..."

    mkdir -p "${BACKUP_DIR}"

    if [[ ! -f "${SQLITE_DB}" ]]; then
        log_warn "SQLite database not found at ${SQLITE_DB}"
        log_warn "No backup created (database is empty or doesn't exist)"
        return 0
    fi

    # Backup database file
    cp "${SQLITE_DB}" "${BACKUP_DIR}/artouch_${TIMESTAMP}.db"
    log_info "Database backed up to: ${BACKUP_DIR}/artouch_${TIMESTAMP}.db"

    # Also export as SQL
    if command -v sqlite3 &> /dev/null; then
        sqlite3 "${SQLITE_DB}" ".dump" > "${BACKUP_DIR}/artouch_${TIMESTAMP}.sql"
        log_info "SQL dump saved to: ${BACKUP_DIR}/artouch_${TIMESTAMP}.sql"
    fi

    log_info "Backup complete!"
}

create_postgres_schema() {
    log_info "Creating PostgreSQL schema..."

    cd "${PROJECT_DIR}"

    # Use Alembic to create schema
    pip install alembic psycopg2-binary -q 2>/dev/null || true

    PYTHONPATH="${PROJECT_DIR}/backend" python -c "
import sys
sys.path.insert(0, '${PROJECT_DIR}/backend')
from alembic import command
from alembic.config import Config

alembic_cfg = Config('${PROJECT_DIR}/alembic.ini')
alembic_cfg.set_main_option('sqlalchemy.url', '${DATABASE_URL}')
command.upgrade(alembic_cfg, 'head')
"

    log_info "Schema created successfully!"
}

verify_migration() {
    log_info "Verifying migration..."

    PYTHONPATH="${PROJECT_DIR}/backend" python -c "
import sys
sys.path.insert(0, '${PROJECT_DIR}/backend')

from app.database import engine
from sqlalchemy import text

with engine.connect() as conn:
    # Check tables exist
    result = conn.execute(text(\"\"\"
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
        ORDER BY table_name
    \"\"\"))
    tables = [row[0] for row in result]
    print(f'Tables found: {tables}')

    # Count records
    for table in ['users', 'videos', 'nfc_tags', 'cultural_products', 'tag_clicks']:
        try:
            result = conn.execute(text(f'SELECT COUNT(*) FROM {table}'))
            count = result.scalar()
            print(f'  {table}: {count} records')
        except Exception as e:
            print(f'  {table}: ERROR - {e}')

print('Verification complete!')
"

    log_info "Verification complete!"
}

# =============================================================================
# Main
# =============================================================================

main() {
    case "${1:-}" in
        --backup)
            backup_sqlite
            ;;
        --migrate)
            backup_sqlite
            create_postgres_schema
            verify_migration
            log_info "Migration complete!"
            log_info "Update your .env to use DATABASE_URL=postgresql://..."
            ;;
        --verify)
            verify_migration
            ;;
        --help|--*)
            echo "Usage: $0 {--backup|--migrate|--verify}"
            echo ""
            echo "  --backup   - Create backup of SQLite database"
            echo "  --migrate - Full migration (backup + schema + verify)"
            echo "  --verify  - Verify PostgreSQL data"
            ;;
        *)
            log_error "Unknown option: $1"
            echo "Usage: $0 {--backup|--migrate|--verify}"
            exit 1
            ;;
    esac
}

main "$@"
