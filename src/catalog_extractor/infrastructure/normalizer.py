"""Category normalization using fuzzy matching."""

from collections import defaultdict

import structlog
from thefuzz import process

from catalog_extractor.domain.interfaces import CategoryNormalizer

logger = structlog.get_logger()


# Default master categories for cosmetics catalogs
DEFAULT_MASTER_CATEGORIES = [
    "Perfumaria",
    "Maquiagem",
    "Corpo e Banho",
    "Cabelos",
    "Skincare",
    "Infantil",
    "Masculino",
    "Unhas",
    "Acessórios",
    "Kits e Presentes",
    "Proteção Solar",
    "Desodorantes",
]

# Pre-defined synonyms for better matching
DEFAULT_SYNONYMS: dict[str, list[str]] = {
    "Perfumaria": [
        "Perfumes",
        "Fragrâncias",
        "Eau de Parfum",
        "Eau de Toilette",
        "Colônia",
        "Deo Parfum",
        "Body Spray",
    ],
    "Maquiagem": [
        "Make",
        "Make-up",
        "Makeup",
        "Cosméticos",
        "Batom",
        "Base",
        "Blush",
        "Sombra",
        "Máscara",
        "Delineador",
        "Corretivo",
        "Pó",
        "Primer",
        "Iluminador",
        "Contorno",
        "Lábios",
        "Olhos",
        "Rosto",
    ],
    "Corpo e Banho": [
        "Corpo",
        "Banho",
        "Hidratação",
        "Hidratante",
        "Loção",
        "Creme Corporal",
        "Body Lotion",
        "Óleo Corporal",
        "Esfoliante",
        "Sabonete",
        "Shower Gel",
        "Body Splash",
        "Desodorante Corporal",
        "Cuidados Corporais",
        "Hidratação Corporal",
    ],
    "Cabelos": [
        "Cabelo",
        "Hair",
        "Shampoo",
        "Condicionador",
        "Máscara Capilar",
        "Leave-in",
        "Finalizador",
        "Óleo Capilar",
        "Tratamento Capilar",
        "Cuidado Capilar",
        "Coloração",
        "Tintura",
    ],
    "Skincare": [
        "Cuidados Faciais",
        "Facial",
        "Rosto",
        "Anti-idade",
        "Anti-rugas",
        "Sérum",
        "Vitamina C",
        "Ácido Hialurônico",
        "Retinol",
        "Cleanser",
        "Tônico",
        "Hidratante Facial",
        "Protetor Facial",
        "Creme Facial",
        "Máscara Facial",
        "Esfoliante Facial",
        "Limpeza Facial",
        "Demaquilante",
        "Água Micelar",
    ],
    "Infantil": [
        "Bebê",
        "Baby",
        "Criança",
        "Kids",
        "Infantil",
        "Linha Bebê",
    ],
    "Masculino": [
        "Homem",
        "Men",
        "Masculina",
        "Barba",
        "Pós-barba",
        "Barbear",
    ],
    "Unhas": [
        "Esmalte",
        "Nail",
        "Unha",
        "Cutículas",
        "Base para Unhas",
        "Top Coat",
    ],
    "Acessórios": [
        "Acessório",
        "Necessaire",
        "Bolsa",
        "Espelho",
        "Pincel",
        "Aplicador",
        "Esponja",
    ],
    "Kits e Presentes": [
        "Kit",
        "Combo",
        "Presente",
        "Gift",
        "Conjunto",
        "Coleção",
        "Edição Especial",
    ],
    "Proteção Solar": [
        "Protetor Solar",
        "FPS",
        "Sunscreen",
        "Bronzeador",
        "Pós-Sol",
        "Solar",
    ],
    "Desodorantes": [
        "Desodorante",
        "Antitranspirante",
        "Deo",
        "Roll-on",
        "Aerossol",
        "Spray",
    ],
}


class FuzzyCategoryNormalizer(CategoryNormalizer):
    """Category normalizer using fuzzy string matching."""

    def __init__(
        self,
        master_categories: list[str] | None = None,
        synonyms: dict[str, list[str]] | None = None,
        threshold: int = 75,
    ) -> None:
        """Initialize normalizer.

        Args:
            master_categories: List of master category names
            synonyms: Dict mapping master categories to their synonyms
            threshold: Minimum fuzzy match score (0-100)
        """
        self._master_categories = list(master_categories or DEFAULT_MASTER_CATEGORIES)
        self._threshold = threshold
        self._logger = logger.bind(component="FuzzyCategoryNormalizer")

        # Build synonym mapping (synonym -> master category)
        self._synonym_to_master: dict[str, str] = {}
        self._master_to_synonyms: dict[str, list[str]] = defaultdict(list)

        # Initialize with default or provided synonyms
        initial_synonyms = synonyms if synonyms is not None else DEFAULT_SYNONYMS
        for master, syns in initial_synonyms.items():
            if master in self._master_categories:
                for syn in syns:
                    self._synonym_to_master[syn.lower()] = master
                    self._master_to_synonyms[master].append(syn)

        # Build search corpus (all master categories + synonyms)
        self._search_corpus = self._build_search_corpus()

        self._logger.info(
            "Normalizer initialized",
            categories=len(self._master_categories),
            synonyms=len(self._synonym_to_master),
            threshold=threshold,
        )

    def _build_search_corpus(self) -> list[str]:
        """Build search corpus from categories and synonyms."""
        corpus = list(self._master_categories)
        corpus.extend(self._synonym_to_master.keys())
        return corpus

    def normalize(self, raw_category: str | None) -> str:
        """Normalize a category to a master category.

        Args:
            raw_category: Raw category string from extraction

        Returns:
            Normalized master category or "Outros" if no match
        """
        if not raw_category:
            return "Outros"

        raw_lower = raw_category.strip().lower()

        # Direct match with master category
        for master in self._master_categories:
            if raw_lower == master.lower():
                return master

        # Direct match with synonym
        if raw_lower in self._synonym_to_master:
            return self._synonym_to_master[raw_lower]

        # Fuzzy match
        match_result = process.extractOne(raw_category, self._search_corpus)
        if match_result:
            best_match, score = match_result[0], match_result[1]

            if score >= self._threshold:
                # Check if match is a synonym
                if best_match.lower() in self._synonym_to_master:
                    master = self._synonym_to_master[best_match.lower()]
                else:
                    master = best_match

                self._logger.debug(
                    "Fuzzy match found",
                    raw=raw_category,
                    matched=master,
                    score=score,
                )
                return master

        self._logger.debug(
            "No match found",
            raw=raw_category,
            best_score=match_result[1] if match_result else 0,
        )
        return "Outros"

    def add_category(self, category: str) -> None:
        """Add a new master category."""
        if category not in self._master_categories:
            self._master_categories.append(category)
            self._search_corpus = self._build_search_corpus()
            self._logger.info("Added new category", category=category)

    def add_synonym(self, master_category: str, synonym: str) -> None:
        """Add a synonym for a master category.

        Args:
            master_category: The master category
            synonym: Synonym to add
        """
        if master_category not in self._master_categories:
            self._logger.warning(
                "Master category not found",
                category=master_category,
            )
            return

        syn_lower = synonym.lower()
        if syn_lower not in self._synonym_to_master:
            self._synonym_to_master[syn_lower] = master_category
            self._master_to_synonyms[master_category].append(synonym)
            self._search_corpus = self._build_search_corpus()

    def get_categories(self) -> list[str]:
        """Get list of master categories."""
        return list(self._master_categories)

    def get_synonyms(self, category: str) -> list[str]:
        """Get synonyms mapped to a master category."""
        return list(self._master_to_synonyms.get(category, []))

    def normalize_batch(self, categories: list[str | None]) -> list[str]:
        """Normalize multiple categories.

        Args:
            categories: List of raw category strings

        Returns:
            List of normalized categories
        """
        return [self.normalize(cat) for cat in categories]

    def get_statistics(self) -> dict:
        """Get normalizer statistics."""
        return {
            "master_categories": len(self._master_categories),
            "total_synonyms": len(self._synonym_to_master),
            "threshold": self._threshold,
            "categories": self._master_categories,
        }
