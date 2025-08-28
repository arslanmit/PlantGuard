#!/bin/bash
# PlantGuard Command Aliases for Backward Compatibility
# This script provides helpful redirects for deprecated desktop commands

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

show_migration_message() {
    local old_cmd="$1"
    local new_cmd="$2"
    local description="$3"
    
    echo -e "${RED}❌ Command Deprecated: ${old_cmd}${NC}"
    echo -e "${YELLOW}📱 PlantGuard is now mobile-only${NC}"
    echo -e "${CYAN}📋 Migration: ${old_cmd} → ${new_cmd}${NC}"
    echo -e "${CYAN}✨ ${description}${NC}"
    echo -e "${GREEN}🚀 Running new command: ${new_cmd}${NC}"
    echo ""
}

# Deprecated command handlers
plantguard_run() {
    show_migration_message "make run" "make mobile" "All desktop functionality available in mobile interface"
    make mobile
}

plantguard_spa() {
    show_migration_message "make spa" "make mobile" "Desktop SPA replaced with mobile-first interface"
    make mobile
}

plantguard_spa_dev() {
    show_migration_message "make spa-dev" "make mobile-dev" "Mobile development mode with hot reload"
    make mobile-dev
}

plantguard_spa_test() {
    show_migration_message "make spa-test" "make mobile-test" "Mobile-specific testing suite"
    make mobile-test
}

plantguard_app() {
    show_migration_message "make app" "make mobile" "Legacy multi-page app replaced with unified mobile interface"
    make mobile
}

plantguard_desktop() {
    show_migration_message "make desktop" "make mobile" "Desktop interface replaced with mobile-first design"
    make mobile
}

# Export functions for use in other scripts
export -f plantguard_run
export -f plantguard_spa
export -f plantguard_spa_dev
export -f plantguard_spa_test
export -f plantguard_app
export -f plantguard_desktop

# If script is run directly, show help
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    echo -e "${CYAN}PlantGuard Command Aliases${NC}"
    echo -e "${YELLOW}Provides backward compatibility for deprecated desktop commands${NC}"
    echo ""
    echo -e "${BLUE}Available aliases:${NC}"
    echo "  plantguard_run      - Redirects 'make run' to 'make mobile'"
    echo "  plantguard_spa      - Redirects 'make spa' to 'make mobile'"
    echo "  plantguard_spa_dev  - Redirects 'make spa-dev' to 'make mobile-dev'"
    echo "  plantguard_spa_test - Redirects 'make spa-test' to 'make mobile-test'"
    echo "  plantguard_app      - Redirects 'make app' to 'make mobile'"
    echo "  plantguard_desktop  - Redirects 'make desktop' to 'make mobile'"
    echo ""
    echo -e "${CYAN}Usage:${NC}"
    echo "  source scripts/command_aliases.sh"
    echo "  plantguard_run  # Shows migration message and runs 'make mobile'"
    echo ""
    echo -e "${YELLOW}📚 For complete migration guide: cat MOBILE_MIGRATION_GUIDE.md${NC}"
fi