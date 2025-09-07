import logging
from typing import Dict, List, Tuple

import numpy as np


class PortfolioOptimizer:
    """
    Optimiseur d'allocation cross-exchange.

    Fournit des méthodes simples:
    - mean-variance (Markowitz) avec contraintes de poids
    - risk-parity (égalisation des contributions au risque)
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def mean_variance_weights(
        self,
        expected_returns: Dict[str, float],
        covariance_matrix: Dict[Tuple[str, str], float],
        risk_aversion: float = 3.0,
        min_weight: float = 0.0,
        max_weight: float = 0.3,
        target_leverage: float = 1.0,
    ) -> Dict[str, float]:
        """
        Calcule des poids optimaux sous contraintes simples.
        expected_returns: map symbol -> mu
        covariance_matrix: map (sym_i, sym_j) -> cov_ij
        """
        symbols: List[str] = list(expected_returns.keys())
        n: int = len(symbols)
        if n == 0:
            return {}

        # Construire mu et cov
        mu = np.array([expected_returns[s] for s in symbols], dtype=float)
        cov = np.zeros((n, n), dtype=float)
        for i, si in enumerate(symbols):
            for j, sj in enumerate(symbols):
                cov[i, j] = float(covariance_matrix.get((si, sj), covariance_matrix.get((sj, si), 0.0)))

        # Heuristique quadratique simple avec clipping: w ~ (1/λ) Σ^-1 μ
        try:
            inv_cov = np.linalg.pinv(cov)
        except Exception:
            inv_cov = np.eye(n)
        raw_w = (1.0 / max(risk_aversion, 1e-6)) * inv_cov.dot(mu)

        # Contraintes: min/max et somme = target_leverage
        w = np.clip(raw_w, min_weight, max_weight)
        s = w.sum()
        if s > 0:
            w = w * (target_leverage / s)
        else:
            # fallback uniforme
            w = np.ones(n) * (target_leverage / n)

        # Re-normaliser après clipping si dépassements
        w = np.clip(w, min_weight, max_weight)
        s = w.sum()
        if s > 0:
            w = w * (target_leverage / s)

        return {symbols[i]: float(w[i]) for i in range(n)}

    def risk_parity_weights(
        self,
        covariance_matrix: Dict[Tuple[str, str], float],
        min_weight: float = 0.0,
        max_weight: float = 0.3,
        target_leverage: float = 1.0,
        iterations: int = 200,
        lr: float = 0.1,
    ) -> Dict[str, float]:
        """
        Applique une heuristique de risk-parity par descente de gradient projetée.
        """
        symbols: List[str] = list({k[0] for k in covariance_matrix.keys()} | {k[1] for k in covariance_matrix.keys()})
        symbols.sort()
        n: int = len(symbols)
        if n == 0:
            return {}

        cov = np.zeros((n, n), dtype=float)
        for i, si in enumerate(symbols):
            for j, sj in enumerate(symbols):
                cov[i, j] = float(covariance_matrix.get((si, sj), covariance_matrix.get((sj, si), 0.0)))

        # init uniforme
        w = np.ones(n) * (target_leverage / n)
        w = np.clip(w, min_weight, max_weight)
        if w.sum() > 0:
            w *= target_leverage / w.sum()

        for _ in range(iterations):
            port_var = float(w.T.dot(cov).dot(w)) + 1e-12
            marginal_risk = cov.dot(w)  # ∂σ^2/∂w
            risk_contrib = w * marginal_risk  # contributions
            target = np.ones(n) * (port_var / n)
            grad = risk_contrib - target
            w = w - lr * grad
            w = np.clip(w, min_weight, max_weight)
            s = w.sum()
            if s > 0:
                w *= target_leverage / s

        return {symbols[i]: float(w[i]) for i in range(n)}


optimizer = PortfolioOptimizer()

