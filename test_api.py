import pytest
import requests
from unittest.mock import patch, MagicMock
from requests.exceptions import ConnectionError, Timeout, HTTPError
import api

class TestFetchRates:
    def test_fetch_rates_success(self):
        """Проверяет успешность получения данных"""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'Valute': {
                'USD': {'Code': 'USD', 'Value': 75.5, 'ID': '1'}
            }
        }
        mock_response.raise_for_status.return_value = None
        
        with patch('requests.get', return_value=mock_response):
            result = api.fetch_rates()
            assert result == mock_response.json.return_value

    def test_fetch_rates_success_without_success_field(self):
        """Проверяет успешность получения данных без поля success"""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'Valute': {
                'EUR': {'Code': 'EUR', 'Value': 90.0, 'ID': '2'}
            }
        }
        mock_response.raise_for_status.return_value = None
        
        with patch('requests.get', return_value=mock_response):
            result = api.fetch_rates()
            assert 'Valute' in result
            assert result['Valute']['EUR']['Value'] == 90.0

    def test_fetch_rates_http_error(self):
        """Проверяет на наличие HTTP-ошибок"""
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = HTTPError("404 Client Error")
        
        with patch('requests.get', return_value=mock_response):
            result = api.fetch_rates()
            assert result == {}

    def test_fetch_rates_connection_error(self):
        """Проверяет на наличие ошибок подключения"""
        with patch('requests.get', side_effect=ConnectionError("Connection failed")):
            result = api.fetch_rates()
            assert result == {}

    def test_fetch_rates_timeout_error(self):
        """Проверяет на наличие timeout-ошибок"""
        with patch('requests.get', side_effect=Timeout("Request timed out")):
            result = api.fetch_rates()
            assert result == {}

    def test_fetch_rates_empty_valute(self):
        """Проверяет, если API вернуло пустое поле Valute"""
        mock_response = MagicMock()
        mock_response.json.return_value = {'Valute': {}}
        mock_response.raise_for_status.return_value = None
        
        with patch('requests.get', return_value=mock_response):
            result = api.fetch_rates()
            assert result == {'Valute': {}}

    def test_fetch_rates_malformed_json(self):
        """Проверяет JSON-файл на структурность"""
        mock_response = MagicMock()
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_response.raise_for_status.return_value = None
        
        with patch('requests.get', return_value=mock_response):
            result = api.fetch_rates()
            assert result == {}

    def test_fetch_rates_ssl_error(self):
        """Проверяет SSL-ошибку"""
        with patch('requests.get', side_effect=requests.exceptions.SSLError("SSL certificate error")):
            result = api.fetch_rates()
            assert result == {}
