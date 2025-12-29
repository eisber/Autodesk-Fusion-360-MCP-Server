"""Tests for geometry sketches module.

Tests for:
- draw_circle (from MCP_old.py: draw_circle)
- draw_ellipse (from MCP_old.py: draw_ellipis)
- draw_2d_rectangle (from MCP_old.py: draw_2d_rect)
- draw_lines (from MCP_old.py: draw_lines)
- draw_one_line (from MCP_old.py: draw_one_line)
- draw_arc (from MCP_old.py: arc)
- draw_spline (from MCP_old.py: spline)
- draw_text (from MCP_old.py: draw_text)
"""

import pytest
from unittest.mock import MagicMock, patch, call


class TestDrawCircle:
    """Tests for draw_circle function - equivalent to old draw_circle."""

    def test_draw_circle_xy_plane(self, mock_design, mock_ui, mock_sketch):
        """Test circle creation on XY plane."""
        from lib.geometry.sketches import draw_circle

        draw_circle(mock_design, mock_ui, radius=5, x=0, y=0, z=0, plane="XY")

        # Verify sketch was created on XY plane
        mock_design.rootComponent.sketches.add.assert_called_once()

        # Verify circle was drawn
        mock_sketch.sketchCurves.sketchCircles.addByCenterRadius.assert_called_once()

    def test_draw_circle_xz_plane(self, mock_design, mock_ui, mock_sketch):
        """Test circle creation on XZ plane."""
        from lib.geometry.sketches import draw_circle

        draw_circle(mock_design, mock_ui, radius=5, x=0, y=0, z=0, plane="XZ")

        # Verify sketch was created on XZ plane
        call_args = mock_design.rootComponent.sketches.add.call_args
        assert call_args[0][0] == mock_design.rootComponent.xZConstructionPlane

    def test_draw_circle_yz_plane(self, mock_design, mock_ui, mock_sketch):
        """Test circle creation on YZ plane."""
        from lib.geometry.sketches import draw_circle

        draw_circle(mock_design, mock_ui, radius=5, x=0, y=0, z=0, plane="YZ")

        # Verify sketch was created on YZ plane
        call_args = mock_design.rootComponent.sketches.add.call_args
        assert call_args[0][0] == mock_design.rootComponent.yZConstructionPlane

    def test_draw_circle_with_offset_xy(self, mock_design, mock_ui, mock_sketch):
        """Test circle on XY plane with Z offset creates offset plane."""
        from lib.geometry.sketches import draw_circle

        draw_circle(mock_design, mock_ui, radius=5, x=0, y=0, z=10, plane="XY")

        # Verify offset plane was created
        planes = mock_design.rootComponent.constructionPlanes
        planes.createInput.assert_called_once()

    def test_draw_circle_with_offset_xz(self, mock_design, mock_ui, mock_sketch):
        """Test circle on XZ plane with Y offset creates offset plane."""
        from lib.geometry.sketches import draw_circle

        draw_circle(mock_design, mock_ui, radius=5, x=0, y=10, z=0, plane="XZ")

        # Verify offset plane was created
        planes = mock_design.rootComponent.constructionPlanes
        planes.createInput.assert_called_once()

    def test_draw_circle_with_offset_yz(self, mock_design, mock_ui, mock_sketch):
        """Test circle on YZ plane with X offset creates offset plane."""
        from lib.geometry.sketches import draw_circle

        draw_circle(mock_design, mock_ui, radius=5, x=10, y=0, z=0, plane="YZ")

        # Verify offset plane was created
        planes = mock_design.rootComponent.constructionPlanes
        planes.createInput.assert_called_once()

    def test_draw_circle_error_handling(self, mock_design, mock_ui, mock_sketch):
        """Test error handling in draw_circle."""
        from lib.geometry.sketches import draw_circle

        mock_design.rootComponent.sketches.add.side_effect = Exception("Test error")

        draw_circle(mock_design, mock_ui, radius=5, x=0, y=0, z=0, plane="XY")

        mock_ui.messageBox.assert_called_once()
        assert "Failed draw_circle" in str(mock_ui.messageBox.call_args)


class TestDrawEllipse:
    """Tests for draw_ellipse function - equivalent to old draw_ellipis."""

    def test_draw_ellipse_xy_plane(self, mock_design, mock_ui, mock_sketch):
        """Test ellipse creation on XY plane."""
        from lib.geometry.sketches import draw_ellipse

        draw_ellipse(
            mock_design, mock_ui,
            x_center=0, y_center=0, z_center=0,
            x_major=5, y_major=0, z_major=0,
            x_through=0, y_through=3, z_through=0,
            plane="XY"
        )

        # Verify sketch was created on XY plane
        mock_design.rootComponent.sketches.add.assert_called_once()

        # Verify ellipse was drawn
        mock_sketch.sketchCurves.sketchEllipses.add.assert_called_once()

    def test_draw_ellipse_xz_plane(self, mock_design, mock_ui, mock_sketch):
        """Test ellipse creation on XZ plane."""
        from lib.geometry.sketches import draw_ellipse

        draw_ellipse(
            mock_design, mock_ui,
            x_center=0, y_center=0, z_center=0,
            x_major=5, y_major=0, z_major=0,
            x_through=0, y_through=0, z_through=3,
            plane="XZ"
        )

        call_args = mock_design.rootComponent.sketches.add.call_args
        assert call_args[0][0] == mock_design.rootComponent.xZConstructionPlane

    def test_draw_ellipse_yz_plane(self, mock_design, mock_ui, mock_sketch):
        """Test ellipse creation on YZ plane."""
        from lib.geometry.sketches import draw_ellipse

        draw_ellipse(
            mock_design, mock_ui,
            x_center=0, y_center=0, z_center=0,
            x_major=0, y_major=5, z_major=0,
            x_through=0, y_through=0, z_through=3,
            plane="YZ"
        )

        call_args = mock_design.rootComponent.sketches.add.call_args
        assert call_args[0][0] == mock_design.rootComponent.yZConstructionPlane

    def test_draw_ellipse_error_handling(self, mock_design, mock_ui, mock_sketch):
        """Test error handling in draw_ellipse."""
        from lib.geometry.sketches import draw_ellipse

        mock_design.rootComponent.sketches.add.side_effect = Exception("Test error")

        draw_ellipse(
            mock_design, mock_ui,
            x_center=0, y_center=0, z_center=0,
            x_major=5, y_major=0, z_major=0,
            x_through=0, y_through=3, z_through=0,
            plane="XY"
        )

        mock_ui.messageBox.assert_called_once()
        assert "Failed draw_ellipse" in str(mock_ui.messageBox.call_args)


class TestDraw2DRectangle:
    """Tests for draw_2d_rectangle function - equivalent to old draw_2d_rect."""

    def test_draw_2d_rectangle_xy_plane(self, mock_design, mock_ui, mock_sketch):
        """Test 2D rectangle creation on XY plane."""
        from lib.geometry.sketches import draw_2d_rectangle

        draw_2d_rectangle(
            mock_design, mock_ui,
            x_1=0, y_1=0, z_1=0,
            x_2=5, y_2=5, z_2=0,
            plane="XY"
        )

        # Verify sketch was created
        mock_design.rootComponent.sketches.add.assert_called_once()

        # Verify rectangle was drawn
        mock_sketch.sketchCurves.sketchLines.addTwoPointRectangle.assert_called_once()

    def test_draw_2d_rectangle_with_z_offset(self, mock_design, mock_ui, mock_sketch):
        """Test 2D rectangle with Z offset creates offset plane."""
        from lib.geometry.sketches import draw_2d_rectangle

        draw_2d_rectangle(
            mock_design, mock_ui,
            x_1=0, y_1=0, z_1=5,
            x_2=10, y_2=10, z_2=5,
            plane="XY"
        )

        # Verify offset plane was created
        planes = mock_design.rootComponent.constructionPlanes
        planes.createInput.assert_called_once()

    def test_draw_2d_rectangle_xz_plane(self, mock_design, mock_ui, mock_sketch):
        """Test 2D rectangle creation on XZ plane."""
        from lib.geometry.sketches import draw_2d_rectangle

        draw_2d_rectangle(
            mock_design, mock_ui,
            x_1=0, y_1=0, z_1=0,
            x_2=5, y_2=0, z_2=5,
            plane="XZ"
        )

        call_args = mock_design.rootComponent.sketches.add.call_args
        assert call_args[0][0] == mock_design.rootComponent.xZConstructionPlane

    def test_draw_2d_rectangle_error_handling(self, mock_design, mock_ui, mock_sketch):
        """Test error handling in draw_2d_rectangle."""
        from lib.geometry.sketches import draw_2d_rectangle

        mock_design.rootComponent.sketches.add.side_effect = Exception("Test error")

        draw_2d_rectangle(
            mock_design, mock_ui,
            x_1=0, y_1=0, z_1=0,
            x_2=5, y_2=5, z_2=0,
            plane="XY"
        )

        mock_ui.messageBox.assert_called_once()
        assert "Failed draw_2d_rectangle" in str(mock_ui.messageBox.call_args)


class TestDrawLines:
    """Tests for draw_lines function - equivalent to old draw_lines."""

    def test_draw_lines_xy_plane(self, mock_design, mock_ui, mock_sketch):
        """Test line drawing on XY plane."""
        from lib.geometry.sketches import draw_lines

        points = [[0, 0, 0], [5, 0, 0], [5, 5, 0], [0, 5, 0], [0, 0, 0]]
        draw_lines(mock_design, mock_ui, points, plane="XY")

        # Verify sketch was created
        mock_design.rootComponent.sketches.add.assert_called_once()

        # Verify lines were drawn (4 lines for 5 points - closing the shape)
        # The function draws lines connecting consecutive points and closes the shape
        assert mock_sketch.sketchCurves.sketchLines.addByTwoPoints.call_count >= 4

    def test_draw_lines_xz_plane(self, mock_design, mock_ui, mock_sketch):
        """Test line drawing on XZ plane."""
        from lib.geometry.sketches import draw_lines

        points = [[0, 0, 0], [5, 0, 0], [5, 0, 5]]
        draw_lines(mock_design, mock_ui, points, plane="XZ")

        call_args = mock_design.rootComponent.sketches.add.call_args
        assert call_args[0][0] == mock_design.rootComponent.xZConstructionPlane

    def test_draw_lines_yz_plane(self, mock_design, mock_ui, mock_sketch):
        """Test line drawing on YZ plane."""
        from lib.geometry.sketches import draw_lines

        points = [[0, 0, 0], [0, 5, 0], [0, 5, 5]]
        draw_lines(mock_design, mock_ui, points, plane="YZ")

        call_args = mock_design.rootComponent.sketches.add.call_args
        assert call_args[0][0] == mock_design.rootComponent.yZConstructionPlane

    def test_draw_lines_error_handling(self, mock_design, mock_ui, mock_sketch):
        """Test error handling in draw_lines."""
        from lib.geometry.sketches import draw_lines

        mock_design.rootComponent.sketches.add.side_effect = Exception("Test error")

        points = [[0, 0, 0], [5, 0, 0]]
        draw_lines(mock_design, mock_ui, points, plane="XY")

        mock_ui.messageBox.assert_called_once()
        assert "Failed draw_lines" in str(mock_ui.messageBox.call_args)


class TestDrawOneLine:
    """Tests for draw_one_line function - equivalent to old draw_one_line."""

    def test_draw_one_line_basic(self, mock_design, mock_ui, mock_sketch):
        """Test drawing a single line in existing sketch."""
        from lib.geometry.sketches import draw_one_line

        # Setup mock to return the sketch when getting last sketch
        mock_design.rootComponent.sketches.count = 1
        mock_design.rootComponent.sketches.item.return_value = mock_sketch

        draw_one_line(mock_design, mock_ui, x1=0, y1=0, z1=0, x2=5, y2=5, z2=0, plane="XY")

        # Verify line was drawn in existing sketch (not creating new sketch)
        # The sketch.item is called to get the last sketch
        mock_design.rootComponent.sketches.item.assert_called()

    def test_draw_one_line_error_handling(self, mock_design, mock_ui, mock_sketch):
        """Test error handling in draw_one_line."""
        from lib.geometry.sketches import draw_one_line

        mock_design.rootComponent.sketches.item.side_effect = Exception("Test error")

        draw_one_line(mock_design, mock_ui, x1=0, y1=0, z1=0, x2=5, y2=5, z2=0, plane="XY")

        mock_ui.messageBox.assert_called_once()
        assert "Failed draw_one_line" in str(mock_ui.messageBox.call_args)


class TestDrawArc:
    """Tests for draw_arc function - equivalent to old arc."""

    def test_draw_arc_xy_plane(self, mock_design, mock_ui, mock_sketch):
        """Test arc creation on XY plane."""
        from lib.geometry.sketches import draw_arc

        point1 = [0, 0, 0]
        point2 = [2.5, 2.5, 0]  # Along point
        point3 = [5, 0, 0]

        draw_arc(mock_design, mock_ui, point1, point2, point3, connect=False, plane="XY")

        # Verify sketch was created
        mock_design.rootComponent.sketches.add.assert_called_once()

        # Verify arc was drawn
        mock_sketch.sketchCurves.sketchArcs.addByThreePoints.assert_called_once()

    def test_draw_arc_with_connect(self, mock_design, mock_ui, mock_sketch):
        """Test arc creation with connecting line."""
        from lib.geometry.sketches import draw_arc

        point1 = [0, 0, 0]
        point2 = [2.5, 2.5, 0]
        point3 = [5, 0, 0]

        draw_arc(mock_design, mock_ui, point1, point2, point3, connect=True, plane="XY")

        # Verify arc was drawn
        mock_sketch.sketchCurves.sketchArcs.addByThreePoints.assert_called_once()

        # Verify connecting line was drawn
        mock_sketch.sketchCurves.sketchLines.addByTwoPoints.assert_called_once()

    def test_draw_arc_xz_plane(self, mock_design, mock_ui, mock_sketch):
        """Test arc creation on XZ plane."""
        from lib.geometry.sketches import draw_arc

        point1 = [0, 0, 0]
        point2 = [2.5, 0, 2.5]
        point3 = [5, 0, 0]

        draw_arc(mock_design, mock_ui, point1, point2, point3, connect=False, plane="XZ")

        call_args = mock_design.rootComponent.sketches.add.call_args
        assert call_args[0][0] == mock_design.rootComponent.xZConstructionPlane

    def test_draw_arc_error_handling(self, mock_design, mock_ui, mock_sketch):
        """Test error handling in draw_arc."""
        from lib.geometry.sketches import draw_arc

        mock_design.rootComponent.sketches.add.side_effect = Exception("Test error")

        draw_arc(mock_design, mock_ui, [0, 0, 0], [2.5, 2.5, 0], [5, 0, 0], connect=False, plane="XY")

        mock_ui.messageBox.assert_called_once()
        assert "Failed draw_arc" in str(mock_ui.messageBox.call_args)


class TestDrawSpline:
    """Tests for draw_spline function - equivalent to old spline."""

    def test_draw_spline_xy_plane(self, mock_design, mock_ui, mock_sketch):
        """Test spline creation on XY plane."""
        from lib.geometry.sketches import draw_spline

        points = [[0, 0, 0], [2, 3, 0], [5, 2, 0], [7, 5, 0]]
        draw_spline(mock_design, mock_ui, points, plane="XY")

        # Verify sketch was created
        mock_design.rootComponent.sketches.add.assert_called_once()

        # Verify spline was drawn
        mock_sketch.sketchCurves.sketchFittedSplines.add.assert_called_once()

    def test_draw_spline_xz_plane(self, mock_design, mock_ui, mock_sketch):
        """Test spline creation on XZ plane."""
        from lib.geometry.sketches import draw_spline

        points = [[0, 0, 0], [2, 0, 3], [5, 0, 2]]
        draw_spline(mock_design, mock_ui, points, plane="XZ")

        call_args = mock_design.rootComponent.sketches.add.call_args
        assert call_args[0][0] == mock_design.rootComponent.xZConstructionPlane

    def test_draw_spline_yz_plane(self, mock_design, mock_ui, mock_sketch):
        """Test spline creation on YZ plane."""
        from lib.geometry.sketches import draw_spline

        points = [[0, 0, 0], [0, 2, 3], [0, 5, 2]]
        draw_spline(mock_design, mock_ui, points, plane="YZ")

        call_args = mock_design.rootComponent.sketches.add.call_args
        assert call_args[0][0] == mock_design.rootComponent.yZConstructionPlane

    def test_draw_spline_error_handling(self, mock_design, mock_ui, mock_sketch):
        """Test error handling in draw_spline."""
        from lib.geometry.sketches import draw_spline

        mock_design.rootComponent.sketches.add.side_effect = Exception("Test error")

        draw_spline(mock_design, mock_ui, [[0, 0, 0], [5, 5, 0]], plane="XY")

        mock_ui.messageBox.assert_called_once()
        assert "Failed draw_spline" in str(mock_ui.messageBox.call_args)


class TestDrawText:
    """Tests for draw_text function - equivalent to old draw_text."""

    def test_draw_text_xy_plane(self, mock_design, mock_ui, mock_sketch):
        """Test text creation on XY plane."""
        from lib.geometry.sketches import draw_text

        draw_text(
            mock_design, mock_ui,
            text="Hello",
            thickness=0.5,
            x_1=0, y_1=0, z_1=0,
            x_2=10, y_2=5, z_2=0,
            value=2,
            plane="XY"
        )

        # Verify sketch was created
        mock_design.rootComponent.sketches.add.assert_called_once()

        # Verify text was created
        mock_sketch.sketchTexts.createInput2.assert_called_once_with("Hello", 0.5)
        mock_sketch.sketchTexts.add.assert_called_once()

        # Verify extrusion was created
        extrudes = mock_design.rootComponent.features.extrudeFeatures
        extrudes.createInput.assert_called_once()
        extrudes.add.assert_called_once()

    def test_draw_text_xz_plane(self, mock_design, mock_ui, mock_sketch):
        """Test text creation on XZ plane."""
        from lib.geometry.sketches import draw_text

        draw_text(
            mock_design, mock_ui,
            text="Test",
            thickness=0.5,
            x_1=0, y_1=0, z_1=0,
            x_2=10, y_2=0, z_2=5,
            value=2,
            plane="XZ"
        )

        call_args = mock_design.rootComponent.sketches.add.call_args
        assert call_args[0][0] == mock_design.rootComponent.xZConstructionPlane

    def test_draw_text_error_handling(self, mock_design, mock_ui, mock_sketch):
        """Test error handling in draw_text."""
        from lib.geometry.sketches import draw_text

        mock_design.rootComponent.sketches.add.side_effect = Exception("Test error")

        draw_text(
            mock_design, mock_ui,
            text="Error",
            thickness=0.5,
            x_1=0, y_1=0, z_1=0,
            x_2=10, y_2=5, z_2=0,
            value=2,
            plane="XY"
        )

        mock_ui.messageBox.assert_called_once()
        assert "Failed draw_text" in str(mock_ui.messageBox.call_args)


class TestSketchEquivalence:
    """Tests to validate equivalence between old and new sketch functions."""

    def test_draw_circle_signature(self, mock_design, mock_ui, mock_sketch):
        """Verify draw_circle accepts same parameters as old version."""
        from lib.geometry.sketches import draw_circle

        # Old signature: draw_circle(design, ui, radius, x, y, z, plane="XY")
        draw_circle(mock_design, mock_ui, 5, 0, 0, 0, "XY")  # Positional
        draw_circle(mock_design, mock_ui, radius=5, x=0, y=0, z=0, plane="XY")  # Keyword

    def test_draw_lines_signature(self, mock_design, mock_ui, mock_sketch):
        """Verify draw_lines accepts same parameters as old version."""
        from lib.geometry.sketches import draw_lines

        # Old signature: draw_lines(design, ui, points, Plane="XY")
        # Note: parameter name changed from 'Plane' to 'plane' for consistency
        points = [[0, 0, 0], [5, 0, 0], [5, 5, 0]]
        draw_lines(mock_design, mock_ui, points, "XY")
        draw_lines(mock_design, mock_ui, points=points, plane="XY")

    def test_draw_arc_signature(self, mock_design, mock_ui, mock_sketch):
        """Verify draw_arc accepts same parameters as old arc function."""
        from lib.geometry.sketches import draw_arc

        # Old signature: arc(design, ui, point1, point2, points3, plane="XY", connect=False)
        # New signature: draw_arc(design, ui, point1, point2, point3, connect, plane="XY")
        draw_arc(mock_design, mock_ui, [0, 0, 0], [2.5, 2.5, 0], [5, 0, 0], False, "XY")
        draw_arc(mock_design, mock_ui, point1=[0, 0, 0], point2=[2.5, 2.5, 0], point3=[5, 0, 0], connect=False, plane="XY")

    def test_draw_spline_signature(self, mock_design, mock_ui, mock_sketch):
        """Verify draw_spline accepts same parameters as old spline function."""
        from lib.geometry.sketches import draw_spline

        # Old signature: spline(design, ui, points, plane="XY")
        points = [[0, 0, 0], [5, 5, 0], [10, 0, 0]]
        draw_spline(mock_design, mock_ui, points, "XY")
        draw_spline(mock_design, mock_ui, points=points, plane="XY")
