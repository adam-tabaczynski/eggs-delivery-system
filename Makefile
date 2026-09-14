.PHONY: psql
psql:
	docker compose exec db psql -U eggs -d doorstep_eggs
