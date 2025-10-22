"""
Script para criar manualmente as tabelas que não foram criadas pela migration.
"""

import os
import django
import sqlite3

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.db import connection

def create_missing_tables():
    """Cria as tabelas que estão faltando no banco de dados."""
    
    with connection.cursor() as cursor:
        # Criar tabela ConfiguracaoSistema
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS escalator_configuracaosistema (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chave VARCHAR(100) UNIQUE NOT NULL,
                valor VARCHAR(200) NOT NULL,
                descricao TEXT,
                created_at DATETIME NOT NULL,
                updated_at DATETIME NOT NULL
            )
        """)
        
        # Criar tabela Contrato
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS escalator_contrato (
                id CHAR(32) PRIMARY KEY,
                funcionario_id CHAR(32) NOT NULL,
                carga_diaria_max INTEGER NOT NULL,
                carga_semanal_max INTEGER NOT NULL,
                extra_diaria_cap INTEGER NOT NULL,
                banco_horas_prazo_meses INTEGER NOT NULL,
                permite_12x36 BOOLEAN NOT NULL,
                vigencia_inicio DATE NOT NULL,
                vigencia_fim DATE,
                created_at DATETIME NOT NULL,
                updated_at DATETIME NOT NULL,
                FOREIGN KEY (funcionario_id) REFERENCES escalator_funcionario (id)
            )
        """)
        
        # Criar tabela Ponto
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS escalator_ponto (
                id CHAR(32) PRIMARY KEY,
                funcionario_id CHAR(32) NOT NULL,
                escala_id CHAR(32),
                timestamp DATETIME NOT NULL,
                tipo_registro VARCHAR(20) NOT NULL,
                localizacao_lat REAL,
                localizacao_lng REAL,
                validado BOOLEAN NOT NULL,
                observacoes TEXT,
                created_at DATETIME NOT NULL,
                FOREIGN KEY (funcionario_id) REFERENCES escalator_funcionario (id),
                FOREIGN KEY (escala_id) REFERENCES escalator_escala (id)
            )
        """)
        
        # Criar tabela BancoHoras
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS escalator_bancohoras (
                id CHAR(32) PRIMARY KEY,
                funcionario_id CHAR(32) NOT NULL,
                data_referencia DATE NOT NULL,
                credito_minutos INTEGER NOT NULL,
                debito_minutos INTEGER NOT NULL,
                saldo_minutos INTEGER NOT NULL,
                data_vencimento DATE,
                compensado BOOLEAN NOT NULL,
                observacoes TEXT,
                created_at DATETIME NOT NULL,
                updated_at DATETIME NOT NULL,
                FOREIGN KEY (funcionario_id) REFERENCES escalator_funcionario (id),
                UNIQUE (funcionario_id, data_referencia)
            )
        """)
        
        # Adicionar campos que podem estar faltando na tabela Escala
        try:
            cursor.execute("ALTER TABLE escalator_escala ADD COLUMN hora_inicio TIME")
        except:
            pass
            
        try:
            cursor.execute("ALTER TABLE escalator_escala ADD COLUMN hora_fim TIME")
        except:
            pass
            
        try:
            cursor.execute("ALTER TABLE escalator_escala ADD COLUMN pausa_minutos INTEGER DEFAULT 60")
        except:
            pass
            
        try:
            cursor.execute("ALTER TABLE escalator_escala ADD COLUMN tipo_escala VARCHAR(20) DEFAULT 'normal'")
        except:
            pass
            
        try:
            cursor.execute("ALTER TABLE escalator_escala ADD COLUMN descanso BOOLEAN DEFAULT 0")
        except:
            pass
            
        try:
            cursor.execute("ALTER TABLE escalator_escala ADD COLUMN created_at DATETIME")
        except:
            pass
        
        # Adicionar campos que podem estar faltando na tabela Funcionario
        try:
            cursor.execute("ALTER TABLE escalator_funcionario ADD COLUMN usuario_id INTEGER")
        except:
            pass
            
        try:
            cursor.execute("ALTER TABLE escalator_funcionario ADD COLUMN created_at DATETIME")
        except:
            pass
        
        print("Tabelas criadas/atualizadas com sucesso!")

if __name__ == '__main__':
    create_missing_tables()