"""
Client Profile Service - Gerenciamento de perfis de clientes
==========================================================

Serviço para CRUD e agregações de dados de clientes.
"""

import json
import time
import logging
from typing import Dict, List, Any, Optional

from .scorer import complexity_score, infer_stage, extract_topics
from data.dao_mentor import DAOMentor


class ClientProfileService:
    """Serviço para gerenciamento de perfis de clientes."""
    
    def __init__(self, dao: DAOMentor, retriever=None):
        self.dao = dao
        self.retriever = retriever  # Opcional: embeddings playbook
        self.logger = logging.getLogger(__name__)
    
    def get_or_create(self, client_id: str, name: str) -> Dict[str, Any]:
        """
        Buscar cliente existente ou criar novo.
        
        Args:
            client_id: ID único do cliente
            name: Nome do cliente
            
        Returns:
            Dict com dados do cliente
        """
        client = self.dao.get_client(client_id)
        if not client:
            self.dao.create_client(client_id, name)
            client = self.dao.get_client(client_id)
            self.logger.info(f"✅ Cliente criado: {client_id} ({name})")
        else:
            self.logger.debug(f"📋 Cliente encontrado: {client_id}")
        
        return client
    
    def update_from_call(self, call_id: str, seller_id: str, client_id: str, 
                        summary_text: str, call_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """
        Atualizar perfil do cliente baseado nos dados da call.
        
        Args:
            call_id: ID da call
            seller_id: ID do vendedor
            client_id: ID do cliente
            summary_text: Texto do resumo da call
            call_metrics: Métricas da call (objeções, sentimento, etc.)
            
        Returns:
            Dict com dados atualizados do perfil
        """
        try:
            # 1. Calcular complexidade
            score, tier = complexity_score(call_metrics)
            
            # 2. Inferir stage
            stage = infer_stage(summary_text)
            
            # 3. Extrair tópicos
            topics = call_metrics.get("top_objections", [])
            if not topics and summary_text:
                topics = extract_topics(summary_text)
            
            topics_json = json.dumps(topics, ensure_ascii=False)
            
            # 4. Timestamp atual
            last_contact_at = int(time.time() * 1000)
            
            # 5. Persistir atualizações
            self.dao.update_client_profile(
                client_id, tier, stage, last_contact_at, score, topics_json
            )
            
            # 6. Vincular call ao cliente
            summary_json = json.dumps({"full_text": summary_text}, ensure_ascii=False)
            self.dao.link_call_to_client(client_id, call_id, stage, summary_json)
            
            self.logger.info(f"✅ Perfil atualizado: {client_id} -> {tier}/{stage} (score: {score:.2f})")
            
            return {
                "tier": tier,
                "stage": stage,
                "score": score,
                "topics": topics,
                "last_contact_at": last_contact_at
            }
            
        except Exception as e:
            self.logger.error(f"❌ Erro ao atualizar perfil: {e}")
            return {
                "tier": "desconhecido",
                "stage": "descoberta",
                "score": 0.0,
                "topics": [],
                "last_contact_at": int(time.time() * 1000)
            }
    
    def get_client_context(self, client_id: str) -> Dict[str, Any]:
        """
        Buscar contexto completo do cliente para UI.
        
        Args:
            client_id: ID do cliente
            
        Returns:
            Dict com contexto completo
        """
        client = self.dao.get_client(client_id)
        if not client:
            return {
                "client_id": client_id,
                "name": "Cliente Desconhecido",
                "tier": "desconhecido",
                "stage": "descoberta",
                "last_contact_at": None,
                "topics": [],
                "hints": []
            }
        
        # Gerar hints baseados no tier/stage
        hints = self._generate_hints(client.get("tier", "desconhecido"), 
                                   client.get("stage", "descoberta"))
        
        return {
            "client_id": client_id,
            "name": client.get("name", "Cliente"),
            "tier": client.get("tier", "desconhecido"),
            "stage": client.get("stage", "descoberta"),
            "last_contact_at": client.get("last_contact_at"),
            "topics": client.get("topics", []),
            "hints": hints
        }
    
    def _generate_hints(self, tier: str, stage: str) -> List[str]:
        """
        Gerar dicas baseadas no tier e stage do cliente.
        
        Args:
            tier: Tier do cliente
            stage: Stage atual
            
        Returns:
            Lista de dicas
        """
        hints = []
        
        # Hints por tier
        if tier == "dificil":
            hints.append("Cliente complexo - foco em autoridade e ROI")
            hints.append("Prepare-se para objeções múltiplas")
        elif tier == "medio":
            hints.append("Cliente intermediário - equilibre benefícios e preço")
        else:
            hints.append("Cliente fácil - mantenha o momentum")
        
        # Hints por stage
        if stage == "descoberta":
            hints.append("Foque em descobrir necessidades reais")
        elif stage == "avanco":
            hints.append("Agende próxima reunião com decisor")
        elif stage == "proposta":
            hints.append("Personalize proposta com benefícios claros")
        elif stage == "negociacao":
            hints.append("Negocie termos, não preço")
        elif stage == "fechamento":
            hints.append("Peça o fechamento de forma direta")
        
        return hints
    
    def get_client_history(self, client_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Buscar histórico de calls do cliente.
        
        Args:
            client_id: ID do cliente
            limit: Limite de registros
            
        Returns:
            Lista de calls do cliente
        """
        return self.dao.get_client_calls(client_id, limit)
    
    def search_clients(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Buscar clientes por nome (simples).
        
        Args:
            query: Termo de busca
            limit: Limite de resultados
            
        Returns:
            Lista de clientes encontrados
        """
        # Implementação simples - pode ser expandida com FTS5
        cursor = self.dao.connection.cursor()
        cursor.execute(
            "SELECT id, name, tier, stage FROM client WHERE name LIKE ? LIMIT ?",
            (f"%{query}%", limit)
        )
        return [dict(row) for row in cursor.fetchall()] 