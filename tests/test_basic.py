"""Test basic functionality of the wn_gloss package."""

import wn_gloss


def test_version():
    """Test that the package has a version."""
    assert hasattr(wn_gloss, "__version__")
    assert isinstance(wn_gloss.__version__, str)
    assert len(wn_gloss.__version__) > 0
