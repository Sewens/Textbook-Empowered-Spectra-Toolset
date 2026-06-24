class MLService:
    """Boundary for future ML model integration.

    The prototype returns deterministic placeholders. Long-running model calls can
    later be moved behind this interface and scheduled with Celery/Redis.
    """

    def describe_formula(self, smiles: str | None) -> str:
        if not smiles:
            return "未提供 SMILES，暂不生成分子结构描述。"
        return f"SMILES: {smiles}"
