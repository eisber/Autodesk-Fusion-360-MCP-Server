"""Tests for parametric modeling tools."""

import pytest
from unittest.mock import patch, MagicMock


class TestUserParameterTools:
    """Test suite for user parameter tools."""

    @patch('src.tools.parametric.send_request')
    def test_create_parameter(self, mock_send):
        """Test create_parameter sends correct request."""
        from src.tools.parametric import create_parameter
        
        mock_send.return_value = {
            "success": True,
            "parameter_name": "width",
            "value": 10.0,
            "expression": "10 mm",
            "unit": "mm"
        }
        
        result = create_parameter(
            name="width",
            value="10",
            unit="mm",
            comment="Part width"
        )
        
        assert result["success"] is True
        assert result["parameter_name"] == "width"
        mock_send.assert_called_once()

    @patch('src.tools.parametric.send_request')
    def test_create_parameter_with_expression(self, mock_send):
        """Test create_parameter with expression referencing other params."""
        from src.tools.parametric import create_parameter
        
        mock_send.return_value = {
            "success": True,
            "parameter_name": "height",
            "value": 20.0,
            "expression": "width * 2"
        }
        
        result = create_parameter(
            name="height",
            value="width * 2",
            unit="mm"
        )
        
        assert result["success"] is True
        assert result["expression"] == "width * 2"

    @patch('src.tools.parametric.send_request')
    def test_delete_parameter(self, mock_send):
        """Test delete_parameter sends correct request."""
        from src.tools.parametric import delete_parameter
        
        mock_send.return_value = {
            "success": True,
            "message": "Parameter 'width' deleted"
        }
        
        result = delete_parameter(name="width")
        
        assert result["success"] is True
        mock_send.assert_called_once()


class TestSketchAnalysisTools:
    """Test suite for sketch analysis tools."""

    @patch('src.tools.parametric.send_get_request')
    def test_get_sketch_info(self, mock_send):
        """Test get_sketch_info returns sketch details."""
        from src.tools.parametric import get_sketch_info
        
        mock_send.return_value = {
            "sketch_name": "Sketch1",
            "sketch_index": 0,
            "is_fully_constrained": True,
            "profile_count": 1,
            "curve_count": 4,
            "curves": [
                {"index": 0, "type": "SketchLine", "length": 5.0}
            ],
            "dimension_count": 2,
            "dimensions": [],
            "constraint_count": 4,
            "constraints": []
        }
        
        result = get_sketch_info(sketch_index=0)
        
        assert result["sketch_name"] == "Sketch1"
        assert result["is_fully_constrained"] is True
        mock_send.assert_called_once()

    @patch('src.tools.parametric.send_get_request')
    def test_get_sketch_info_last_sketch(self, mock_send):
        """Test get_sketch_info with -1 index for last sketch."""
        from src.tools.parametric import get_sketch_info
        
        mock_send.return_value = {
            "sketch_name": "Sketch3",
            "sketch_index": 2
        }
        
        result = get_sketch_info(sketch_index=-1)
        
        assert "sketch_index=-1" in mock_send.call_args[0][0]

    @patch('src.tools.parametric.send_get_request')
    def test_get_sketch_constraints(self, mock_send):
        """Test get_sketch_constraints returns constraint list."""
        from src.tools.parametric import get_sketch_constraints
        
        mock_send.return_value = {
            "sketch_name": "Sketch1",
            "constraint_count": 4,
            "constraints": [
                {"index": 0, "type": "HorizontalConstraint"},
                {"index": 1, "type": "VerticalConstraint"},
                {"index": 2, "type": "CoincidentConstraint"},
                {"index": 3, "type": "PerpendicularConstraint"}
            ]
        }
        
        result = get_sketch_constraints(sketch_index=0)
        
        assert result["constraint_count"] == 4
        assert result["constraints"][0]["type"] == "HorizontalConstraint"

    @patch('src.tools.parametric.send_get_request')
    def test_get_sketch_dimensions(self, mock_send):
        """Test get_sketch_dimensions returns dimension list."""
        from src.tools.parametric import get_sketch_dimensions
        
        mock_send.return_value = {
            "sketch_name": "Sketch1",
            "dimension_count": 2,
            "dimensions": [
                {"index": 0, "name": "d1", "value": 5.0, "expression": "5 mm"},
                {"index": 1, "name": "d2", "value": 3.0, "expression": "3 mm"}
            ]
        }
        
        result = get_sketch_dimensions(sketch_index=0)
        
        assert result["dimension_count"] == 2
        assert result["dimensions"][0]["name"] == "d1"


class TestInterferenceDetectionTools:
    """Test suite for interference detection tools."""

    @patch('src.tools.parametric.send_request')
    def test_check_interference_specific_bodies_no_collision(self, mock_send):
        """Test check_interference with specific bodies when no collision exists."""
        from src.tools.parametric import check_interference
        
        mock_send.return_value = {
            "has_interference": False,
            "interference_volume_cm3": 0,
            "body1_name": "Body1",
            "body2_name": "Body2"
        }
        
        result = check_interference(body1_index=0, body2_index=1)
        
        assert result["has_interference"] is False
        assert result["interference_volume_cm3"] == 0

    @patch('src.tools.parametric.send_request')
    def test_check_interference_specific_bodies_with_collision(self, mock_send):
        """Test check_interference with specific bodies when collision exists."""
        from src.tools.parametric import check_interference
        
        mock_send.return_value = {
            "has_interference": True,
            "interference_volume_cm3": 1.5,
            "body1_name": "Body1",
            "body2_name": "Body2"
        }
        
        result = check_interference(body1_index=0, body2_index=1)
        
        assert result["has_interference"] is True
        assert result["interference_volume_cm3"] == 1.5

    @patch('src.tools.parametric.send_get_request')
    def test_check_interference_all_bodies(self, mock_send):
        """Test check_interference without indices checks all bodies."""
        from src.tools.parametric import check_interference
        
        mock_send.return_value = {
            "total_bodies": 3,
            "interference_count": 1,
            "interferences": [
                {
                    "body1_index": 0,
                    "body1_name": "Body1",
                    "body2_index": 2,
                    "body2_name": "Body3",
                    "volume_cm3": 0.5
                }
            ]
        }
        
        result = check_interference()
        
        assert result["total_bodies"] == 3
        assert result["interference_count"] == 1


class TestTimelineTools:
    """Test suite for timeline/feature history tools."""

    @patch('src.tools.parametric.send_get_request')
    def test_get_timeline_info(self, mock_send):
        """Test get_timeline_info returns feature list."""
        from src.tools.parametric import get_timeline_info
        
        mock_send.return_value = {
            "feature_count": 5,
            "current_position": 5,
            "features": [
                {"index": 0, "name": "Sketch1", "type": "Sketch", "is_suppressed": False},
                {"index": 1, "name": "Extrude1", "type": "ExtrudeFeature", "is_suppressed": False},
                {"index": 2, "name": "Fillet1", "type": "FilletFeature", "is_suppressed": True}
            ]
        }
        
        result = get_timeline_info()
        
        assert result["feature_count"] == 5
        assert result["features"][2]["is_suppressed"] is True

    @patch('src.tools.parametric.send_request')
    def test_rollback_to_feature(self, mock_send):
        """Test rollback_to_feature changes timeline position."""
        from src.tools.parametric import rollback_to_feature
        
        mock_send.return_value = {
            "success": True,
            "current_position": 2,
            "message": "Rolled back to feature 2"
        }
        
        result = rollback_to_feature(feature_index=2)
        
        assert result["success"] is True
        assert result["current_position"] == 2

    @patch('src.tools.parametric.send_request')
    def test_rollback_to_end(self, mock_send):
        """Test rollback_to_end moves to latest feature."""
        from src.tools.parametric import rollback_to_end
        
        mock_send.return_value = {
            "success": True,
            "current_position": 5
        }
        
        result = rollback_to_end()
        
        assert result["success"] is True
        assert result["current_position"] == 5

    @patch('src.tools.parametric.send_request')
    def test_suppress_feature(self, mock_send):
        """Test suppress_feature toggles suppression state."""
        from src.tools.parametric import suppress_feature
        
        mock_send.return_value = {
            "success": True,
            "feature_name": "Fillet1",
            "is_suppressed": True
        }
        
        result = suppress_feature(feature_index=2, suppress=True)
        
        assert result["success"] is True
        assert result["is_suppressed"] is True


class TestMassPropertiesTools:
    """Test suite for mass properties tools."""

    @patch('src.tools.parametric.send_request')
    def test_get_mass_properties(self, mock_send):
        """Test get_mass_properties returns physical properties."""
        from src.tools.parametric import get_mass_properties
        
        mock_send.return_value = {
            "body_name": "Body1",
            "volume_cm3": 125.0,
            "density_g_cm3": 7.85,
            "mass_g": 981.25,
            "center_of_gravity": [2.5, 2.5, 2.5],
            "moments_of_inertia": {
                "Ixx": 1000.0,
                "Iyy": 1000.0,
                "Izz": 1000.0
            },
            "radii_of_gyration": {
                "kx": 2.83,
                "ky": 2.83,
                "kz": 2.83
            }
        }
        
        result = get_mass_properties(body_index=0)
        
        assert result["volume_cm3"] == 125.0
        assert result["mass_g"] == 981.25
        assert result["center_of_gravity"] == [2.5, 2.5, 2.5]

    @patch('src.tools.parametric.send_request')
    def test_get_mass_properties_with_density_override(self, mock_send):
        """Test get_mass_properties with custom density."""
        from src.tools.parametric import get_mass_properties
        
        mock_send.return_value = {
            "body_name": "Body1",
            "volume_cm3": 125.0,
            "density_g_cm3": 2.7,
            "mass_g": 337.5
        }
        
        result = get_mass_properties(body_index=0, material_density=2.7)
        
        assert result["density_g_cm3"] == 2.7
        # Check that density was passed in the request
        call_args = mock_send.call_args
        assert call_args[0][1]["material_density"] == 2.7


class TestConstructionGeometryTools:
    """Test suite for construction geometry tools."""

    @patch('src.tools.parametric.send_request')
    def test_create_offset_plane(self, mock_send):
        """Test create_offset_plane creates construction plane."""
        from src.tools.parametric import create_offset_plane
        
        mock_send.return_value = {
            "success": True,
            "plane_name": "Plane1"
        }
        
        result = create_offset_plane(offset=5.0, base_plane="XY")
        
        assert result["success"] is True
        assert result["plane_name"] == "Plane1"

    @patch('src.tools.parametric.send_request')
    def test_create_plane_at_angle(self, mock_send):
        """Test create_plane_at_angle creates angled plane."""
        from src.tools.parametric import create_plane_at_angle
        
        mock_send.return_value = {
            "success": True,
            "plane_name": "Plane2"
        }
        
        result = create_plane_at_angle(angle=45.0, base_plane="XY", axis="X")
        
        assert result["success"] is True
        call_args = mock_send.call_args
        assert call_args[0][1]["angle"] == 45.0

    @patch('src.tools.parametric.send_request')
    def test_create_midplane(self, mock_send):
        """Test create_midplane creates plane between faces."""
        from src.tools.parametric import create_midplane
        
        mock_send.return_value = {
            "success": True,
            "plane_name": "Plane3",
            "offset": 2.5
        }
        
        result = create_midplane(body_index=0, face1_index=0, face2_index=1)
        
        assert result["success"] is True
        assert result["offset"] == 2.5

    @patch('src.tools.parametric.send_request')
    def test_create_construction_axis(self, mock_send):
        """Test create_construction_axis creates axis."""
        from src.tools.parametric import create_construction_axis
        
        mock_send.return_value = {
            "success": True,
            "axis_name": "Axis1"
        }
        
        result = create_construction_axis(axis_type="edge", body_index=0, edge_index=0)
        
        assert result["success"] is True
        assert result["axis_name"] == "Axis1"

    @patch('src.tools.parametric.send_request')
    def test_create_construction_axis_two_points(self, mock_send):
        """Test create_construction_axis with two points."""
        from src.tools.parametric import create_construction_axis
        
        mock_send.return_value = {
            "success": True,
            "axis_name": "Axis2"
        }
        
        result = create_construction_axis(
            axis_type="two_points",
            point1=[0, 0, 0],
            point2=[10, 0, 0]
        )
        
        assert result["success"] is True
        call_args = mock_send.call_args
        assert call_args[0][1]["point1"] == [0, 0, 0]
        assert call_args[0][1]["point2"] == [10, 0, 0]

    @patch('src.tools.parametric.send_request')
    def test_create_construction_point(self, mock_send):
        """Test create_construction_point creates point."""
        from src.tools.parametric import create_construction_point
        
        mock_send.return_value = {
            "success": True,
            "point_name": "Point1",
            "coordinates": [5.0, 5.0, 5.0]
        }
        
        result = create_construction_point(point_type="coordinates", x=5.0, y=5.0, z=5.0)
        
        assert result["success"] is True
        assert result["coordinates"] == [5.0, 5.0, 5.0]

    @patch('src.tools.parametric.send_get_request')
    def test_list_construction_geometry(self, mock_send):
        """Test list_construction_geometry returns all construction elements."""
        from src.tools.parametric import list_construction_geometry
        
        mock_send.return_value = {
            "plane_count": 2,
            "planes": [
                {"index": 0, "name": "Plane1"},
                {"index": 1, "name": "Plane2"}
            ],
            "axis_count": 1,
            "axes": [
                {"index": 0, "name": "Axis1", "direction": [1, 0, 0]}
            ],
            "point_count": 1,
            "points": [
                {"index": 0, "name": "Point1", "position": [5, 5, 5]}
            ]
        }
        
        result = list_construction_geometry()
        
        assert result["plane_count"] == 2
        assert result["axis_count"] == 1
        assert result["point_count"] == 1


class TestParametricToolsErrorHandling:
    """Test error handling in parametric tools."""

    @patch('src.tools.parametric.send_request')
    def test_create_parameter_request_error(self, mock_send):
        """Test create_parameter handles request errors."""
        from src.tools.parametric import create_parameter
        import requests
        
        mock_send.side_effect = requests.RequestException("Connection failed")
        
        with pytest.raises(requests.RequestException):
            create_parameter(name="test", value="10")

    @patch('src.tools.parametric.send_get_request')
    def test_get_timeline_info_request_error(self, mock_send):
        """Test get_timeline_info handles request errors."""
        from src.tools.parametric import get_timeline_info
        import requests
        
        mock_send.side_effect = requests.RequestException("Connection failed")
        
        with pytest.raises(requests.RequestException):
            get_timeline_info()

    @patch('src.tools.parametric.send_request')
    def test_check_interference_request_error(self, mock_send):
        """Test check_interference handles request errors."""
        from src.tools.parametric import check_interference
        import requests
        
        mock_send.side_effect = requests.RequestException("Connection failed")
        
        with pytest.raises(requests.RequestException):
            check_interference(body1_index=0, body2_index=1)
