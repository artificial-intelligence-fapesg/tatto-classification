"""
Camada de acesso ao banco de dados de tatuadores (SQLite).

A chave de ligação com o modelo é a coluna `classe`, que deve ser
exatamente igual ao nome usado na lista CLASSES do classificador.
"""

import sqlite3
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

DB_PATH = Path(__file__).parent / "data" / "tatuadores.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS tatuadores (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    classe          TEXT    NOT NULL UNIQUE,   -- rótulo retornado pelo modelo
    nome            TEXT    NOT NULL,
    apelido         TEXT,                      -- nome artístico
    bio             TEXT,
    especialidades  TEXT,                      -- ex: "blackwork, fineline"

    -- Localização
    estudio         TEXT,
    endereco        TEXT,
    bairro          TEXT,
    cidade          TEXT,
    estado          TEXT,
    cep             TEXT,
    latitude        REAL,
    longitude       REAL,

    -- Contato
    telefone        TEXT,
    whatsapp        TEXT,
    email           TEXT,

    -- Redes sociais
    instagram       TEXT,
    tiktok          TEXT,
    facebook        TEXT,
    site            TEXT,

    -- Extras
    horario         TEXT,
    preco_medio     TEXT,
    foto_url        TEXT,
    ativo           INTEGER DEFAULT 1
);

CREATE INDEX IF NOT EXISTS idx_tatuadores_classe ON tatuadores(classe);
"""


@dataclass
class Tatuador:
    classe: str
    nome: str
    apelido: Optional[str] = None
    bio: Optional[str] = None
    especialidades: Optional[str] = None
    estudio: Optional[str] = None
    endereco: Optional[str] = None
    bairro: Optional[str] = None
    cidade: Optional[str] = None
    estado: Optional[str] = None
    cep: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    telefone: Optional[str] = None
    whatsapp: Optional[str] = None
    email: Optional[str] = None
    instagram: Optional[str] = None
    tiktok: Optional[str] = None
    facebook: Optional[str] = None
    site: Optional[str] = None
    horario: Optional[str] = None
    preco_medio: Optional[str] = None
    foto_url: Optional[str] = None
    ativo: int = 1
    id: Optional[int] = field(default=None)

    @property
    def endereco_completo(self) -> str:
        partes = [self.endereco, self.bairro, self.cidade, self.estado, self.cep]
        return ", ".join(p for p in partes if p)

    @property
    def tem_coordenadas(self) -> bool:
        return self.latitude is not None and self.longitude is not None


def conectar() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def criar_schema() -> None:
    with conectar() as conn:
        conn.executescript(SCHEMA)


def _row_para_tatuador(row: sqlite3.Row) -> Tatuador:
    dados = dict(row)
    return Tatuador(**dados)


def salvar(tatuador: Tatuador) -> None:
    """Insere ou atualiza pelo campo `classe` (UPSERT)."""
    campos = {k: v for k, v in tatuador.__dict__.items() if k != "id"}
    colunas = ", ".join(campos)
    placeholders = ", ".join(f":{c}" for c in campos)
    updates = ", ".join(f"{c}=excluded.{c}" for c in campos if c != "classe")

    sql = (
        f"INSERT INTO tatuadores ({colunas}) VALUES ({placeholders}) "
        f"ON CONFLICT(classe) DO UPDATE SET {updates}"
    )
    with conectar() as conn:
        conn.execute(sql, campos)


def buscar_por_classe(classe: str) -> Optional[Tatuador]:
    with conectar() as conn:
        row = conn.execute(
            "SELECT * FROM tatuadores WHERE classe = ? AND ativo = 1", (classe,)
        ).fetchone()
    return _row_para_tatuador(row) if row else None


def listar_todos() -> list[Tatuador]:
    with conectar() as conn:
        rows = conn.execute(
            "SELECT * FROM tatuadores WHERE ativo = 1 ORDER BY nome"
        ).fetchall()
    return [_row_para_tatuador(r) for r in rows]
