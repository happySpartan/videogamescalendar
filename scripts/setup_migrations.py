"""
Alembic Database Migration Setup
Initialize and manage database schema migrations for PostgreSQL
"""
import os
import sys
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from alembic.config import Config
from alembic import command
from alembic.script import ScriptDirectory
from alembic.runtime.environment import EnvironmentContext
from sqlalchemy import create_engine

from shared.database import get_database_url
from shared.models import Base

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_alembic_config():
    """Create Alembic configuration"""
    
    # Create alembic directory structure
    alembic_dir = project_root / "alembic"
    versions_dir = alembic_dir / "versions"
    
    alembic_dir.mkdir(exist_ok=True)
    versions_dir.mkdir(exist_ok=True)
    
    # Create alembic.ini
    alembic_ini_path = project_root / "alembic.ini"
    if not alembic_ini_path.exists():
        alembic_ini_content = f"""# A generic, single database configuration.

[alembic]
# path to migration scripts
script_location = alembic

# template used to generate migration files
file_template = %%(year)d%%(month).2d%%(day).2d_%%(hour).2d%%(minute).2d_%%(rev)s_%%(slug)s

# sys.path path, will be prepended to sys.path if present.
prepend_sys_path = .

# timezone to use when rendering the date within the migration file
# as well as the filename.
timezone = UTC

# max length of characters to apply to the "slug" field
truncate_slug_length = 40

# set to 'true' to run the environment during the 'revision' command, regardless
# of autogenerate
revision_environment = false

# set to 'true' to allow .pyc and .pyo files without
# a source .py file to be detected as revisions in the versions/ directory
sourceless = false

# version number format for new versions.
version_num_format = %%(year)d%%(month).2d%%(day).2d_%%(hour).2d%%(minute).2d

# version path separator; As of Alembic 1.10.0, this can now be any python string.
version_path_separator = os

# the output encoding used when revision files
# are written from script.py.mako
output_encoding = utf-8

sqlalchemy.url = {get_database_url()}

[post_write_hooks]
# post_write_hooks defines scripts or Python functions that are run
# on newly generated revision scripts.

# format using "black" - use the console_scripts runner, against the "black" entrypoint
# hooks = black
# black.type = console_scripts
# black.entrypoint = black
# black.options = -l 79 REVISION_SCRIPT_FILENAME

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console
qualname =

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %%(levelname)-5.5s [%%(name)s] %%(message)s
datefmt = %%H:%%M:%%S
"""
        with open(alembic_ini_path, 'w') as f:
            f.write(alembic_ini_content)
        
        logger.info(f"Created alembic.ini at {alembic_ini_path}")
    
    # Create env.py
    env_py_path = alembic_dir / "env.py"
    if not env_py_path.exists():
        env_py_content = """from logging.config import fileConfig
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context
import os
import sys

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from shared.models import Base
from shared.database import get_database_url

# this is the Alembic Config object
config = context.config

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Set the database URL from environment
config.set_main_option("sqlalchemy.url", get_database_url())

# add your model's MetaData object here for 'autogenerate' support
target_metadata = Base.metadata

def run_migrations_offline() -> None:
    \"\"\"Run migrations in 'offline' mode.\"\"\"
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    \"\"\"Run migrations in 'online' mode.\"\"\"
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
"""
        with open(env_py_path, 'w') as f:
            f.write(env_py_content)
        
        logger.info(f"Created env.py at {env_py_path}")
    
    # Create script.py.mako
    script_py_mako_path = alembic_dir / "script.py.mako"
    if not script_py_mako_path.exists():
        script_py_mako_content = '''"""${message}

Revision ID: ${up_revision}
Revises: ${down_revision | comma,n}
Create Date: ${create_date}

"""
from alembic import op
import sqlalchemy as sa
${imports if imports else ""}

# revision identifiers, used by Alembic.
revision = ${repr(up_revision)}
down_revision = ${repr(down_revision)}
branch_labels = ${repr(branch_labels)}
depends_on = ${repr(depends_on)}


def upgrade() -> None:
    ${upgrades if upgrades else "pass"}


def downgrade() -> None:
    ${downgrades if downgrades else "pass"}
'''
        with open(script_py_mako_path, 'w') as f:
            f.write(script_py_mako_content)
        
        logger.info(f"Created script.py.mako at {script_py_mako_path}")
    
    return str(alembic_ini_path)

def init_alembic():
    """Initialize Alembic for the project"""
    try:
        logger.info("Initializing Alembic configuration...")
        
        # Create configuration files
        alembic_ini_path = create_alembic_config()
        
        # Test database connection
        database_url = get_database_url()
        engine = create_engine(database_url)
        
        try:
            with engine.connect() as conn:
                logger.info("Database connection successful")
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            raise
        finally:
            engine.dispose()
        
        logger.info("Alembic initialization completed")
        return alembic_ini_path
        
    except Exception as e:
        logger.error(f"Alembic initialization failed: {e}")
        raise

def create_initial_migration():
    """Create initial migration with all models"""
    try:
        alembic_ini_path = project_root / "alembic.ini"
        
        if not alembic_ini_path.exists():
            logger.error("Alembic not initialized. Run init_alembic() first.")
            return
        
        # Create Alembic config
        alembic_cfg = Config(str(alembic_ini_path))
        
        # Create initial migration
        logger.info("Creating initial migration...")
        command.revision(
            alembic_cfg, 
            message="Initial migration with all models",
            autogenerate=True
        )
        
        logger.info("Initial migration created successfully")
        
    except Exception as e:
        logger.error(f"Failed to create initial migration: {e}")
        raise

def run_migrations():
    """Run all pending migrations"""
    try:
        alembic_ini_path = project_root / "alembic.ini"
        
        if not alembic_ini_path.exists():
            logger.error("Alembic not initialized. Run init_alembic() first.")
            return
        
        # Create Alembic config
        alembic_cfg = Config(str(alembic_ini_path))
        
        # Run migrations
        logger.info("Running database migrations...")
        command.upgrade(alembic_cfg, "head")
        
        logger.info("Migrations completed successfully")
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        raise

def create_migration(message: str):
    """Create a new migration"""
    try:
        alembic_ini_path = project_root / "alembic.ini"
        
        if not alembic_ini_path.exists():
            logger.error("Alembic not initialized. Run init_alembic() first.")
            return
        
        # Create Alembic config
        alembic_cfg = Config(str(alembic_ini_path))
        
        # Create migration
        logger.info(f"Creating migration: {message}")
        command.revision(
            alembic_cfg,
            message=message,
            autogenerate=True
        )
        
        logger.info(f"Migration '{message}' created successfully")
        
    except Exception as e:
        logger.error(f"Failed to create migration: {e}")
        raise

def show_migration_history():
    """Show migration history"""
    try:
        alembic_ini_path = project_root / "alembic.ini"
        
        if not alembic_ini_path.exists():
            logger.error("Alembic not initialized.")
            return
        
        # Create Alembic config
        alembic_cfg = Config(str(alembic_ini_path))
        
        # Show history
        logger.info("Migration history:")
        command.history(alembic_cfg)
        
    except Exception as e:
        logger.error(f"Failed to show migration history: {e}")
        raise

def main():
    """Main setup function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Database migration management')
    parser.add_argument('action', choices=['init', 'create-initial', 'migrate', 'create', 'history'],
                       help='Action to perform')
    parser.add_argument('--message', '-m', help='Migration message (for create action)')
    
    args = parser.parse_args()
    
    try:
        if args.action == 'init':
            init_alembic()
            logger.info("Alembic initialized. Next steps:")
            logger.info("1. Run 'python setup_migrations.py create-initial' to create initial migration")
            logger.info("2. Run 'python setup_migrations.py migrate' to apply migrations")
        
        elif args.action == 'create-initial':
            create_initial_migration()
        
        elif args.action == 'migrate':
            run_migrations()
        
        elif args.action == 'create':
            if not args.message:
                logger.error("Message required for create action. Use --message/-m")
                return
            create_migration(args.message)
        
        elif args.action == 'history':
            show_migration_history()
    
    except Exception as e:
        logger.error(f"Command failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()