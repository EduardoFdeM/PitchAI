"""
Módulo de dados - Gerenciamento de banco de dados e DAOs
======================================================

Este módulo contém:
- DatabaseManager: Gerenciador do banco SQLite
- DAOMentor: DAO para operações de mentoring
- DAODisc: DAO para operações DISC
- Migrações SQL
"""

from .database import DatabaseManager
from .dao_mentor import DAOMentor
from .dao_disc import DAODisc

__all__ = ['DatabaseManager', 'DAOMentor', 'DAODisc'] 