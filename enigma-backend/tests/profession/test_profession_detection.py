from app.profession import ProfessionDetector
from app.profession.reference_professions import MarketingSocialSellingDetector


def test_profession_detector_detects_marketing_goal():
    """Detector should detect marketing profession from relevant goal."""
    detector = MarketingSocialSellingDetector()

    # Clear marketing goal
    profession = detector.detect("I want to grow my social media audience and increase engagement")
    assert profession is not None
    assert profession.id == "marketing-social-selling"
    assert profession.name == "Marketing & Social Selling"


def test_profession_detector_returns_none_for_non_marketing_goal():
    """Detector should return None for non-marketing goals."""
    detector = MarketingSocialSellingDetector()

    # Non-marketing goal
    profession = detector.detect("I want to build a software application")
    assert profession is None


def test_profession_detector_confidence_calculation():
    """Detector should calculate confidence based on keyword matches."""
    detector = MarketingSocialSellingDetector()

    # High confidence goal (many keywords)
    profession = detector.detect("I want to improve my marketing campaign and social media selling for better engagement and conversion")
    if profession:
        confidence = detector.get_confidence("I want to improve my marketing campaign and social media selling for better engagement and conversion", profession)
        assert confidence > 0.5

    # Low confidence goal (few keywords)
    profession = detector.detect("I want to sell products")
    if profession:
        confidence = detector.get_confidence("I want to sell products", profession)
        assert confidence < 0.5


def test_profession_detector_confidence_for_wrong_profession():
    """Detector should return 0 confidence for wrong profession."""
    detector = MarketingSocialSellingDetector()

    from app.profession import Profession

    wrong_profession = Profession(
        id="software-development",
        name="Software Development",
        description="Building software",
        category="Technology",
    )

    confidence = detector.get_confidence("I want to do marketing", wrong_profession)
    assert confidence == 0.0


def test_profession_detector_case_insensitive():
    """Detector should be case-insensitive."""
    detector = MarketingSocialSellingDetector()

    profession_upper = detector.detect("I WANT TO DO MARKETING AND SOCIAL MEDIA SELLING")
    profession_lower = detector.detect("i want to do marketing and social media selling")
    profession_mixed = detector.detect("I Want To Do Marketing And Social Media Selling")

    assert profession_upper is not None
    assert profession_lower is not None
    assert profession_mixed is not None

    assert profession_upper.id == profession_lower.id == profession_mixed.id
