"""Tests for measurement tools."""

import pytest
from unittest.mock import patch, MagicMock


class TestMeasurementTools:
    """Test suite for measurement tools."""

    @patch('src.tools.measurement.send_request')
    def test_measure_distance(self, mock_send):
        """Test measure_distance sends correct request."""
        from src.tools.measurement import measure_distance
        
        mock_send.return_value = {
            "distance_cm": 5.0,
            "distance_mm": 50.0,
            "point1": [0, 0, 0],
            "point2": [5, 0, 0]
        }
        
        result = measure_distance(
            entity1_type="face",
            entity1_index=0,
            entity2_type="face",
            entity2_index=1,
            body1_index=0,
            body2_index=0
        )
        
        assert result["distance_cm"] == 5.0
        assert result["distance_mm"] == 50.0
        mock_send.assert_called_once()

    @patch('src.tools.measurement.send_request')
    def test_measure_angle(self, mock_send):
        """Test measure_angle sends correct request."""
        from src.tools.measurement import measure_angle
        
        mock_send.return_value = {
            "angle_degrees": 90.0,
            "angle_radians": 1.5708
        }
        
        result = measure_angle(
            entity1_type="face",
            entity1_index=0,
            entity2_type="face",
            entity2_index=1
        )
        
        assert result["angle_degrees"] == 90.0
        mock_send.assert_called_once()

    @patch('src.tools.measurement.send_request')
    def test_measure_area(self, mock_send):
        """Test measure_area sends correct request."""
        from src.tools.measurement import measure_area
        
        mock_send.return_value = {
            "area_cm2": 25.0,
            "area_mm2": 2500.0,
            "face_type": "Plane"
        }
        
        result = measure_area(face_index=0, body_index=0)
        
        assert result["area_cm2"] == 25.0
        assert result["face_type"] == "Plane"
        mock_send.assert_called_once()

    @patch('src.tools.measurement.send_request')
    def test_measure_volume(self, mock_send):
        """Test measure_volume sends correct request."""
        from src.tools.measurement import measure_volume
        
        mock_send.return_value = {
            "volume_cm3": 125.0,
            "volume_mm3": 125000.0,
            "body_name": "Body1"
        }
        
        result = measure_volume(body_index=0)
        
        assert result["volume_cm3"] == 125.0
        assert result["body_name"] == "Body1"
        mock_send.assert_called_once()

    @patch('src.tools.measurement.send_request')
    def test_measure_edge_length(self, mock_send):
        """Test measure_edge_length sends correct request."""
        from src.tools.measurement import measure_edge_length
        
        mock_send.return_value = {
            "length_cm": 10.0,
            "length_mm": 100.0,
            "edge_type": "Line3D",
            "start_point": [0, 0, 0],
            "end_point": [10, 0, 0]
        }
        
        result = measure_edge_length(edge_index=0, body_index=0)
        
        assert result["length_cm"] == 10.0
        assert result["edge_type"] == "Line3D"
        mock_send.assert_called_once()

    @patch('src.tools.measurement.send_request')
    def test_measure_body_properties(self, mock_send):
        """Test measure_body_properties sends correct request."""
        from src.tools.measurement import measure_body_properties
        
        mock_send.return_value = {
            "volume_cm3": 125.0,
            "surface_area_cm2": 150.0,
            "bounding_box": {
                "min": [0, 0, 0],
                "max": [5, 5, 5],
                "size": [5, 5, 5]
            },
            "centroid": [2.5, 2.5, 2.5],
            "face_count": 6,
            "edge_count": 12,
            "vertex_count": 8,
            "body_name": "Body1"
        }
        
        result = measure_body_properties(body_index=0)
        
        assert result["volume_cm3"] == 125.0
        assert result["face_count"] == 6
        assert result["centroid"] == [2.5, 2.5, 2.5]
        mock_send.assert_called_once()

    @patch('src.tools.measurement.send_request')
    def test_measure_point_to_point(self, mock_send):
        """Test measure_point_to_point sends correct request."""
        from src.tools.measurement import measure_point_to_point
        
        mock_send.return_value = {
            "distance_cm": 5.0,
            "distance_mm": 50.0,
            "delta": [3, 4, 0]
        }
        
        result = measure_point_to_point(
            point1=[0, 0, 0],
            point2=[3, 4, 0]
        )
        
        assert result["distance_cm"] == 5.0
        assert result["delta"] == [3, 4, 0]
        mock_send.assert_called_once()

    @patch('src.tools.measurement.send_get_request')
    def test_get_edges_info(self, mock_send):
        """Test get_edges_info sends correct GET request."""
        from src.tools.measurement import get_edges_info
        
        mock_send.return_value = {
            "body_name": "Body1",
            "body_index": 0,
            "edge_count": 12,
            "edges": [
                {"index": 0, "type": "Line3D", "length_cm": 5.0}
            ]
        }
        
        result = get_edges_info(body_index=0)
        
        assert result["edge_count"] == 12
        mock_send.assert_called_once()

    @patch('src.tools.measurement.send_get_request')
    def test_get_vertices_info(self, mock_send):
        """Test get_vertices_info sends correct GET request."""
        from src.tools.measurement import get_vertices_info
        
        mock_send.return_value = {
            "body_name": "Body1",
            "body_index": 0,
            "vertex_count": 8,
            "vertices": [
                {"index": 0, "position": [0, 0, 0]}
            ]
        }
        
        result = get_vertices_info(body_index=0)
        
        assert result["vertex_count"] == 8
        mock_send.assert_called_once()


class TestMeasurementToolsErrorHandling:
    """Test error handling in measurement tools."""

    @patch('src.tools.measurement.send_request')
    def test_measure_distance_request_error(self, mock_send):
        """Test measure_distance handles request errors."""
        from src.tools.measurement import measure_distance
        import requests
        
        mock_send.side_effect = requests.RequestException("Connection failed")
        
        with pytest.raises(requests.RequestException):
            measure_distance(
                entity1_type="face",
                entity1_index=0,
                entity2_type="face",
                entity2_index=1
            )

    @patch('src.tools.measurement.send_request')
    def test_measure_volume_request_error(self, mock_send):
        """Test measure_volume handles request errors."""
        from src.tools.measurement import measure_volume
        import requests
        
        mock_send.side_effect = requests.RequestException("Connection failed")
        
        with pytest.raises(requests.RequestException):
            measure_volume(body_index=0)
