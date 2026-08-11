@echo off
echo Starting AuraBiz Tenant App on port 3004...
set TENANT_MODE=true
set PORT=3004
set NEXT_PUBLIC_API_URL=http://localhost:8000
set NEXT_PUBLIC_MASTER_URL=http://localhost:8010
cd /d "%~dp0"
npx next dev -p 3004
