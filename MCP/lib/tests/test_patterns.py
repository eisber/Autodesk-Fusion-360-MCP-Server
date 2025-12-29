"""Tests for pattern features module.

Tests for:
- circular_pattern (from MCP_old.py: circular_pattern)
- rectangular_pattern (from MCP_old.py: rect_pattern)
"""

import pytest
from unittest.mock import MagicMock, patch, call


class TestCircularPattern:
    """Tests for circular_pattern function."""

    def test_circular_pattern_z_axis(self, mock_design, mock_ui, mock_body):
        """Test circular pattern around Z axis."""
        from lib.features.patterns import circular_pattern

        mock_design.rootComponent.bRepBodies.count = 1
        mock_design.rootComponent.bRepBodies.item.return_value = mock_body

        circular_pattern(mock_design, mock_ui, quantity=6, axis="Z", plane="XY")

        # Verify pattern was created
        circ_feats = mock_design.rootComponent.features.circularPatternFeatures
        circ_feats.createInput.assert_called_once()
        circ_feats.add.assert_called_once()

    def test_circular_pattern_x_axis(self, mock_design, mock_ui, mock_body):
        """Test circular pattern around X axis."""
        from lib.features.patterns import circular_pattern

        mock_design.rootComponent.bRepBodies.count = 1
        mock_design.rootComponent.bRepBodies.item.return_value = mock_body

        circular_pattern(mock_design, mock_ui, quantity=4, axis="X", plane="YZ")

        circ_feats = mock_design.rootComponent.features.circularPatternFeatures
        circ_feats.createInput.assert_called_once()

        # Verify X axis was used
        call_args = circ_feats.createInput.call_args
        assert call_args[0][1] == mock_design.rootComponent.xConstructionAxis

    def test_circular_pattern_y_axis(self, mock_design, mock_ui, mock_body):
        """Test circular pattern around Y axis."""
        from lib.features.patterns import circular_pattern

        mock_design.rootComponent.bRepBodies.count = 1
        mock_design.rootComponent.bRepBodies.item.return_value = mock_body

        circular_pattern(mock_design, mock_ui, quantity=8, axis="Y", plane="XZ")

        circ_feats = mock_design.rootComponent.features.circularPatternFeatures
        circ_feats.createInput.assert_called_once()

        # Verify Y axis was used
        call_args = circ_feats.createInput.call_args
        assert call_args[0][1] == mock_design.rootComponent.yConstructionAxis

    def test_circular_pattern_no_bodies(self, mock_design, mock_ui):
        """Test circular pattern with no bodies shows message."""
        from lib.features.patterns import circular_pattern

        mock_design.rootComponent.bRepBodies.count = 0

        circular_pattern(mock_design, mock_ui, quantity=6, axis="Z", plane="XY")

        mock_ui.messageBox.assert_called_once()
        assert "No bodies found" in str(mock_ui.messageBox.call_args)

    def test_circular_pattern_uses_latest_body(self, mock_design, mock_ui, mock_body):
        """Test that circular pattern uses the latest body."""
        from lib.features.patterns import circular_pattern

        body1 = MagicMock(name="Body1")
        body2 = MagicMock(name="Body2")
        body3 = MagicMock(name="Body3")

        mock_design.rootComponent.bRepBodies.count = 3
        mock_design.rootComponent.bRepBodies.item.side_effect = lambda i: [body1, body2, body3][i]

        circular_pattern(mock_design, mock_ui, quantity=6, axis="Z", plane="XY")

        # Verify the last body (index 2) was accessed
        mock_design.rootComponent.bRepBodies.item.assert_called_with(2)

    def test_circular_pattern_error_handling(self, mock_design, mock_ui, mock_body):
        """Test error handling in circular_pattern."""
        from lib.features.patterns import circular_pattern

        mock_design.rootComponent.bRepBodies.count = 1
        mock_design.rootComponent.bRepBodies.item.return_value = mock_body
        mock_design.rootComponent.features.circularPatternFeatures.createInput.side_effect = Exception("Test error")

        circular_pattern(mock_design, mock_ui, quantity=6, axis="Z", plane="XY")

        mock_ui.messageBox.assert_called_once()
        assert "Failed circular_pattern" in str(mock_ui.messageBox.call_args)


class TestRectangularPattern:
    """Tests for rectangular_pattern function."""

    def test_rectangular_pattern_xy(self, mock_design, mock_ui, mock_body):
        """Test rectangular pattern in XY plane."""
        from lib.features.patterns import rectangular_pattern

        mock_design.rootComponent.bRepBodies.count = 1
        mock_design.rootComponent.bRepBodies.item.return_value = mock_body

        rectangular_pattern(
            mock_design, mock_ui,
            axis_one="X", axis_two="Y",
            quantity_one=3, quantity_two=2,
            distance_one=10, distance_two=10,
            plane="XY"
        )

        # Verify pattern was created
        rect_feats = mock_design.rootComponent.features.rectangularPatternFeatures
        rect_feats.createInput.assert_called_once()
        rect_feats.add.assert_called_once()

        # Verify second direction was set
        rect_input = rect_feats.createInput.return_value
        rect_input.setDirectionTwo.assert_called_once()

    def test_rectangular_pattern_xz(self, mock_design, mock_ui, mock_body):
        """Test rectangular pattern in XZ plane."""
        from lib.features.patterns import rectangular_pattern

        mock_design.rootComponent.bRepBodies.count = 1
        mock_design.rootComponent.bRepBodies.item.return_value = mock_body

        rectangular_pattern(
            mock_design, mock_ui,
            axis_one="X", axis_two="Z",
            quantity_one=4, quantity_two=3,
            distance_one=5, distance_two=5,
            plane="XZ"
        )

        rect_feats = mock_design.rootComponent.features.rectangularPatternFeatures
        rect_feats.createInput.assert_called_once()

    def test_rectangular_pattern_yz(self, mock_design, mock_ui, mock_body):
        """Test rectangular pattern in YZ plane."""
        from lib.features.patterns import rectangular_pattern

        mock_design.rootComponent.bRepBodies.count = 1
        mock_design.rootComponent.bRepBodies.item.return_value = mock_body

        rectangular_pattern(
            mock_design, mock_ui,
            axis_one="Y", axis_two="Z",
            quantity_one=2, quantity_two=4,
            distance_one=20, distance_two=15,
            plane="YZ"
        )

        rect_feats = mock_design.rootComponent.features.rectangularPatternFeatures
        rect_feats.createInput.assert_called_once()

    def test_rectangular_pattern_no_bodies(self, mock_design, mock_ui):
        """Test rectangular pattern with no bodies shows message."""
        from lib.features.patterns import rectangular_pattern

        mock_design.rootComponent.bRepBodies.count = 0

        rectangular_pattern(
            mock_design, mock_ui,
            axis_one="X", axis_two="Y",
            quantity_one=3, quantity_two=2,
            distance_one=10, distance_two=10,
            plane="XY"
        )

        mock_ui.messageBox.assert_called_once()
        assert "No bodies found" in str(mock_ui.messageBox.call_args)

    def test_rectangular_pattern_uses_latest_body(self, mock_design, mock_ui, mock_body):
        """Test that rectangular pattern uses the latest body."""
        from lib.features.patterns import rectangular_pattern

        body1 = MagicMock(name="Body1")
        body2 = MagicMock(name="Body2")

        mock_design.rootComponent.bRepBodies.count = 2
        mock_design.rootComponent.bRepBodies.item.side_effect = lambda i: [body1, body2][i]

        rectangular_pattern(
            mock_design, mock_ui,
            axis_one="X", axis_two="Y",
            quantity_one=3, quantity_two=2,
            distance_one=10, distance_two=10,
            plane="XY"
        )

        # Verify the last body (index 1) was accessed
        mock_design.rootComponent.bRepBodies.item.assert_called_with(1)

    def test_rectangular_pattern_error_handling(self, mock_design, mock_ui, mock_body):
        """Test error handling in rectangular_pattern."""
        from lib.features.patterns import rectangular_pattern

        mock_design.rootComponent.bRepBodies.count = 1
        mock_design.rootComponent.bRepBodies.item.return_value = mock_body
        mock_design.rootComponent.features.rectangularPatternFeatures.createInput.side_effect = Exception("Test error")

        rectangular_pattern(
            mock_design, mock_ui,
            axis_one="X", axis_two="Y",
            quantity_one=3, quantity_two=2,
            distance_one=10, distance_two=10,
            plane="XY"
        )

        mock_ui.messageBox.assert_called_once()
        assert "Failed rectangular_pattern" in str(mock_ui.messageBox.call_args)


class TestPatternEquivalence:
    """Tests to validate equivalence between old and new pattern functions."""

    def test_circular_pattern_signature(self, mock_design, mock_ui, mock_body):
        """Verify circular_pattern accepts same parameters as old version."""
        from lib.features.patterns import circular_pattern

        # Old signature: circular_pattern(design, ui, quantity, axis, plane)
        mock_design.rootComponent.bRepBodies.count = 1
        mock_design.rootComponent.bRepBodies.item.return_value = mock_body

        circular_pattern(mock_design, mock_ui, 6, "Z", "XY")  # Positional
        circular_pattern(mock_design, mock_ui, quantity=6, axis="Z", plane="XY")  # Keyword

    def test_rectangular_pattern_signature(self, mock_design, mock_ui, mock_body):
        """Verify rectangular_pattern accepts same parameters as old rect_pattern."""
        from lib.features.patterns import rectangular_pattern

        # Old signature: rect_pattern(design, ui, axis_one, axis_two, quantity_one, quantity_two, distance_one, distance_two, plane="XY")
        mock_design.rootComponent.bRepBodies.count = 1
        mock_design.rootComponent.bRepBodies.item.return_value = mock_body

        # Positional
        rectangular_pattern(mock_design, mock_ui, "X", "Y", 3, 2, 10, 10, "XY")
        
        # Keyword
        rectangular_pattern(
            mock_design, mock_ui,
            axis_one="X", axis_two="Y",
            quantity_one=3, quantity_two=2,
            distance_one=10, distance_two=10,
            plane="XY"
        )


class TestPatternWorkflow:
    """Integration-style tests for pattern workflows."""

    def test_circular_pattern_after_cylinder(self, mock_design, mock_ui, mock_body, mock_sketch):
        """Test creating holes in a circular pattern around a cylinder."""
        from lib.geometry.primitives import draw_cylinder
        from lib.features.patterns import circular_pattern

        # Create a cylinder first
        draw_cylinder(mock_design, mock_ui, radius=5, height=2, x=0, y=0, z=0, plane="XY")

        # Setup mock to have one body
        mock_design.rootComponent.bRepBodies.count = 1
        mock_design.rootComponent.bRepBodies.item.return_value = mock_body

        # Create circular pattern
        circular_pattern(mock_design, mock_ui, quantity=8, axis="Z", plane="XY")

        # Both operations should complete
        mock_design.rootComponent.features.extrudeFeatures.add.assert_called_once()
        mock_design.rootComponent.features.circularPatternFeatures.add.assert_called_once()

    def test_rectangular_pattern_after_box(self, mock_design, mock_ui, mock_body, mock_sketch):
        """Test creating a grid pattern of boxes."""
        from lib.geometry.primitives import draw_box
        from lib.features.patterns import rectangular_pattern

        # Create a box first
        draw_box(mock_design, mock_ui, height=2, width=2, depth=2, x=0, y=0, z=0, plane="XY")

        # Setup mock to have one body
        mock_design.rootComponent.bRepBodies.count = 1
        mock_design.rootComponent.bRepBodies.item.return_value = mock_body

        # Create rectangular pattern (3x3 grid)
        rectangular_pattern(
            mock_design, mock_ui,
            axis_one="X", axis_two="Y",
            quantity_one=3, quantity_two=3,
            distance_one=30, distance_two=30,
            plane="XY"
        )

        # Both operations should complete
        mock_design.rootComponent.features.extrudeFeatures.add.assert_called_once()
        mock_design.rootComponent.features.rectangularPatternFeatures.add.assert_called_once()
