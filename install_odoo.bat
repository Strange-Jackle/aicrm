@echo off
echo Starting Odoo installation in Docker...

echo Step 1: Running PostgreSQL container...
docker run -d -v odoo-db:/var/lib/postgresql/data -e POSTGRES_USER=odoo -e POSTGRES_PASSWORD=odoo -e POSTGRES_DB=postgres --name db postgres:15

echo Step 2: Running Odoo container...
docker run -v odoo-data:/var/lib/odoo -d -p 8069:8069 --name odoo --link db:db -t odoo

echo Step 3: Stopping and restarting Odoo...
docker stop odoo
docker start -a odoo

echo Installation complete! Odoo should be accessible at http://localhost:8069