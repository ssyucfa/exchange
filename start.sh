#!/bin/bash
export CONFIGPATH='/exchange_api/config.yml'
alembic revision -m "game_models migration" --autogenerate --head head
alembic upgrade head
python3 main.py