"""Tests for utils module functions.

These tests validate the state, selection, and export utility functions.
"""

import pytest
from unittest.mock import MagicMock


class TestGetModelParameters:
    """Tests for get_model_parameters function."""

    def test_get_parameters_empty(self, mock_design):
        """Test getting parameters from empty design."""
        from lib.utils.state import get_model_parameters

        # Set up empty parameters
        mock_design.allParameters = []
        mock_design.userParameters.count = 0
        mock_design.userParameters.item = MagicMock(return_value=None)

        result = get_model_parameters(mock_design)

        assert result == []

    def test_get_parameters_basic(self, mock_design):
        """Test getting parameters with some parameters."""
        from lib.utils.state import get_model_parameters

        # Set up mock parameters
        param1 = MagicMock()
        param1.name = "Length"
        param1.value = 10.0
        param1.unit = "mm"
        param1.expression = "10 mm"

        param2 = MagicMock()
        param2.name = "Width"
        param2.value = 5.0
        param2.unit = "mm"
        param2.expression = "5 mm"

        mock_design.allParameters = [param1, param2]
        mock_design.userParameters.count = 0
        mock_design.userParameters.item = MagicMock(return_value=None)

        result = get_model_parameters(mock_design)

        assert len(result) == 2
        assert result[0]["Name"] == "Length"
        assert result[1]["Name"] == "Width"


class TestGetCurrentModelState:
    """Tests for get_current_model_state function."""

    def test_get_state_no_design(self):
        """Test getting state with no design."""
        from lib.utils.state import get_current_model_state

        result = get_current_model_state(None)

        assert "error" in result
        assert "No active design" in result["error"]

    def test_get_state_empty_model(self, mock_design):
        """Test getting state from empty model."""
        from lib.utils.state import get_current_model_state

        mock_design.rootComponent.bRepBodies.count = 0
        mock_design.rootComponent.sketches.count = 0
        mock_design.rootComponent.name = "TestDesign"

        result = get_current_model_state(mock_design)

        assert result["body_count"] == 0
        assert result["sketch_count"] == 0
        assert result["bodies"] == []
        assert result["sketches"] == []
        assert result["design_name"] == "TestDesign"

    def test_get_state_with_bodies(self, mock_design):
        """Test getting state from model with bodies."""
        from lib.utils.state import get_current_model_state

        # Create a fresh body mock with name as a concrete string value
        body = MagicMock()
        body.name = "Body1"
        body.volume = 100.0
        bounding_box = MagicMock()
        min_point = MagicMock()
        min_point.x = 0
        min_point.y = 0
        min_point.z = 0
        max_point = MagicMock()
        max_point.x = 5
        max_point.y = 5
        max_point.z = 5
        bounding_box.minPoint = min_point
        bounding_box.maxPoint = max_point
        body.boundingBox = bounding_box

        mock_design.rootComponent.bRepBodies.count = 1
        # Override the side_effect set in conftest.py
        mock_design.rootComponent.bRepBodies.item.side_effect = None
        mock_design.rootComponent.bRepBodies.item.return_value = body
        mock_design.rootComponent.sketches.count = 0
        mock_design.rootComponent.name = "TestDesign"

        result = get_current_model_state(mock_design)

        assert result["body_count"] == 1
        assert len(result["bodies"]) == 1
        assert result["bodies"][0]["name"] == "Body1"

    def test_get_state_with_sketches(self, mock_design, mock_sketch):
        """Test getting state from model with sketches."""
        from lib.utils.state import get_current_model_state

        mock_design.rootComponent.bRepBodies.count = 0
        mock_design.rootComponent.sketches.count = 1
        mock_sketch.name = "Sketch1"
        mock_sketch.isVisible = True
        mock_design.rootComponent.sketches.item.side_effect = None
        mock_design.rootComponent.sketches.item.return_value = mock_sketch
        mock_design.rootComponent.name = "TestDesign"

        result = get_current_model_state(mock_design)

        assert result["sketch_count"] == 1
        assert len(result["sketches"]) == 1


class TestGetFacesInfo:
    """Tests for get_faces_info function."""

    def test_get_faces_no_design(self):
        """Test getting faces info with no design."""
        from lib.utils.state import get_faces_info

        result = get_faces_info(None)

        assert "error" in result

    def test_get_faces_invalid_index(self, mock_design, mock_body):
        """Test getting faces with invalid body index."""
        from lib.utils.state import get_faces_info

        mock_design.rootComponent.bRepBodies.count = 1

        result = get_faces_info(mock_design, body_index=5)

        assert "error" in result
        assert "out of range" in result["error"]

    def test_get_faces_basic(self, mock_design):
        """Test getting faces info."""
        from lib.utils.state import get_faces_info

        # Create a fresh body mock with name as a concrete string value
        body = MagicMock()
        body.name = "Body1"
        faces = MagicMock()
        face = MagicMock()
        face.centroid = MagicMock(x=2.5, y=2.5, z=2.5)
        face.area = 25.0
        face.geometry = MagicMock(objectType="adsk::fusion::Plane")
        faces.count = 6
        faces.item = MagicMock(return_value=face)
        body.faces = faces

        mock_design.rootComponent.bRepBodies.count = 1
        # Override the side_effect set in conftest.py
        mock_design.rootComponent.bRepBodies.item.side_effect = None
        mock_design.rootComponent.bRepBodies.item.return_value = body

        result = get_faces_info(mock_design, body_index=0)

        assert result["body_name"] == "Body1"
        assert result["body_index"] == 0
        assert result["face_count"] == 6


class TestSetParameter:
    """Tests for set_parameter function."""

    def test_set_parameter_basic(self, mock_design, mock_ui):
        """Test setting a parameter value."""
        from lib.utils.state import set_parameter

        param = MagicMock()
        mock_design.allParameters.itemByName.return_value = param

        set_parameter(mock_design, mock_ui, "Length", "20 mm")

        mock_design.allParameters.itemByName.assert_called_with("Length")
        assert param.expression == "20 mm"

    def test_set_parameter_error_handling(self, mock_design, mock_ui):
        """Test error handling when parameter not found."""
        from lib.utils.state import set_parameter

        mock_design.allParameters.itemByName.side_effect = Exception("Not found")

        # Should not raise, just show message box
        set_parameter(mock_design, mock_ui, "NonExistent", "10")

        mock_ui.messageBox.assert_called()


class TestUndo:
    """Tests for undo function."""

    def test_undo_basic(self, mock_adsk_module, mock_design, mock_ui):
        """Test undo operation."""
        from lib.utils.state import undo

        # Undo uses adsk.core.Application.get() internally
        # Just verify it doesn't crash
        undo(mock_design, mock_ui)


class TestDeleteAll:
    """Tests for delete_all function."""

    def test_delete_all_empty(self, mock_design, mock_ui):
        """Test delete all on empty design."""
        from lib.utils.state import delete_all

        mock_design.rootComponent.bRepBodies.count = 0

        # Should not raise
        delete_all(mock_design, mock_ui)

    def test_delete_all_with_bodies(self, mock_design, mock_ui, mock_body):
        """Test delete all with bodies."""
        from lib.utils.state import delete_all

        mock_design.rootComponent.bRepBodies.count = 1
        mock_design.rootComponent.bRepBodies.item.return_value = mock_body

        delete_all(mock_design, mock_ui)

        mock_design.rootComponent.features.removeFeatures.add.assert_called()

    def test_delete_all_error_handling(self, mock_design, mock_ui):
        """Test error handling in delete_all."""
        from lib.utils.state import delete_all

        mock_design.rootComponent.bRepBodies.count = 1
        mock_design.rootComponent.bRepBodies.item.side_effect = Exception("Error")

        # Should not raise
        delete_all(mock_design, mock_ui)

        mock_ui.messageBox.assert_called()


class TestSelectBody:
    """Tests for select_body function."""

    def test_select_body_found(self, mock_design, mock_ui, mock_body):
        """Test selecting an existing body."""
        from lib.utils.selection import select_body

        mock_design.rootComponent.bRepBodies.itemByName.return_value = mock_body

        result = select_body(mock_design, mock_ui, "Body1")

        assert result == mock_body
        mock_design.rootComponent.bRepBodies.itemByName.assert_called_with("Body1")

    def test_select_body_not_found(self, mock_design, mock_ui):
        """Test selecting a non-existent body."""
        from lib.utils.selection import select_body

        mock_design.rootComponent.bRepBodies.itemByName.return_value = None

        result = select_body(mock_design, mock_ui, "NonExistent")

        assert result is None
        mock_ui.messageBox.assert_called()

    def test_select_body_error_handling(self, mock_design, mock_ui):
        """Test error handling in select_body."""
        from lib.utils.selection import select_body

        mock_design.rootComponent.bRepBodies.itemByName.side_effect = Exception("Error")

        result = select_body(mock_design, mock_ui, "Body1")

        assert result is None
        mock_ui.messageBox.assert_called()


class TestSelectSketch:
    """Tests for select_sketch function."""

    def test_select_sketch_found(self, mock_design, mock_ui, mock_sketch):
        """Test selecting an existing sketch."""
        from lib.utils.selection import select_sketch

        mock_design.rootComponent.sketches.itemByName.return_value = mock_sketch

        result = select_sketch(mock_design, mock_ui, "Sketch1")

        assert result == mock_sketch
        mock_design.rootComponent.sketches.itemByName.assert_called_with("Sketch1")

    def test_select_sketch_not_found(self, mock_design, mock_ui):
        """Test selecting a non-existent sketch."""
        from lib.utils.selection import select_sketch

        mock_design.rootComponent.sketches.itemByName.return_value = None

        result = select_sketch(mock_design, mock_ui, "NonExistent")

        assert result is None
        mock_ui.messageBox.assert_called()

    def test_select_sketch_error_handling(self, mock_design, mock_ui):
        """Test error handling in select_sketch."""
        from lib.utils.selection import select_sketch

        mock_design.rootComponent.sketches.itemByName.side_effect = Exception("Error")

        result = select_sketch(mock_design, mock_ui, "Sketch1")

        assert result is None
        mock_ui.messageBox.assert_called()


class TestExportAsStep:
    """Tests for export_as_step function."""

    def test_export_step_success(self, mock_design, mock_ui, monkeypatch):
        """Test successful STEP export."""
        from lib.utils.export import export_as_step

        # Mock os.makedirs and os.path.join
        monkeypatch.setattr("os.makedirs", lambda *args, **kwargs: None)
        monkeypatch.setattr("os.environ", {"USERPROFILE": "C:\\Users\\Test"})

        mock_design.exportManager.execute.return_value = True

        export_as_step(mock_design, mock_ui, "TestExport")

        mock_design.exportManager.createSTEPExportOptions.assert_called()
        mock_design.exportManager.execute.assert_called()

    def test_export_step_failure(self, mock_design, mock_ui, monkeypatch):
        """Test failed STEP export."""
        from lib.utils.export import export_as_step

        monkeypatch.setattr("os.makedirs", lambda *args, **kwargs: None)
        monkeypatch.setattr("os.environ", {"USERPROFILE": "C:\\Users\\Test"})

        mock_design.exportManager.execute.return_value = False

        export_as_step(mock_design, mock_ui, "TestExport")

        mock_ui.messageBox.assert_called()


class TestExportAsStl:
    """Tests for export_as_stl function."""

    def test_export_stl_success(self, mock_design, mock_ui, monkeypatch):
        """Test successful STL export."""
        from lib.utils.export import export_as_stl

        monkeypatch.setattr("os.makedirs", lambda *args, **kwargs: None)
        monkeypatch.setattr("os.environ", {"USERPROFILE": "C:\\Users\\Test"})

        mock_stl_options = MagicMock()
        mock_stl_options.availablePrintUtilities = []
        mock_design.exportManager.createSTLExportOptions.return_value = mock_stl_options
        mock_design.rootComponent.allOccurrences = []
        mock_design.rootComponent.bRepBodies = []

        export_as_stl(mock_design, mock_ui, "TestExport")

        mock_design.exportManager.createSTLExportOptions.assert_called()


class TestUtilsEquivalence:
    """Tests to verify equivalence with MCP_old.py functions."""

    def test_get_model_parameters_signature(self):
        """Verify get_model_parameters has correct signature."""
        from lib.utils.state import get_model_parameters
        import inspect

        sig = inspect.signature(get_model_parameters)
        params = list(sig.parameters.keys())

        assert params == ["design"]

    def test_get_current_model_state_signature(self):
        """Verify get_current_model_state has correct signature."""
        from lib.utils.state import get_current_model_state
        import inspect

        sig = inspect.signature(get_current_model_state)
        params = list(sig.parameters.keys())

        assert params == ["design"]

    def test_delete_all_signature(self):
        """Verify delete_all has correct signature."""
        from lib.utils.state import delete_all
        import inspect

        sig = inspect.signature(delete_all)
        params = list(sig.parameters.keys())

        assert params == ["design", "ui"]
