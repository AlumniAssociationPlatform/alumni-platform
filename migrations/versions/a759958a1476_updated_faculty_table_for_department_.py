"""Updated faculty table for department column

Revision ID: a759958a1476
Revises: 9211388e38d5
Create Date: 2026-01-18 16:03:08.813726

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = 'a759958a1476'
down_revision = '9211388e38d5'
branch_labels = None
depends_on = None


def upgrade():
    # First, convert existing data from 'Computer Engineering' format to 'COMPUTER_ENGINEERING' format
    connection = op.get_bind()
    
    # Create mapping for data conversion
    mapping = {
        'Computer Engineering': 'COMPUTER_ENGINEERING',
        'IT Engineering': 'IT_ENGINEERING',
        'Electrical Engineering': 'ELECTRICAL_ENGINEERING',
        'Civil Engineering': 'CIVIL_ENGINEERING',
        'Mechanical Engineering': 'MECHANICAL_ENGINEERING',
    }
    
    # Convert each value in the faculty table
    for old_value, new_value in mapping.items():
        connection.execute(
            sa.text(f"UPDATE faculty SET department = '{new_value}' WHERE department = '{old_value}'")
        )
    
    # Now alter the column to use the ENUM type with the new values
    with op.batch_alter_table('faculty', schema=None) as batch_op:
        batch_op.alter_column('department',
               existing_type=mysql.VARCHAR(length=100),
               type_=sa.Enum('COMPUTER_ENGINEERING', 'IT_ENGINEERING', 'ELECTRICAL_ENGINEERING', 'CIVIL_ENGINEERING', 'MECHANICAL_ENGINEERING', name='department'),
               existing_nullable=False)


def downgrade():
    # First, convert data back from 'COMPUTER_ENGINEERING' format to 'Computer Engineering' format
    connection = op.get_bind()
    
    # Create reverse mapping for data conversion
    reverse_mapping = {
        'COMPUTER_ENGINEERING': 'Computer Engineering',
        'IT_ENGINEERING': 'IT Engineering',
        'ELECTRICAL_ENGINEERING': 'Electrical Engineering',
        'CIVIL_ENGINEERING': 'Civil Engineering',
        'MECHANICAL_ENGINEERING': 'Mechanical Engineering',
    }
    
    # Convert each value back in the faculty table
    for old_value, new_value in reverse_mapping.items():
        connection.execute(
            sa.text(f"UPDATE faculty SET department = '{new_value}' WHERE department = '{old_value}'")
        )
    
    # Revert the column type back to VARCHAR
    with op.batch_alter_table('faculty', schema=None) as batch_op:
        batch_op.alter_column('department',
               existing_type=sa.Enum('COMPUTER_ENGINEERING', 'IT_ENGINEERING', 'ELECTRICAL_ENGINEERING', 'CIVIL_ENGINEERING', 'MECHANICAL_ENGINEERING', name='department'),
               type_=mysql.VARCHAR(length=100),
               existing_nullable=False)
