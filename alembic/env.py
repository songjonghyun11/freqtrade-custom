# alembic/env.py

import sys
import os
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context

# 프로젝트 루트를 파이썬 import 경로에 추가
sys.path.insert(0, os.getcwd())

# Alembic 설정 로드
config = context.config
fileConfig(config.config_file_name)

# 나중에 모델 MetaData를 여기에 연결할 수 있음
target_metadata = None

def run_migrations_offline():
    url = config.get_main_option("sqlalchemy.url")
    context.configure(url=url, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
