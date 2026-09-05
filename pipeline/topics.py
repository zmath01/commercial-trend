"""Watchlist: the fields we track, mapped onto each data source.

OpenAlex topic matching is by keyword search over topic display names
(resolved to stable topic IDs at ingest time). GitHub/StackOverflow signals
use explicit keyword / tag lists. Extend freely — this is config, not code.
"""

FIELDS = {
    "artificial_intelligence": {
        "label": "AI / Machine Learning",
        "openalex_queries": ["machine learning", "deep learning", "large language model",
                             "reinforcement learning", "neural network"],
        "github_keywords": ["machine-learning", "deep-learning", "llm", "transformer"],
        "so_tags": ["torch", "tensorflow", "transformers", "scikit-learn"],
    },
    "applied_math": {
        "label": "Applied Mathematics",
        "openalex_queries": ["optimization", "numerical analysis", "stochastic process",
                             "graph theory", "computational mathematics"],
        "github_keywords": ["optimization", "numerical-methods", "scientific-computing"],
        "so_tags": ["numpy", "scipy", "cvxpy", "networkx"],
    },
    "computer_science": {
        "label": "Computer Science (general)",
        "openalex_queries": ["computer science", "algorithms", "distributed system",
                             "database", "computer vision"],
        "github_keywords": ["algorithms", "distributed-systems", "database"],
        "so_tags": ["django", "flask", "fastapi", "sqlalchemy"],
    },
    "software_engineering": {
        "label": "Software Engineering",
        "openalex_queries": ["software engineering", "programming language",
                             "software testing", "devops"],
        "github_keywords": ["devops", "ci-cd", "testing-framework", "linter"],
        "so_tags": ["pytest", "black", "mypy", "ruff"],
    },
    "quant_finance": {
        "label": "Quantitative Finance",
        "openalex_queries": ["financial mathematics", "portfolio optimization",
                             "algorithmic trading", "risk management", "option pricing"],
        "github_keywords": ["quantitative-finance", "algorithmic-trading", "backtesting"],
        "so_tags": ["pandas", "zipline", "backtrader", "quantlib", "quantitative-finance"],
    },
    "crypto_fintech": {
        "label": "Cryptocurrency / FinTech",
        "openalex_queries": ["blockchain", "cryptocurrency", "smart contract",
                             "decentralized finance", "payment system"],
        "github_keywords": ["blockchain", "ethereum", "defi", "smart-contracts", "web3"],
        "so_tags": ["web3", "ethereum", "solidity", "blockchain", "defi"],
    },
    "quantum_computing": {
        "label": "Quantum Computing / Cryptography",
        "openalex_queries": ["quantum computing", "quantum algorithm",
                             "quantum cryptography", "quantum error correction",
                             "post-quantum cryptography"],
        "github_keywords": ["quantum-computing", "quantum-algorithms", "post-quantum"],
        "so_tags": ["qiskit", "cirq", "pennylane", "quantum-computing"],
    },
    "chips_hardware": {
        "label": "Chips / GPU / Memory Hardware",
        "openalex_queries": ["graphics processing unit", "semiconductor",
                             "computer architecture", "memory system",
                             "neuromorphic computing", "chip design"],
        "github_keywords": ["gpu-computing", "cuda", "chip-design", "riscv", "fpga"],
        "so_tags": ["cuda", "gpu", "numba", "fpga", "riscv"],
    },
}

# Composite index weights (declared explicitly per THEORY.md section 2.2d).
# Each weight applies to the min-max-normalized yearly signal.
CSI_WEIGHTS = {
    "repos_new": 0.40,     # new GitHub repos this year (engineering energy)
    "questions": 0.35,     # StackOverflow questions this year (community adoption)
    "papers": 0.25,        # publication volume (research activity)
}
