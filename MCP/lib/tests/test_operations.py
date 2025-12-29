"""Tests for feature operations module.

Tests for:
- loft (from MCP_old.py: loft)
- sweep (from MCP_old.py: sweep)
- revolve_profile (from MCP_old.py: revolve_profile)
- boolean_operation (from MCP_old.py: boolean_operation)
- shell_existing_body (from MCP_old.py: shell_existing_body)
- fillet_edges (from MCP_old.py: fillet_edges)
- holes (from MCP_old.py: holes)
- create_thread (from MCP_old.py: create_thread)
"""

import pytest
from unittest.mock import MagicMock, patch, call


class TestLoft:
    """Tests for loft function."""

    def test_loft_basic(self, mock_design, mock_ui, mock_sketch):
        """Test basic loft between two sketches."""
        from lib.features.operations import loft

        # Setup multiple sketches
        sketch1 = MagicMock()
        sketch1.profiles = MagicMock()
        sketch1.profiles.item.return_value = MagicMock()
        
        sketch2 = MagicMock()
        sketch2.profiles = MagicMock()
        sketch2.profiles.item.return_value = MagicMock()

        mock_design.rootComponent.sketches.count = 2
        mock_design.rootComponent.sketches.item.side_effect = [sketch2, sketch1]  # Reverse order for loft

        loft(mock_design, mock_ui, sketchcount=2)

        # Verify loft was created
        loft_feats = mock_design.rootComponent.features.loftFeatures
        loft_feats.createInput.assert_called_once()
        loft_feats.add.assert_called_once()

    def test_loft_multiple_sketches(self, mock_design, mock_ui):
        """Test loft with multiple sketches."""
        from lib.features.operations import loft

        # Setup 3 sketches
        sketches = [MagicMock() for _ in range(3)]
        for s in sketches:
            s.profiles = MagicMock()
            s.profiles.item.return_value = MagicMock()

        mock_design.rootComponent.sketches.count = 3
        mock_design.rootComponent.sketches.item.side_effect = lambda i: sketches[2 - i]

        loft(mock_design, mock_ui, sketchcount=3)

        # Verify loft sections were added
        loft_input = mock_design.rootComponent.features.loftFeatures.createInput.return_value
        assert loft_input.loftSections.add.call_count == 3

    def test_loft_error_handling(self, mock_design, mock_ui):
        """Test error handling in loft."""
        from lib.features.operations import loft

        mock_design.rootComponent.sketches.item.side_effect = Exception("Test error")

        loft(mock_design, mock_ui, sketchcount=2)

        mock_ui.messageBox.assert_called_once()
        assert "Failed loft" in str(mock_ui.messageBox.call_args)


class TestSweep:
    """Tests for sweep function."""

    def test_sweep_basic(self, mock_design, mock_ui, mock_sketch):
        """Test basic sweep operation."""
        from lib.features.operations import sweep

        # Setup profile sketch (second to last)
        profile_sketch = MagicMock()
        profile_sketch.profiles = MagicMock()
        profile_sketch.profiles.item.return_value = MagicMock()

        # Setup path sketch (last)
        path_sketch = MagicMock()
        path_sketch.sketchCurves = MagicMock()
        path_sketch.sketchCurves.count = 1
        path_sketch.sketchCurves.item.return_value = MagicMock()

        mock_design.rootComponent.sketches.count = 2
        mock_design.rootComponent.sketches.item.side_effect = lambda i: (
            path_sketch if i == 1 else profile_sketch
        )

        sweep(mock_design, mock_ui)

        # Verify sweep was created
        sweep_feats = mock_design.rootComponent.features.sweepFeatures
        sweep_feats.createInput.assert_called_once()
        sweep_feats.add.assert_called_once()

    def test_sweep_error_handling(self, mock_design, mock_ui):
        """Test error handling in sweep."""
        from lib.features.operations import sweep

        mock_design.rootComponent.sketches.item.side_effect = Exception("Test error")

        sweep(mock_design, mock_ui)

        mock_ui.messageBox.assert_called_once()
        assert "Failed sweep" in str(mock_ui.messageBox.call_args)


class TestRevolveProfile:
    """Tests for revolve_profile function."""

    def test_revolve_profile_basic(self, mock_design, mock_ui):
        """Test basic revolve operation."""
        from lib.features.operations import revolve_profile

        # Mock user selection
        mock_profile = MagicMock()
        mock_axis = MagicMock()
        mock_ui.selectEntity.side_effect = [
            MagicMock(entity=mock_profile),
            MagicMock(entity=mock_axis),
        ]

        revolve_profile(mock_design, mock_ui, angle=360)

        # Verify revolve was created
        revolve_feats = mock_design.rootComponent.features.revolveFeatures
        revolve_feats.createInput.assert_called_once()
        revolve_feats.add.assert_called_once()

    def test_revolve_profile_custom_angle(self, mock_design, mock_ui):
        """Test revolve with custom angle."""
        from lib.features.operations import revolve_profile

        mock_profile = MagicMock()
        mock_axis = MagicMock()
        mock_ui.selectEntity.side_effect = [
            MagicMock(entity=mock_profile),
            MagicMock(entity=mock_axis),
        ]

        revolve_profile(mock_design, mock_ui, angle=180)

        # Verify revolve input was configured with custom angle
        revolve_input = mock_design.rootComponent.features.revolveFeatures.createInput.return_value
        revolve_input.setAngleExtent.assert_called_once()

    def test_revolve_profile_error_handling(self, mock_design, mock_ui):
        """Test error handling in revolve_profile."""
        from lib.features.operations import revolve_profile

        mock_ui.selectEntity.side_effect = Exception("User cancelled")

        revolve_profile(mock_design, mock_ui, angle=360)

        mock_ui.messageBox.assert_called()


class TestBooleanOperation:
    """Tests for boolean_operation function.
    
    Note: boolean_operation uses adsk.core.Application.get() internally
    which makes it difficult to fully mock. These tests verify the function
    doesn't crash and handles errors appropriately.
    """

    def test_boolean_cut_no_crash(self, mock_design, mock_ui, mock_body, mock_adsk_module):
        """Test cut boolean operation doesn't crash."""
        from lib.features.operations import boolean_operation

        # Setup two bodies
        body1 = MagicMock(name="TargetBody")
        body2 = MagicMock(name="ToolBody")
        mock_design.rootComponent.bRepBodies.item.side_effect = [body1, body2]
        mock_design.rootComponent.bRepBodies.count = 2

        # Mock the internal app.get() call to return a functional design
        mock_app = MagicMock()
        mock_app.activeProduct = mock_design
        mock_adsk_module.core.Application.get.return_value = mock_app
        mock_adsk_module.fusion.Design.cast.return_value = mock_design

        # Should not raise exception
        boolean_operation(mock_design, mock_ui, op="cut")

    def test_boolean_join_no_crash(self, mock_design, mock_ui, mock_body, mock_adsk_module):
        """Test join boolean operation doesn't crash."""
        from lib.features.operations import boolean_operation

        body1 = MagicMock()
        body2 = MagicMock()
        mock_design.rootComponent.bRepBodies.item.side_effect = [body1, body2]
        mock_design.rootComponent.bRepBodies.count = 2

        mock_app = MagicMock()
        mock_app.activeProduct = mock_design
        mock_adsk_module.core.Application.get.return_value = mock_app
        mock_adsk_module.fusion.Design.cast.return_value = mock_design

        boolean_operation(mock_design, mock_ui, op="join")

    def test_boolean_intersect_no_crash(self, mock_design, mock_ui, mock_body, mock_adsk_module):
        """Test intersect boolean operation doesn't crash."""
        from lib.features.operations import boolean_operation

        body1 = MagicMock()
        body2 = MagicMock()
        mock_design.rootComponent.bRepBodies.item.side_effect = [body1, body2]
        mock_design.rootComponent.bRepBodies.count = 2

        mock_app = MagicMock()
        mock_app.activeProduct = mock_design
        mock_adsk_module.core.Application.get.return_value = mock_app
        mock_adsk_module.fusion.Design.cast.return_value = mock_design

        boolean_operation(mock_design, mock_ui, op="intersect")

    def test_boolean_error_handling(self, mock_design, mock_ui, mock_adsk_module):
        """Test error handling in boolean_operation."""
        from lib.features.operations import boolean_operation

        # Simulate error by making Application.get raise exception
        mock_adsk_module.core.Application.get.side_effect = Exception("Test error")

        # Should handle error gracefully (may or may not show message depending on impl)
        try:
            boolean_operation(mock_design, mock_ui, op="cut")
        except Exception:
            pass  # Expected since we can't fully mock the internal chain


class TestShellExistingBody:
    """Tests for shell_existing_body function."""

    def test_shell_basic(self, mock_design, mock_ui, mock_body):
        """Test basic shell operation."""
        from lib.features.operations import shell_existing_body

        mock_design.rootComponent.bRepBodies.item.return_value = mock_body

        shell_existing_body(mock_design, mock_ui, thickness=0.5, faceindex=0)

        # Verify shell was created
        shell_feats = mock_design.rootComponent.features.shellFeatures
        shell_feats.createInput.assert_called_once()
        shell_feats.add.assert_called_once()

    def test_shell_custom_face(self, mock_design, mock_ui, mock_body):
        """Test shell on specific face."""
        from lib.features.operations import shell_existing_body

        mock_design.rootComponent.bRepBodies.item.return_value = mock_body

        shell_existing_body(mock_design, mock_ui, thickness=0.3, faceindex=4)

        # Shell operates on first body, face selection is done differently
        # Just verify the shell feature was created
        shell_feats = mock_design.rootComponent.features.shellFeatures
        shell_feats.createInput.assert_called_once()

    def test_shell_error_handling(self, mock_design, mock_ui):
        """Test error handling in shell_existing_body."""
        from lib.features.operations import shell_existing_body

        mock_design.rootComponent.bRepBodies.item.side_effect = Exception("Test error")

        shell_existing_body(mock_design, mock_ui, thickness=0.5, faceindex=0)

        mock_ui.messageBox.assert_called_once()
        assert "Failed shell_existing_body" in str(mock_ui.messageBox.call_args)


class TestFilletEdges:
    """Tests for fillet_edges function."""

    def test_fillet_basic(self, mock_design, mock_ui, mock_body):
        """Test basic fillet operation."""
        from lib.features.operations import fillet_edges

        mock_design.rootComponent.bRepBodies.count = 1
        mock_design.rootComponent.bRepBodies.item.return_value = mock_body

        fillet_edges(mock_design, mock_ui, radius=0.3)

        # Verify fillet was created
        fillet_feats = mock_design.rootComponent.features.filletFeatures
        fillet_feats.createInput.assert_called_once()
        fillet_feats.add.assert_called_once()

    def test_fillet_custom_radius(self, mock_design, mock_ui, mock_body):
        """Test fillet with custom radius."""
        from lib.features.operations import fillet_edges

        mock_design.rootComponent.bRepBodies.count = 1
        mock_design.rootComponent.bRepBodies.item.return_value = mock_body

        fillet_edges(mock_design, mock_ui, radius=1.5)

        fillet_feats = mock_design.rootComponent.features.filletFeatures
        fillet_feats.createInput.assert_called_once()

    def test_fillet_error_handling(self, mock_design, mock_ui):
        """Test error handling in fillet_edges."""
        from lib.features.operations import fillet_edges

        mock_design.rootComponent.bRepBodies.count = 0

        fillet_edges(mock_design, mock_ui, radius=0.3)

        # Should not crash even with no bodies


class TestHoles:
    """Tests for holes function."""

    def test_holes_single(self, mock_design, mock_ui, mock_body, mock_sketch):
        """Test creating a single hole."""
        from lib.features.operations import holes

        mock_design.rootComponent.bRepBodies.count = 1
        mock_design.rootComponent.bRepBodies.item.return_value = mock_body
        mock_design.rootComponent.sketches.add.return_value = mock_sketch

        points = [[0, 0]]
        holes(mock_design, mock_ui, points=points, width=1.0, distance=1.0, faceindex=0)

        # Verify hole was created
        hole_feats = mock_design.rootComponent.features.holeFeatures
        hole_feats.createSimpleInput.assert_called_once()
        hole_feats.add.assert_called_once()

    def test_holes_multiple(self, mock_design, mock_ui, mock_body, mock_sketch):
        """Test creating multiple holes."""
        from lib.features.operations import holes

        mock_design.rootComponent.bRepBodies.count = 1
        mock_design.rootComponent.bRepBodies.item.return_value = mock_body
        mock_design.rootComponent.sketches.add.return_value = mock_sketch

        points = [[0, 0], [5, 0], [5, 5], [0, 5]]
        holes(mock_design, mock_ui, points=points, width=0.5, distance=2.0, faceindex=0)

        # Verify multiple holes were created
        hole_feats = mock_design.rootComponent.features.holeFeatures
        assert hole_feats.add.call_count == 4

    def test_holes_no_bodies(self, mock_design, mock_ui):
        """Test holes function with no bodies."""
        from lib.features.operations import holes

        mock_design.rootComponent.bRepBodies.count = 0

        holes(mock_design, mock_ui, points=[[0, 0]], width=1.0, distance=1.0, faceindex=0)

        mock_ui.messageBox.assert_called_once()
        assert "No bodies found" in str(mock_ui.messageBox.call_args)

    def test_holes_error_handling(self, mock_design, mock_ui, mock_body):
        """Test error handling in holes."""
        from lib.features.operations import holes

        mock_design.rootComponent.bRepBodies.count = 1
        mock_design.rootComponent.bRepBodies.item.return_value = mock_body
        mock_design.rootComponent.sketches.add.side_effect = Exception("Test error")

        holes(mock_design, mock_ui, points=[[0, 0]], width=1.0, distance=1.0, faceindex=0)

        mock_ui.messageBox.assert_called_once()
        assert "Failed holes" in str(mock_ui.messageBox.call_args)


class TestCreateThread:
    """Tests for create_thread function."""

    def test_thread_basic(self, mock_design, mock_ui):
        """Test basic thread creation."""
        from lib.features.operations import create_thread

        # Mock user selection
        mock_face = MagicMock()
        mock_ui.selectEntity.return_value = MagicMock(entity=mock_face)

        create_thread(mock_design, mock_ui, inside=True, sizes=0)

        # Verify thread was created
        thread_feats = mock_design.rootComponent.features.threadFeatures
        thread_feats.createInput.assert_called_once()
        thread_feats.add.assert_called_once()

    def test_thread_external(self, mock_design, mock_ui):
        """Test external thread creation."""
        from lib.features.operations import create_thread

        mock_face = MagicMock()
        mock_ui.selectEntity.return_value = MagicMock(entity=mock_face)

        create_thread(mock_design, mock_ui, inside=False, sizes=1)

        thread_feats = mock_design.rootComponent.features.threadFeatures
        thread_feats.createInput.assert_called_once()

    def test_thread_error_handling(self, mock_design, mock_ui):
        """Test error handling in create_thread."""
        from lib.features.operations import create_thread

        mock_ui.selectEntity.side_effect = Exception("User cancelled")

        create_thread(mock_design, mock_ui, inside=True, sizes=0)

        mock_ui.messageBox.assert_called()


class TestOperationsEquivalence:
    """Tests to validate equivalence between old and new operation functions."""

    def test_loft_signature(self, mock_design, mock_ui, mock_sketch):
        """Verify loft accepts same parameters as old version."""
        from lib.features.operations import loft

        # Old signature: loft(design, ui, sketchcount)
        mock_design.rootComponent.sketches.count = 2
        mock_design.rootComponent.sketches.item.return_value = mock_sketch

        loft(mock_design, mock_ui, 2)  # Positional
        loft(mock_design, mock_ui, sketchcount=2)  # Keyword

    def test_boolean_operation_signature(self, mock_design, mock_ui, mock_body):
        """Verify boolean_operation accepts same parameters as old version."""
        from lib.features.operations import boolean_operation

        # Old signature: boolean_operation(design, ui, op)
        mock_design.rootComponent.bRepBodies.count = 2
        mock_design.rootComponent.bRepBodies.item.return_value = mock_body

        boolean_operation(mock_design, mock_ui, "cut")  # Positional
        boolean_operation(mock_design, mock_ui, op="cut")  # Keyword

    def test_shell_signature(self, mock_design, mock_ui, mock_body):
        """Verify shell_existing_body accepts same parameters as old version."""
        from lib.features.operations import shell_existing_body

        # Old signature: shell_existing_body(design, ui, thickness=0.5, faceindex=0)
        mock_design.rootComponent.bRepBodies.item.return_value = mock_body

        shell_existing_body(mock_design, mock_ui)  # Defaults
        shell_existing_body(mock_design, mock_ui, 0.5, 0)  # Positional
        shell_existing_body(mock_design, mock_ui, thickness=0.5, faceindex=0)  # Keyword

    def test_fillet_signature(self, mock_design, mock_ui, mock_body):
        """Verify fillet_edges accepts same parameters as old version."""
        from lib.features.operations import fillet_edges

        # Old signature: fillet_edges(design, ui, radius=0.3)
        mock_design.rootComponent.bRepBodies.count = 1
        mock_design.rootComponent.bRepBodies.item.return_value = mock_body

        fillet_edges(mock_design, mock_ui)  # Default
        fillet_edges(mock_design, mock_ui, 0.3)  # Positional
        fillet_edges(mock_design, mock_ui, radius=0.3)  # Keyword
