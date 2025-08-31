"""
StatsService - Normalização dinâmica e percentis
==============================================

Serviço para calcular estatísticas e normalizar features usando percentis.
"""

import numpy as np
from collections import defaultdict
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)


class StatsService:
    """Serviço para normalização dinâmica baseada em percentis."""
    
    def __init__(self, dao):
        self.dao = dao
        self.logger = logging.getLogger(__name__)
    
    def fit_seller_features(self, features_iter) -> Dict[str, Dict[str, float]]:
        """
        Calcular estatísticas para features de vendedores.
        
        Args:
            features_iter: Iterável de dicionários com features DISC
            
        Returns:
            Dict com estatísticas por feature
        """
        buf = defaultdict(list)
        
        for f in features_iter:
            for k, v in f.items():
                if isinstance(v, (int, float)):
                    buf[k].append(float(v))
        
        stats = {}
        for k, arr in buf.items():
            if not arr:
                continue
                
            a = np.array(arr, dtype=float)
            s = {
                "p10": float(np.percentile(a, 10)),
                "p25": float(np.percentile(a, 25)),
                "p50": float(np.percentile(a, 50)),
                "p75": float(np.percentile(a, 75)),
                "p90": float(np.percentile(a, 90)),
                "mean": float(a.mean()),
                "std": float(a.std() + 1e-9),
                "n": int(a.size)
            }
            
            self.dao.upsert_stats(scope="seller_feature", key=k, **s)
            stats[k] = s
            
            self.logger.info(f"📊 Stats para {k}: p25={s['p25']:.3f}, p75={s['p75']:.3f}, n={s['n']}")
        
        return stats
    
    def fit_client_complexity(self, scores: List[float]) -> Optional[Dict[str, float]]:
        """
        Calcular estatísticas para scores de complexidade de clientes.
        
        Args:
            scores: Lista de scores de complexidade
            
        Returns:
            Dict com estatísticas ou None se não há dados
        """
        if not scores:
            return None
            
        a = np.array(scores, dtype=float)
        s = {
            "p10": float(np.percentile(a, 10)),
            "p25": float(np.percentile(a, 25)),
            "p50": float(np.percentile(a, 50)),
            "p75": float(np.percentile(a, 75)),
            "p90": float(np.percentile(a, 90)),
            "mean": float(a.mean()),
            "std": float(a.std() + 1e-9),
            "n": int(a.size)
        }
        
        self.dao.upsert_stats(scope="client_score", key="complexity", **s)
        
        self.logger.info(f"📊 Client complexity stats: p25={s['p25']:.3f}, p75={s['p75']:.3f}, n={s['n']}")
        
        return s
    
    def normalize(self, scope: str, key: str, x: float, method: str = "z") -> float:
        """
        Normalizar valor usando estatísticas armazenadas.
        
        Args:
            scope: Escopo ('seller_feature' ou 'client_score')
            key: Chave da feature
            x: Valor a normalizar
            method: Método ('z' para z-score, 'minmax' para percentis)
            
        Returns:
            Valor normalizado entre 0..1
        """
        st = self.dao.get_stats(scope, key)
        if not st:
            # Fallback: clamp simples
            return float(max(0.0, min(1.0, x)))
        
        if method == "z":
            # Z-score com squash sigmóide
            z = (x - st["mean"]) / st["std"]
            return float(1 / (1 + np.exp(-z)))  # squash 0..1
        
        elif method == "minmax":
            # Normalização por percentis
            lo, hi = st["p10"], st["p90"]
            return float(max(0.0, min(1.0, (x - lo) / max(1e-9, (hi - lo)))))
        
        else:
            # Método desconhecido, retornar original
            return x
    
    def get_percentile(self, scope: str, key: str, x: float) -> float:
        """
        Obter percentil de um valor.
        
        Args:
            scope: Escopo da estatística
            key: Chave da feature
            x: Valor
            
        Returns:
            Percentil (0..100)
        """
        st = self.dao.get_stats(scope, key)
        if not st:
            return 50.0  # Fallback: mediana
        
        # Aproximação linear entre percentis conhecidos
        if x <= st["p10"]:
            return 10.0
        elif x <= st["p25"]:
            return 10.0 + 15.0 * (x - st["p10"]) / (st["p25"] - st["p10"])
        elif x <= st["p50"]:
            return 25.0 + 25.0 * (x - st["p25"]) / (st["p50"] - st["p25"])
        elif x <= st["p75"]:
            return 50.0 + 25.0 * (x - st["p50"]) / (st["p75"] - st["p50"])
        elif x <= st["p90"]:
            return 75.0 + 15.0 * (x - st["p75"]) / (st["p90"] - st["p75"])
        else:
            return 90.0 + 10.0 * min(1.0, (x - st["p90"]) / (st["p90"] - st["p10"]))
    
    def get_tier_by_percentile(self, scope: str, key: str, x: float) -> str:
        """
        Determinar tier baseado em percentis.
        
        Args:
            scope: Escopo da estatística
            key: Chave da feature
            x: Valor
            
        Returns:
            Tier: 'facil', 'medio', 'dificil'
        """
        percentile = self.get_percentile(scope, key, x)
        
        if percentile < 25:
            return "facil"
        elif percentile < 75:
            return "medio"
        else:
            return "dificil"
    
    def get_stats_summary(self) -> Dict[str, Any]:
        """
        Obter resumo das estatísticas armazenadas.
        
        Returns:
            Dict com resumo das estatísticas
        """
        try:
            seller_stats = {}
            client_stats = {}
            
            # Buscar todas as estatísticas
            all_stats = self.dao.get_all_stats()
            
            for stat in all_stats:
                if stat["scope"] == "seller_feature":
                    seller_stats[stat["key"]] = {
                        "p25": stat["p25"],
                        "p75": stat["p75"],
                        "n": stat["sample_size"]
                    }
                elif stat["scope"] == "client_score":
                    client_stats[stat["key"]] = {
                        "p25": stat["p25"],
                        "p75": stat["p75"],
                        "n": stat["sample_size"]
                    }
            
            return {
                "seller_features": seller_stats,
                "client_scores": client_stats,
                "total_features": len(seller_stats),
                "total_scores": len(client_stats)
            }
            
        except Exception as e:
            self.logger.error(f"Erro ao obter resumo de estatísticas: {e}")
            return {"seller_features": {}, "client_scores": {}, "total_features": 0, "total_scores": 0} 