"""Tests for category normalizer."""

import pytest

from catalog_extractor.infrastructure.normalizer import FuzzyCategoryNormalizer


class TestFuzzyCategoryNormalizer:
    """Tests for FuzzyCategoryNormalizer."""

    @pytest.fixture
    def normalizer(self) -> FuzzyCategoryNormalizer:
        """Create normalizer instance."""
        return FuzzyCategoryNormalizer(threshold=75)

    def test_normalize_exact_match(self, normalizer: FuzzyCategoryNormalizer) -> None:
        """Test exact category match."""
        assert normalizer.normalize("Perfumaria") == "Perfumaria"
        assert normalizer.normalize("Maquiagem") == "Maquiagem"

    def test_normalize_case_insensitive(self, normalizer: FuzzyCategoryNormalizer) -> None:
        """Test case insensitive matching."""
        assert normalizer.normalize("perfumaria") == "Perfumaria"
        assert normalizer.normalize("MAQUIAGEM") == "Maquiagem"

    def test_normalize_synonym(self, normalizer: FuzzyCategoryNormalizer) -> None:
        """Test synonym matching."""
        assert normalizer.normalize("Perfumes") == "Perfumaria"
        assert normalizer.normalize("Make-up") == "Maquiagem"
        assert normalizer.normalize("Hidratante") == "Corpo e Banho"
        assert normalizer.normalize("Shampoo") == "Cabelos"

    def test_normalize_fuzzy_match(self, normalizer: FuzzyCategoryNormalizer) -> None:
        """Test fuzzy matching for similar terms."""
        assert normalizer.normalize("Cuidado Capilar") == "Cabelos"
        assert normalizer.normalize("Produtos para Cabelo") == "Cabelos"

    def test_normalize_no_match(self, normalizer: FuzzyCategoryNormalizer) -> None:
        """Test fallback to 'Outros' when no match."""
        assert normalizer.normalize("xyz123") == "Outros"
        assert normalizer.normalize("") == "Outros"
        assert normalizer.normalize(None) == "Outros"

    def test_add_category(self, normalizer: FuzzyCategoryNormalizer) -> None:
        """Test adding new category."""
        normalizer.add_category("Nova Categoria")
        assert "Nova Categoria" in normalizer.get_categories()

    def test_add_synonym(self, normalizer: FuzzyCategoryNormalizer) -> None:
        """Test adding synonym."""
        normalizer.add_synonym("Perfumaria", "Fragrância Nova")
        assert normalizer.normalize("Fragrância Nova") == "Perfumaria"

    def test_get_statistics(self, normalizer: FuzzyCategoryNormalizer) -> None:
        """Test statistics retrieval."""
        stats = normalizer.get_statistics()
        assert "master_categories" in stats
        assert "total_synonyms" in stats
        assert stats["master_categories"] > 0

    def test_normalize_batch(self, normalizer: FuzzyCategoryNormalizer) -> None:
        """Test batch normalization."""
        categories = ["Perfumes", "Make", "Cabelo", None, "xyz"]
        results = normalizer.normalize_batch(categories)

        assert results == ["Perfumaria", "Maquiagem", "Cabelos", "Outros", "Outros"]
