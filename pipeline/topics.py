"""Watchlist: ten commercial fields with a shared arXiv taxonomy.

The arXiv category list is deliberately identical to commercial-trend-fusion:
23 categories grouped into 10 commercial fields. OpenAlex/GitHub/StackOverflow
signals remain field-level; arxiv_categories provides the canonical research
scope for cross-repository comparability.
"""

FIELDS = {
    "artificial_intelligence": {
        "label": "AI / Machine Learning",
        "arxiv_categories": ["cs.AI", "cs.LG", "cs.CL", "cs.CV", "stat.ML", "cs.NE"],
        "openalex_queries": ["machine learning", "deep learning", "large language model",
                             "reinforcement learning", "neural network"],
        "github_keywords": ["machine-learning", "deep-learning", "llm", "transformer"],
        "so_tags": ["torch", "tensorflow", "transformers", "scikit-learn"],
    },
    "applied_math": {
        "label": "Applied Mathematics",
        "arxiv_categories": ["math.OC", "math.NA"],
        "openalex_queries": ["optimization", "numerical analysis", "computational mathematics",
                             "optimal control"],
        "github_keywords": ["optimization", "numerical-methods", "scientific-computing"],
        "so_tags": ["numpy", "scipy", "cvxpy", "networkx"],
    },
    "computer_science": {
        "label": "Computer Science",
        "arxiv_categories": ["cs.DS", "cs.DC"],
        "openalex_queries": ["algorithms", "distributed system", "data structures",
                             "parallel computing"],
        "github_keywords": ["algorithms", "distributed-systems", "parallel-computing"],
        "so_tags": ["algorithm", "distributed", "parallel-processing"],
    },
    "software_engineering": {
        "label": "Software Engineering",
        "arxiv_categories": ["cs.SE", "cs.PL"],
        "openalex_queries": ["software engineering", "programming language",
                             "software testing", "software maintenance"],
        "github_keywords": ["devops", "ci-cd", "testing-framework", "linter"],
        "so_tags": ["pytest", "black", "mypy", "ruff"],
    },
    "security_crypto": {
        "label": "Security / Cryptography",
        "arxiv_categories": ["cs.CR"],
        "openalex_queries": ["cryptography", "cybersecurity", "privacy enhancing technology",
                             "authentication"],
        "github_keywords": ["cryptography", "cybersecurity", "zero-knowledge", "privacy"],
        "so_tags": ["cryptography", "security", "encryption", "oauth-2.0"],
    },
    "quant_finance": {
        "label": "Quantitative Finance",
        "arxiv_categories": ["q-fin.CP", "q-fin.MF", "q-fin.RM", "q-fin.ST", "q-fin.TR"],
        "openalex_queries": ["financial mathematics", "portfolio optimization",
                             "algorithmic trading", "risk management", "option pricing"],
        "github_keywords": ["quantitative-finance", "algorithmic-trading", "backtesting"],
        "so_tags": ["pandas", "zipline", "backtrader", "quantlib", "quantitative-finance"],
    },
    "fintech": {
        "label": "FinTech",
        "arxiv_categories": ["cs.CE"],
        "openalex_queries": ["financial technology", "payment system", "digital payments",
                             "financial computing"],
        "github_keywords": ["fintech", "payments", "payment-gateway", "open-banking"],
        "so_tags": ["stripe-payments", "paypal", "payment", "fintech"],
    },
    "quantum_computing": {
        "label": "Quantum Computing",
        "arxiv_categories": ["quant-ph"],
        "openalex_queries": ["quantum computing", "quantum algorithm", "quantum error correction",
                             "quantum information"],
        "github_keywords": ["quantum-computing", "quantum-algorithms", "quantum-information"],
        "so_tags": ["qiskit", "cirq", "pennylane", "quantum-computing"],
    },
    "chips_hardware": {
        "label": "Chips / GPU / Storage / Architecture",
        "arxiv_categories": ["cs.AR", "cs.ET"],
        "openalex_queries": ["graphics processing unit", "semiconductor",
                             "computer architecture", "memory system", "chip design"],
        "github_keywords": ["gpu-computing", "cuda", "chip-design", "riscv", "fpga"],
        "so_tags": ["cuda", "gpu", "numba", "fpga", "riscv"],
    },
    "digital_markets": {
        "label": "Digital Markets / Mechanism Design",
        "arxiv_categories": ["cs.GT"],
        "openalex_queries": ["mechanism design", "electronic commerce", "market design",
                             "computational game theory"],
        "github_keywords": ["mechanism-design", "market-design", "game-theory", "auction"],
        "so_tags": ["game-theory", "auction", "marketplace", "e-commerce"],
    },
}

# Composite index weights (declared explicitly per THEORY.md section 2.2d).
CSI_WEIGHTS = {
    "repos_new": 0.40,
    "questions": 0.35,
    "papers": 0.25,
}
