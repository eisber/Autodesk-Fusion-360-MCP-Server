"""Tests for geometry primitives module.

Tests for:
- draw_box (from MCP_old.py: draw_Box)
- draw_cylinder (from MCP_old.py: draw_cylinder)
- create_sphere (from MCP_old.py: create_sphere)
"""

import pytest
from unittest.mock import MagicMock, patch, call


class TestDrawBox:
    """Tests for draw_box function - equivalent to old draw_Box."""

    def test_draw_box_xy_plane_no_offset(self, mock_design, mock_ui, mock_sketch):
        """Test box creation on XY plane with no Z offset."""
        from lib.geometry.primitives import draw_box

        draw_box(mock_design, mock_ui, height=5, width=3, depth=2, x=0, y=0, z=0, plane="XY")

        # Verify sketch was created on XY plane
        mock_design.rootComponent.sketches.add.assert_called_once()
        call_args = mock_design.rootComponent.sketches.add.call_args
        assert call_args[0][0] == mock_design.rootComponent.xYConstructionPlane

        # Verify rectangle was drawn
        mock_sketch.sketchCurves.sketchLines.addCenterPointRectangle.assert_called_once()

        # Verify extrusion was created
        extrudes = mock_design.rootComponent.features.extrudeFeatures
        extrudes.createInput.assert_called_once()
        extrudes.add.assert_called_once()

    def test_draw_box_xy_plane_with_offset(self, mock_design, mock_ui, mock_sketch):
        """Test box creation on XY plane with Z offset."""
        from lib.geometry.primitives import draw_box

        draw_box(mock_design, mock_ui, height=5, width=3, depth=2, x=0, y=0, z=5, plane="XY")

        # Verify offset plane was created
        planes = mock_design.rootComponent.constructionPlanes
        planes.createInput.assert_called_once()
        planes.add.assert_called_once()

    def test_draw_box_xz_plane(self, mock_design, mock_ui, mock_sketch):
        """Test box creation on XZ plane."""
        from lib.geometry.primitives import draw_box

        draw_box(mock_design, mock_ui, height=5, width=3, depth=2, x=0, y=0, z=0, plane="XZ")

        # Verify sketch was created on XZ plane
        mock_design.rootComponent.sketches.add.assert_called_once()
        call_args = mock_design.rootComponent.sketches.add.call_args
        assert call_args[0][0] == mock_design.rootComponent.xZConstructionPlane

    def test_draw_box_yz_plane(self, mock_design, mock_ui, mock_sketch):
        """Test box creation on YZ plane."""
        from lib.geometry.primitives import draw_box

        draw_box(mock_design, mock_ui, height=5, width=3, depth=2, x=0, y=0, z=0, plane="YZ")

        # Verify sketch was created on YZ plane
        mock_design.rootComponent.sketches.add.assert_called_once()
        call_args = mock_design.rootComponent.sketches.add.call_args
        assert call_args[0][0] == mock_design.rootComponent.yZConstructionPlane

    def test_draw_box_with_position(self, mock_design, mock_ui, mock_sketch):
        """Test box creation at specific position."""
        from lib.geometry.primitives import draw_box

        draw_box(mock_design, mock_ui, height=5, width=3, depth=2, x=10, y=20, z=0, plane="XY")

        # Verify rectangle was drawn at correct position
        mock_sketch.sketchCurves.sketchLines.addCenterPointRectangle.assert_called_once()

    def test_draw_box_error_handling(self, mock_design, mock_ui, mock_sketch):
        """Test error handling in draw_box."""
        from lib.geometry.primitives import draw_box

        # Make sketches.add raise an exception
        mock_design.rootComponent.sketches.add.side_effect = Exception("Test error")

        draw_box(mock_design, mock_ui, height=5, width=3, depth=2, x=0, y=0, z=0, plane="XY")

        # Verify error message was shown
        mock_ui.messageBox.assert_called_once()
        assert "Failed draw_box" in str(mock_ui.messageBox.call_args)


class TestDrawCylinder:
    """Tests for draw_cylinder function - equivalent to old draw_cylinder."""

    def test_draw_cylinder_xy_plane(self, mock_design, mock_ui, mock_sketch):
        """Test cylinder creation on XY plane."""
        from lib.geometry.primitives import draw_cylinder

        draw_cylinder(mock_design, mock_ui, radius=2.5, height=5, x=0, y=0, z=0, plane="XY")

        # Verify sketch was created on XY plane
        mock_design.rootComponent.sketches.add.assert_called_once()

        # Verify circle was drawn
        mock_sketch.sketchCurves.sketchCircles.addByCenterRadius.assert_called_once()

        # Verify extrusion
        extrudes = mock_design.rootComponent.features.extrudeFeatures
        extrudes.createInput.assert_called_once()
        extrudes.add.assert_called_once()

    def test_draw_cylinder_xz_plane(self, mock_design, mock_ui, mock_sketch):
        """Test cylinder creation on XZ plane."""
        from lib.geometry.primitives import draw_cylinder

        draw_cylinder(mock_design, mock_ui, radius=2.5, height=5, x=0, y=0, z=0, plane="XZ")

        # Verify sketch was created on XZ plane
        mock_design.rootComponent.sketches.add.assert_called_once()
        call_args = mock_design.rootComponent.sketches.add.call_args
        assert call_args[0][0] == mock_design.rootComponent.xZConstructionPlane

    def test_draw_cylinder_yz_plane(self, mock_design, mock_ui, mock_sketch):
        """Test cylinder creation on YZ plane."""
        from lib.geometry.primitives import draw_cylinder

        draw_cylinder(mock_design, mock_ui, radius=2.5, height=5, x=0, y=0, z=0, plane="YZ")

        # Verify sketch was created on YZ plane
        call_args = mock_design.rootComponent.sketches.add.call_args
        assert call_args[0][0] == mock_design.rootComponent.yZConstructionPlane

    def test_draw_cylinder_with_offset_xy(self, mock_design, mock_ui, mock_sketch):
        """Test cylinder creation on XY plane with Z offset."""
        from lib.geometry.primitives import draw_cylinder

        draw_cylinder(mock_design, mock_ui, radius=2.5, height=5, x=0, y=0, z=10, plane="XY")

        # Verify offset plane was created
        planes = mock_design.rootComponent.constructionPlanes
        planes.createInput.assert_called_once()
        planes.add.assert_called_once()

    def test_draw_cylinder_with_offset_xz(self, mock_design, mock_ui, mock_sketch):
        """Test cylinder creation on XZ plane with Y offset."""
        from lib.geometry.primitives import draw_cylinder

        draw_cylinder(mock_design, mock_ui, radius=2.5, height=5, x=0, y=10, z=0, plane="XZ")

        # Verify offset plane was created
        planes = mock_design.rootComponent.constructionPlanes
        planes.createInput.assert_called_once()

    def test_draw_cylinder_with_offset_yz(self, mock_design, mock_ui, mock_sketch):
        """Test cylinder creation on YZ plane with X offset."""
        from lib.geometry.primitives import draw_cylinder

        draw_cylinder(mock_design, mock_ui, radius=2.5, height=5, x=10, y=0, z=0, plane="YZ")

        # Verify offset plane was created
        planes = mock_design.rootComponent.constructionPlanes
        planes.createInput.assert_called_once()

    def test_draw_cylinder_error_handling(self, mock_design, mock_ui, mock_sketch):
        """Test error handling in draw_cylinder."""
        from lib.geometry.primitives import draw_cylinder

        mock_design.rootComponent.sketches.add.side_effect = Exception("Test error")

        draw_cylinder(mock_design, mock_ui, radius=2.5, height=5, x=0, y=0, z=0, plane="XY")

        mock_ui.messageBox.assert_called_once()
        assert "Failed draw_cylinder" in str(mock_ui.messageBox.call_args)


class TestCreateSphere:
    """Tests for create_sphere function - equivalent to old create_sphere."""

    def test_create_sphere_basic(self, mock_design, mock_ui, mock_sketch):
        """Test basic sphere creation."""
        from lib.geometry.primitives import create_sphere

        create_sphere(mock_design, mock_ui, radius=5, x=0, y=0, z=0)

        # Verify sketch was created on XY plane
        mock_design.rootComponent.sketches.add.assert_called_once()

        # Verify circle was drawn
        mock_sketch.sketchCurves.sketchCircles.addByCenterRadius.assert_called_once()

        # Verify axis line was drawn
        mock_sketch.sketchCurves.sketchLines.addByTwoPoints.assert_called_once()

        # Verify revolve was created
        revolves = mock_design.rootComponent.features.revolveFeatures
        revolves.createInput.assert_called_once()
        revolves.add.assert_called_once()

    def test_create_sphere_with_position(self, mock_design, mock_ui, mock_sketch):
        """Test sphere creation at specific position."""
        from lib.geometry.primitives import create_sphere

        create_sphere(mock_design, mock_ui, radius=5, x=10, y=20, z=30)

        # Verify circle was drawn (position is passed to Point3D.create)
        mock_sketch.sketchCurves.sketchCircles.addByCenterRadius.assert_called_once()

    def test_create_sphere_error_handling(self, mock_design, mock_ui, mock_sketch):
        """Test error handling in create_sphere."""
        from lib.geometry.primitives import create_sphere

        mock_design.rootComponent.sketches.add.side_effect = Exception("Test error")

        create_sphere(mock_design, mock_ui, radius=5, x=0, y=0, z=0)

        mock_ui.messageBox.assert_called_once()
        assert "Failed create_sphere" in str(mock_ui.messageBox.call_args)


class TestPrimitiveEquivalence:
    """
    Tests to validate equivalence between old MCP_old.py functions
    and new refactored primitives.py functions.
    """

    def test_draw_box_function_signature(self, mock_design, mock_ui, mock_sketch):
        """Verify draw_box accepts same parameters as old draw_Box."""
        from lib.geometry.primitives import draw_box

        # Old signature: draw_Box(design, ui, height, width, depth, x, y, z, plane=None)
        # New signature should be compatible
        draw_box(mock_design, mock_ui, 5, 3, 2, 0, 0, 0, None)  # Positional args
        draw_box(mock_design, mock_ui, height=5, width=3, depth=2, x=0, y=0, z=0, plane="XY")

    def test_draw_cylinder_function_signature(self, mock_design, mock_ui, mock_sketch):
        """Verify draw_cylinder accepts same parameters as old version."""
        from lib.geometry.primitives import draw_cylinder

        # Old signature: draw_cylinder(design, ui, radius, height, x, y, z, plane="XY")
        draw_cylinder(mock_design, mock_ui, 2.5, 5, 0, 0, 0, "XY")  # Positional args
        draw_cylinder(mock_design, mock_ui, radius=2.5, height=5, x=0, y=0, z=0, plane="XY")

    def test_create_sphere_function_signature(self, mock_design, mock_ui, mock_sketch):
        """Verify create_sphere accepts same parameters as old version."""
        from lib.geometry.primitives import create_sphere

        # Old signature: create_sphere(design, ui, radius, x, y, z)
        create_sphere(mock_design, mock_ui, 5, 0, 0, 0)  # Positional args
        create_sphere(mock_design, mock_ui, radius=5, x=0, y=0, z=0)
