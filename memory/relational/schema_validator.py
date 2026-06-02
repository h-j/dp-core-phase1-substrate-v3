"""Schema validation for structured theory persistence.

Verifies that the canonical structured theory storage is correctly configured.
Runs at startup and raises if schema is invalid.
"""

import json
from sqlalchemy import inspect, text
from sqlalchemy.exc import OperationalError


class SchemaValidator:
    """Validates PostgreSQL schema for structured theory persistence."""

    def __init__(self, engine):
        """
        Args:
            engine: SQLAlchemy engine
        """
        self.engine = engine

    def validate_startup(self):
        """
        Comprehensive schema validation at startup.
        
        Raises:
            RuntimeError: If any validation fails
        """
        print("\n" + "=" * 70)
        print("SCHEMA VALIDATION: Structured Theory Persistence")
        print("=" * 70)
        
        try:
            # Check 1: PostgreSQL connection
            self._check_postgres_connection()
            
            # Check 2: All required analytics tables exist
            required_tables = [
                'theories', 
                'transition_pressure_events', 
                'prediction_probes', 
                'prediction_results', 
                'market_outcomes'
            ]
            for table_name in required_tables:
                self._check_table_exists(table_name)
            
            # Check 3: summary_structured column exists
            self._check_summary_structured_column()
            
            # Check 4: Verify theory_structures table does NOT exist (dead schema)
            self._check_theory_structures_removed()
            
            print("\n✓ SCHEMA VALIDATION PASSED")
            print(f"✓ Canonical Storage: theories.summary_structured (JSON text)")
            print("=" * 70 + "\n")
            
        except RuntimeError as e:
            print("\n" + "!" * 70)
            print("✗ SCHEMA VALIDATION FAILED")
            print("!" * 70)
            print(f"\nError: {e}\n")
            raise

    def _check_postgres_connection(self):
        """Verify PostgreSQL is running and accessible."""
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text("SELECT version();"))
                version = result.scalar()
                db_version = version.split(" ")[1]  # Extract version number
                print(f"✓ PostgreSQL Connection Active (v{db_version})")
        except OperationalError as e:
            raise RuntimeError(
                f"PostgreSQL connection failed: {e}\n"
                "Ensure PostgreSQL is running and settings are correct."
            )
        except Exception as e:
            raise RuntimeError(f"PostgreSQL connection check failed: {e}")

    def _check_table_exists(self, table_name: str):
        """Verify a specific table exists."""
        try:
            inspector = inspect(self.engine)
            tables = inspector.get_table_names()
            
            if table_name not in tables:
                raise RuntimeError(
                    f"Table '{table_name}' not found in database.\n"
                    "Run Base.metadata.create_all(engine) to initialize schema."
                )
        except Exception as e:
            raise RuntimeError(f"Failed to check table '{table_name}': {e}")

    def _check_summary_structured_column(self):
        """Verify summary_structured column exists on theories table."""
        try:
            inspector = inspect(self.engine)
            columns = inspector.get_columns('theories')
            column_names = [c['name'] for c in columns]
            
            if 'summary_structured' not in column_names:
                raise RuntimeError(
                    "summary_structured column not found on theories table.\n"
                    f"Available columns: {', '.join(column_names)}\n"
                    "Run: ALTER TABLE theories ADD COLUMN summary_structured TEXT;"
                )
            
            # Check column type
            col_type = next(c['type'] for c in columns if c['name'] == 'summary_structured')
            print(f"✓ theories.summary_structured column exists (type: {col_type})")
            
        except RuntimeError:
            raise
        except Exception as e:
            raise RuntimeError(f"Failed to check summary_structured column: {e}")

    def _check_theory_structures_removed(self):
        """
        Verify theory_structures table does NOT exist (dead schema).
        
        This is an anti-pattern check - warns if dead schema still exists.
        """
        try:
            inspector = inspect(self.engine)
            tables = inspector.get_table_names()
            
            if 'theory_structures' in tables:
                print("⚠ WARNING: theory_structures table still exists (deprecated)")
                print("  This table is no longer used. Consider dropping it:")
                print("  DROP TABLE theory_structures;")
            else:
                print("✓ theory_structures table correctly removed (dead schema)")
                
        except Exception as e:
            # Don't fail on this check - just log
            print(f"⚠ Could not check theory_structures table: {e}")


def validate_schema_startup(engine):
    """Convenience function for schema validation at startup."""
    validator = SchemaValidator(engine)
    validator.validate_startup()
