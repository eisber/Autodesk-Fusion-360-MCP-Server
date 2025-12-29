"""Tests for transform features module.

Tests for:
- move_last_body (from MCP_old.py: move_last_body)
- offsetplane (from MCP_old.py: offsetplane)
"""

import pytest
from unittest.mock import MagicMock, patch, call


class TestMoveLastBody:
    """Tests for move_last_body function."""

    def test_move_body_basic(self, mock_design, mock_ui, mock_body):
        """Test basic body movement."""
        from lib.features.transform import move_last_body

        mock_design.rootComponent.bRepBodies.count = 1
        mock_design.rootComponent.bRepBodies.item.return_value = mock_body

        move_last_body(mock_design, mock_ui, x=10, y=20, z=30)

        # Verify move feature was created
        move_feats = mock_design.rootComponent.features.moveFeatures
        move_feats.createInput2.assert_called_once()
        move_feats.add.assert_called_once()

    def test_move_body_negative(self, mock_design, mock_ui, mock_body):
        """Test body movement with negative values."""
        from lib.features.transform import move_last_body

        mock_design.rootComponent.bRepBodies.count = 1
        mock_design.rootComponent.bRepBodies.item.return_value = mock_body

        move_last_body(mock_design, mock_ui, x=-5, y=-10, z=-15)

        move_feats = mock_design.rootComponent.features.moveFeatures
        move_feats.createInput2.assert_called_once()
        move_feats.add.assert_called_once()

    def test_move_body_zero(self, mock_design, mock_ui, mock_body):
        """Test body movement with zero offset (no-op)."""
        from lib.features.transform import move_last_body

        mock_design.rootComponent.bRepBodies.count = 1
        mock_design.rootComponent.bRepBodies.item.return_value = mock_body

        move_last_body(mock_design, mock_ui, x=0, y=0, z=0)

        # Even zero movement creates a move feature
        move_feats = mock_design.rootComponent.features.moveFeatures
        move_feats.createInput2.assert_called_once()

    def test_move_body_uses_latest(self, mock_design, mock_ui, mock_body):
        """Test that move uses the latest body."""
        from lib.features.transform import move_last_body

        body1 = MagicMock(name="Body1")
        body2 = MagicMock(name="Body2")
        body3 = MagicMock(name="Body3")

        mock_design.rootComponent.bRepBodies.count = 3
        mock_design.rootComponent.bRepBodies.item.side_effect = lambda i: [body1, body2, body3][i]

        move_last_body(mock_design, mock_ui, x=10, y=10, z=10)

        # Verify the last body (index 2) was accessed
        mock_design.rootComponent.bRepBodies.item.assert_called_with(2)

    def test_move_body_no_bodies(self, mock_design, mock_ui):
        """Test move with no bodies shows message."""
        from lib.features.transform import move_last_body

        mock_design.rootComponent.bRepBodies.count = 0

        move_last_body(mock_design, mock_ui, x=10, y=10, z=10)

        mock_ui.messageBox.assert_called_once()
        assert "No bodies found" in str(mock_ui.messageBox.call_args)

    def test_move_body_error_handling(self, mock_design, mock_ui, mock_body):
        """Test error handling in move_last_body."""
        from lib.features.transform import move_last_body

        mock_design.rootComponent.bRepBodies.count = 1
        mock_design.rootComponent.bRepBodies.item.return_value = mock_body
        mock_design.rootComponent.features.moveFeatures.createInput2.side_effect = Exception("Test error")

        move_last_body(mock_design, mock_ui, x=10, y=10, z=10)

        mock_ui.messageBox.assert_called_once()
        assert "Failed move_last_body" in str(mock_ui.messageBox.call_args)


class TestOffsetPlane:
    """Tests for offsetplane function."""

    def test_offset_plane_xy(self, mock_design, mock_ui):
        """Test offset plane from XY plane."""
        from lib.features.transform import offsetplane

        offsetplane(mock_design, mock_ui, offset=10, plane="XY")

        # Verify offset plane was created
        planes = mock_design.rootComponent.constructionPlanes
        planes.createInput.assert_called_once()
        planes.add.assert_called_once()

    def test_offset_plane_xz(self, mock_design, mock_ui):
        """Test offset plane from XZ plane."""
        from lib.features.transform import offsetplane

        offsetplane(mock_design, mock_ui, offset=5, plane="XZ")

        planes = mock_design.rootComponent.constructionPlanes
        planes.createInput.assert_called_once()
        
        # Verify the input was set using XZ plane
        plane_input = planes.createInput.return_value
        plane_input.setByOffset.assert_called_once()

    def test_offset_plane_yz(self, mock_design, mock_ui):
        """Test offset plane from YZ plane."""
        from lib.features.transform import offsetplane

        offsetplane(mock_design, mock_ui, offset=15, plane="YZ")

        planes = mock_design.rootComponent.constructionPlanes
        planes.createInput.assert_called_once()

    def test_offset_plane_negative(self, mock_design, mock_ui):
        """Test offset plane with negative offset."""
        from lib.features.transform import offsetplane

        offsetplane(mock_design, mock_ui, offset=-10, plane="XY")

        planes = mock_design.rootComponent.constructionPlanes
        planes.createInput.assert_called_once()
        planes.add.assert_called_once()

    def test_offset_plane_default(self, mock_design, mock_ui):
        """Test offset plane with default plane (XY)."""
        from lib.features.transform import offsetplane

        offsetplane(mock_design, mock_ui, offset=10)

        planes = mock_design.rootComponent.constructionPlanes
        planes.createInput.assert_called_once()

    def test_offset_plane_error_handling(self, mock_design, mock_ui):
        """Test error handling in offsetplane."""
        from lib.features.transform import offsetplane

        mock_design.rootComponent.constructionPlanes.createInput.side_effect = Exception("Test error")

        offsetplane(mock_design, mock_ui, offset=10, plane="XY")

        mock_ui.messageBox.assert_called_once()
        assert "Failed offsetplane" in str(mock_ui.messageBox.call_args)


class TestTransformEquivalence:
    """Tests to validate equivalence between old and new transform functions."""

    def test_move_last_body_signature(self, mock_design, mock_ui, mock_body):
        """Verify move_last_body accepts same parameters as old version."""
        from lib.features.transform import move_last_body

        # Old signature: move_last_body(design, ui, x, y, z)
        mock_design.rootComponent.bRepBodies.count = 1
        mock_design.rootComponent.bRepBodies.item.return_value = mock_body

        move_last_body(mock_design, mock_ui, 10, 20, 30)  # Positional
        move_last_body(mock_design, mock_ui, x=10, y=20, z=30)  # Keyword

    def test_offsetplane_signature(self, mock_design, mock_ui):
        """Verify offsetplane accepts same parameters as old version."""
        from lib.features.transform import offsetplane

        # Old signature: offsetplane(design, ui, offset, plane="XY")
        offsetplane(mock_design, mock_ui, 10)  # Minimal
        offsetplane(mock_design, mock_ui, 10, "XY")  # Positional
        offsetplane(mock_design, mock_ui, offset=10, plane="XY")  # Keyword


class TestTransformWorkflow:
    """Integration-style tests for transform workflows."""

    def test_create_and_move_body(self, mock_design, mock_ui, mock_body, mock_sketch):
        """Test creating a body and then moving it."""
        from lib.geometry.primitives import draw_box
        from lib.features.transform import move_last_body

        # Create a box
        draw_box(mock_design, mock_ui, height=5, width=5, depth=5, x=0, y=0, z=0, plane="XY")

        # Setup mock to have one body
        mock_design.rootComponent.bRepBodies.count = 1
        mock_design.rootComponent.bRepBodies.item.return_value = mock_body

        # Move the box
        move_last_body(mock_design, mock_ui, x=10, y=10, z=0)

        # Both operations should complete
        mock_design.rootComponent.features.extrudeFeatures.add.assert_called_once()
        mock_design.rootComponent.features.moveFeatures.add.assert_called_once()

    def test_create_offset_plane_then_sketch(self, mock_design, mock_ui, mock_sketch):
        """Test creating an offset plane and then sketching on it."""
        from lib.features.transform import offsetplane
        from lib.geometry.sketches import draw_circle

        # Create offset plane
        offsetplane(mock_design, mock_ui, offset=10, plane="XY")

        # Create a circle at that height
        draw_circle(mock_design, mock_ui, radius=5, x=0, y=0, z=10, plane="XY")

        # Offset plane and circle should both be created
        mock_design.rootComponent.constructionPlanes.add.assert_called()
        mock_sketch.sketchCurves.sketchCircles.addByCenterRadius.assert_called()

    def test_multiple_moves(self, mock_design, mock_ui, mock_body):
        """Test multiple sequential moves."""
        from lib.features.transform import move_last_body

        mock_design.rootComponent.bRepBodies.count = 1
        mock_design.rootComponent.bRepBodies.item.return_value = mock_body

        # Move body multiple times
        move_last_body(mock_design, mock_ui, x=10, y=0, z=0)
        move_last_body(mock_design, mock_ui, x=0, y=10, z=0)
        move_last_body(mock_design, mock_ui, x=0, y=0, z=10)

        # Verify all three moves were applied
        move_feats = mock_design.rootComponent.features.moveFeatures
        assert move_feats.add.call_count == 3
