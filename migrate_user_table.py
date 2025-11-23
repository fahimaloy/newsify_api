#!/usr/bin/env python3
"""
Script to migrate the user table to add missing columns.
This will preserve existing data while adding new fields.
Usage: uv run python migrate_user_table.py
"""
from sqlmodel import Session, text
from cj36.dependencies import engine

def migrate_user_table():
    """Add missing columns to the user table."""
    print("=" * 60)
    print("Migrating User Table Schema")
    print("=" * 60)
    print()
    
    migrations = [
        # Add email column if it doesn't exist
        """
        DO $$ 
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                          WHERE table_name='user' AND column_name='email') THEN
                ALTER TABLE "user" ADD COLUMN email VARCHAR;
                CREATE INDEX IF NOT EXISTS ix_user_email ON "user"(email);
            END IF;
        END $$;
        """,
        
        # Add phone column if it doesn't exist
        """
        DO $$ 
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                          WHERE table_name='user' AND column_name='phone') THEN
                ALTER TABLE "user" ADD COLUMN phone VARCHAR;
            END IF;
        END $$;
        """,
        
        # Add full_name column if it doesn't exist
        """
        DO $$ 
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                          WHERE table_name='user' AND column_name='full_name') THEN
                ALTER TABLE "user" ADD COLUMN full_name VARCHAR;
            END IF;
        END $$;
        """,
        
        # Add user_type column if it doesn't exist
        """
        DO $$ 
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                          WHERE table_name='user' AND column_name='user_type') THEN
                ALTER TABLE "user" ADD COLUMN user_type VARCHAR DEFAULT 'subscriber';
            END IF;
        END $$;
        """,
        
        # Add admin_type column if it doesn't exist
        """
        DO $$ 
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                          WHERE table_name='user' AND column_name='admin_type') THEN
                ALTER TABLE "user" ADD COLUMN admin_type VARCHAR;
            END IF;
        END $$;
        """,
        
        # Add newsletter_subscribed column if it doesn't exist
        """
        DO $$ 
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                          WHERE table_name='user' AND column_name='newsletter_subscribed') THEN
                ALTER TABLE "user" ADD COLUMN newsletter_subscribed BOOLEAN DEFAULT FALSE;
            END IF;
        END $$;
        """,
        
        # Add is_verified column if it doesn't exist
        """
        DO $$ 
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                          WHERE table_name='user' AND column_name='is_verified') THEN
                ALTER TABLE "user" ADD COLUMN is_verified BOOLEAN DEFAULT FALSE;
            END IF;
        END $$;
        """,
        
        # Add is_blocked column if it doesn't exist
        """
        DO $$ 
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                          WHERE table_name='user' AND column_name='is_blocked') THEN
                ALTER TABLE "user" ADD COLUMN is_blocked BOOLEAN DEFAULT FALSE;
            END IF;
        END $$;
        """,
        
        # Add verification_code column if it doesn't exist
        """
        DO $$ 
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                          WHERE table_name='user' AND column_name='verification_code') THEN
                ALTER TABLE "user" ADD COLUMN verification_code VARCHAR;
            END IF;
        END $$;
        """,
    ]
    
    try:
        with Session(engine) as session:
            print("🔄 Applying migrations...")
            print()
            
            for i, migration in enumerate(migrations, 1):
                try:
                    session.exec(text(migration))
                    session.commit()
                    print(f"✅ Migration {i}/{len(migrations)} completed")
                except Exception as e:
                    print(f"⚠️  Migration {i}/{len(migrations)} skipped or failed: {e}")
                    session.rollback()
            
            print()
            print("=" * 60)
            print("✅ Migration completed!")
            print("=" * 60)
            print()
            
            # Show current table structure
            print("Current user table structure:")
            result = session.exec(text("""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns
                WHERE table_name = 'user'
                ORDER BY ordinal_position;
            """))
            
            print()
            print(f"{'Column':<25} {'Type':<20} {'Nullable':<10} {'Default':<20}")
            print("-" * 80)
            for row in result:
                col_name, data_type, nullable, default = row
                default_str = str(default)[:20] if default else ""
                print(f"{col_name:<25} {data_type:<20} {nullable:<10} {default_str:<20}")
            
            print()
            print("=" * 60)
            print("You can now run 'uv run python create_admin.py'")
            print("=" * 60)
            
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    migrate_user_table()
