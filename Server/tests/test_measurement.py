"""Tests for measurement tools using @fusion_tool decorator."""

from unittest.mock import MagicMock, patch

import pytest


class TestMeasurementTools:
    """Test suite for measurement tools."""

    @patch("src.tools.base.requests.post")
    @patch("src.tools.base.get_telemetry")
    def test_measure_distance(self, mock_telemetry, mock_post):
        """Test measure_distance sends correct request."""
        from src.tools.measurement import measure_distance

        mock_telemetry.return_value = MagicMock()
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "distance_cm": 5.0,
            "distance_mm": 50.0,
            "point1": [0, 0, 0],
            "point2": [5, 0, 0],
        }
        mock_post.return_value = mock_response

        result = measure_distance(
            entity1_type="face",
            entity1_index=0,
            entity2_type="face",
            entity2_index=1,
            body1_index=0,
            body2_index=0,
        )

        assert result["distance_cm"] == 5.0
        mock_post.assert_called_once()
        # Verify the command was sent correctly
        call_kwargs = mock_post.call_args
        assert call_kwargs[1]["json"]["command"] == "measure_distance"

    @patch("src.tools.base.requests.post")
    @patch("src.tools.base.get_telemetry")
    def test_measure_angle(self, mock_telemetry, mock_post):
        """Test measure_angle sends correct request."""
        from src.tools.measurement import measure_angle

        mock_telemetry.return_value = MagicMock()
        mock_response = MagicMock()
        mock_response.json.return_value = {"angle_degrees": 90.0, "angle_radians": 1.5708}
        mock_post.return_value = mock_response

        result = measure_angle(
            entity1_type="face", entity1_index=0, entity2_type="face", entity2_index=1
        )

        assert result["angle_degrees"] == 90.0
        mock_post.assert_called_once()

    @patch("src.tools.base.requests.post")
    @patch("src.tools.base.get_telemetry")
    def test_measure_area(self, mock_telemetry, mock_post):
        """Test measure_area sends correct request."""
        from src.tools.measurement import measure_area

        mock_telemetry.return_value = MagicMock()
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "area_cm2": 10.0,
            "area_mm2": 1000.0,
            "face_type": "Plane",
        }
        mock_post.return_value = mock_response

        result = measure_area(face_index=0, body_index=0)

        assert result["area_cm2"] == 10.0
        mock_post.assert_called_once()

    @patch("src.tools.base.requests.post")
    @patch("src.tools.base.get_telemetry")
    def test_measure_volume(self, mock_telemetry, mock_post):
        """Test measure_volume sends correct request."""
        from src.tools.measurement import measure_volume

        mock_telemetry.return_value = MagicMock()
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "volume_cm3": 125.0,
            "volume_mm3": 125000.0,
            "body_name": "Body1",
        }
        mock_post.return_value = mock_response

        result = measure_volume(body_index=0)

        assert result["volume_cm3"] == 125.0

    @patch("src.tools.base.requests.get")
    @patch("src.tools.base.get_telemetry")
    def test_get_edges_info(self, mock_telemetry, mock_get):
        """Test get_edges_info uses GET request."""
        from src.tools.measurement import get_edges_info

        mock_telemetry.return_value = MagicMock()
        mock_response = MagicMock()
        mock_response.json.return_value = {"edge_count": 12, "edges": []}
        mock_get.return_value = mock_response

        result = get_edges_info(body_index=0)

        assert result["edge_count"] == 12
        mock_get.assert_called_once()


class TestMeasurementToolsErrorHandling:
    """Tests for measurement tool error handling."""

    @patch("src.tools.base.requests.post")
    @patch("src.tools.base.get_telemetry")
    def test_measure_distance_request_error(self, mock_telemetry, mock_post):
        """Test measure_distance handles request errors."""
        import requests

        from src.tools.measurement import measure_distance

        mock_telemetry.return_value = MagicMock()
        mock_post.side_effect = requests.RequestException("Connection failed")

        with pytest.raises(requests.RequestException):
            measure_distance(
                entity1_type="face", entity1_index=0, entity2_type="face", entity2_index=1
            )
