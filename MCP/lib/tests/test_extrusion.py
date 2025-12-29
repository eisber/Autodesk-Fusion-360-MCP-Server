"""Tests for extrusion features module.

Tests for:
- extrude_last_sketch (from MCP_old.py: extrude_last_sketch)
- extrude_thin (from MCP_old.py: extrude_thin)
- cut_extrude (from MCP_old.py: cut_extrude)
"""

import pytest
from unittest.mock import MagicMock, patch, call


class TestExtrudeLastSketch:
    """Tests for extrude_last_sketch function."""

    def test_extrude_basic(self, mock_design, mock_ui, mock_sketch):
        """Test basic extrusion without taper."""
        from lib.features.extrusion import extrude_last_sketch

        mock_design.rootComponent.sketches.count = 1
        mock_design.rootComponent.sketches.item.return_value = mock_sketch

        extrude_last_sketch(mock_design, mock_ui, value=5, taperangle=0)

        # Verify extrusion was created
        extrudes = mock_design.rootComponent.features.extrudeFeatures
        extrudes.createInput.assert_called_once()
        extrudes.add.assert_called_once()

        # Verify the extrude input was configured
        ext_input = extrudes.createInput.return_value
        ext_input.setDistanceExtent.assert_called_once()

    def test_extrude_with_taper(self, mock_design, mock_ui, mock_sketch):
        """Test extrusion with taper angle."""
        from lib.features.extrusion import extrude_last_sketch

        mock_design.rootComponent.sketches.count = 1
        mock_design.rootComponent.sketches.item.return_value = mock_sketch

        extrude_last_sketch(mock_design, mock_ui, value=5, taperangle=10)

        # Verify extrusion was created
        extrudes = mock_design.rootComponent.features.extrudeFeatures
        extrudes.createInput.assert_called_once()
        extrudes.add.assert_called_once()

        # Verify taper was applied (setOneSideExtent should be called instead of setDistanceExtent)
        ext_input = extrudes.createInput.return_value
        ext_input.setOneSideExtent.assert_called_once()

    def test_extrude_uses_last_sketch(self, mock_design, mock_ui, mock_sketch):
        """Test that extrusion uses the last sketch."""
        from lib.features.extrusion import extrude_last_sketch

        mock_design.rootComponent.sketches.count = 3
        mock_design.rootComponent.sketches.item.return_value = mock_sketch

        extrude_last_sketch(mock_design, mock_ui, value=5, taperangle=0)

        # Verify it accessed the last sketch (index = count - 1 = 2)
        mock_design.rootComponent.sketches.item.assert_called_with(2)

    def test_extrude_error_handling(self, mock_design, mock_ui, mock_sketch):
        """Test error handling in extrude_last_sketch."""
        from lib.features.extrusion import extrude_last_sketch

        mock_design.rootComponent.sketches.item.side_effect = Exception("Test error")

        extrude_last_sketch(mock_design, mock_ui, value=5, taperangle=0)

        mock_ui.messageBox.assert_called_once()
        assert "Failed extrude_last_sketch" in str(mock_ui.messageBox.call_args)


class TestExtrudeThin:
    """Tests for extrude_thin function."""

    def test_extrude_thin_basic(self, mock_design, mock_ui, mock_sketch):
        """Test thin extrusion for hollow bodies."""
        from lib.features.extrusion import extrude_thin

        mock_design.rootComponent.sketches.count = 1
        mock_design.rootComponent.sketches.item.return_value = mock_sketch

        extrude_thin(mock_design, mock_ui, thickness=0.5, distance=5)

        # Verify extrusion was created
        extrudes = mock_design.rootComponent.features.extrudeFeatures
        extrudes.createInput.assert_called_once()
        extrudes.add.assert_called_once()

        # Verify thin extrude was configured
        ext_input = extrudes.createInput.return_value
        ext_input.setThinExtrude.assert_called_once()

    def test_extrude_thin_uses_last_sketch(self, mock_design, mock_ui, mock_sketch):
        """Test that thin extrusion uses the last sketch."""
        from lib.features.extrusion import extrude_thin

        mock_design.rootComponent.sketches.count = 2
        mock_design.rootComponent.sketches.item.return_value = mock_sketch

        extrude_thin(mock_design, mock_ui, thickness=0.5, distance=5)

        # Verify it accessed the last sketch
        mock_design.rootComponent.sketches.item.assert_called_with(1)

    def test_extrude_thin_error_handling(self, mock_design, mock_ui, mock_sketch):
        """Test error handling in extrude_thin."""
        from lib.features.extrusion import extrude_thin

        mock_design.rootComponent.sketches.item.side_effect = Exception("Test error")

        extrude_thin(mock_design, mock_ui, thickness=0.5, distance=5)

        mock_ui.messageBox.assert_called_once()
        assert "Failed extrude_thin" in str(mock_ui.messageBox.call_args)


class TestCutExtrude:
    """Tests for cut_extrude function."""

    def test_cut_extrude_basic(self, mock_design, mock_ui, mock_sketch):
        """Test cut extrusion (material removal)."""
        from lib.features.extrusion import cut_extrude

        mock_design.rootComponent.sketches.count = 1
        mock_design.rootComponent.sketches.item.return_value = mock_sketch

        cut_extrude(mock_design, mock_ui, depth=-2)

        # Verify extrusion was created
        extrudes = mock_design.rootComponent.features.extrudeFeatures
        extrudes.createInput.assert_called_once()
        extrudes.add.assert_called_once()

    def test_cut_extrude_uses_cut_operation(self, mock_design, mock_ui, mock_sketch, mock_adsk_module):
        """Test that cut extrude uses CutFeatureOperation."""
        from lib.features.extrusion import cut_extrude

        mock_design.rootComponent.sketches.count = 1
        mock_design.rootComponent.sketches.item.return_value = mock_sketch

        cut_extrude(mock_design, mock_ui, depth=-2)

        # Verify CutFeatureOperation was used
        extrudes = mock_design.rootComponent.features.extrudeFeatures
        call_args = extrudes.createInput.call_args
        # The second argument should be the cut operation
        assert call_args[0][1] == mock_adsk_module.fusion.FeatureOperations.CutFeatureOperation

    def test_cut_extrude_uses_last_sketch(self, mock_design, mock_ui, mock_sketch):
        """Test that cut extrusion uses the last sketch."""
        from lib.features.extrusion import cut_extrude

        mock_design.rootComponent.sketches.count = 4
        mock_design.rootComponent.sketches.item.return_value = mock_sketch

        cut_extrude(mock_design, mock_ui, depth=-2)

        # Verify it accessed the last sketch (index = count - 1 = 3)
        mock_design.rootComponent.sketches.item.assert_called_with(3)

    def test_cut_extrude_error_handling(self, mock_design, mock_ui, mock_sketch):
        """Test error handling in cut_extrude."""
        from lib.features.extrusion import cut_extrude

        mock_design.rootComponent.sketches.item.side_effect = Exception("Test error")

        cut_extrude(mock_design, mock_ui, depth=-2)

        mock_ui.messageBox.assert_called_once()
        assert "Failed cut_extrude" in str(mock_ui.messageBox.call_args)


class TestExtrusionEquivalence:
    """Tests to validate equivalence between old and new extrusion functions."""

    def test_extrude_last_sketch_signature(self, mock_design, mock_ui, mock_sketch):
        """Verify extrude_last_sketch accepts same parameters as old version."""
        from lib.features.extrusion import extrude_last_sketch

        # Old signature: extrude_last_sketch(design, ui, value, taperangle)
        extrude_last_sketch(mock_design, mock_ui, 5, 0)  # Positional
        extrude_last_sketch(mock_design, mock_ui, value=5, taperangle=0)  # Keyword

    def test_extrude_thin_signature(self, mock_design, mock_ui, mock_sketch):
        """Verify extrude_thin accepts same parameters as old version."""
        from lib.features.extrusion import extrude_thin

        # Old signature: extrude_thin(design, ui, thickness, distance)
        extrude_thin(mock_design, mock_ui, 0.5, 5)  # Positional
        extrude_thin(mock_design, mock_ui, thickness=0.5, distance=5)  # Keyword

    def test_cut_extrude_signature(self, mock_design, mock_ui, mock_sketch):
        """Verify cut_extrude accepts same parameters as old version."""
        from lib.features.extrusion import cut_extrude

        # Old signature: cut_extrude(design, ui, depth)
        cut_extrude(mock_design, mock_ui, -2)  # Positional
        cut_extrude(mock_design, mock_ui, depth=-2)  # Keyword


class TestExtrusionWorkflow:
    """Integration-style tests for common extrusion workflows."""

    def test_sketch_then_extrude_workflow(self, mock_design, mock_ui, mock_sketch):
        """Test typical workflow: create sketch then extrude."""
        from lib.geometry.sketches import draw_circle
        from lib.features.extrusion import extrude_last_sketch

        # Create a circle sketch
        mock_design.rootComponent.sketches.count = 0
        draw_circle(mock_design, mock_ui, radius=2.5, x=0, y=0, z=0, plane="XY")

        # Update mock to reflect sketch was added
        mock_design.rootComponent.sketches.count = 1
        mock_design.rootComponent.sketches.item.return_value = mock_sketch

        # Extrude the sketch
        extrude_last_sketch(mock_design, mock_ui, value=5, taperangle=0)

        # Verify both operations completed
        mock_design.rootComponent.sketches.add.assert_called_once()
        mock_design.rootComponent.features.extrudeFeatures.add.assert_called_once()

    def test_thin_wall_cylinder_workflow(self, mock_design, mock_ui, mock_sketch):
        """Test creating a thin-walled cylinder (tube)."""
        from lib.geometry.sketches import draw_circle
        from lib.features.extrusion import extrude_thin

        # Create a circle sketch
        mock_design.rootComponent.sketches.count = 0
        draw_circle(mock_design, mock_ui, radius=2.5, x=0, y=0, z=0, plane="XY")

        # Update mock
        mock_design.rootComponent.sketches.count = 1
        mock_design.rootComponent.sketches.item.return_value = mock_sketch

        # Create thin extrusion
        extrude_thin(mock_design, mock_ui, thickness=0.2, distance=5)

        # Verify thin extrude was used
        ext_input = mock_design.rootComponent.features.extrudeFeatures.createInput.return_value
        ext_input.setThinExtrude.assert_called_once()
