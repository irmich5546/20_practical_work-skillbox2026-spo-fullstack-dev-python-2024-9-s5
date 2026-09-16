import pytest
import tkinter as tk
from unittest.mock import patch, MagicMock, Mock
from main import CurrencyConverterApp
import db
import api

@pytest.fixture
def app():
    """Create application instance for testing"""
    with patch('tk.Tk.__init__', return_value=None):
        app = CurrencyConverterApp()
        app.loan_var = Mock()
        app.loan_time_var = Mock()
        app.annual_interest_var = Mock()
        app.base_var = Mock()
        app.target_var = Mock()
        app.monthly_label = Mock()
        app.loan_sum_label = Mock()
        app.interest_label = Mock()
        app.result_label = Mock()
        app.log_text = Mock()
        return app

class TestCalculateLoan:
    def test_calculate_loan_success(self, app):
        """Проверяет правильность вычисления кредита"""
        app.loan_var.get.return_value = "100000"
        app.loan_time_var.get.return_value = "12"
        app.annual_interest_var.get.return_value = "10"
        
        app.calculate_loan()
        
        # Проверяем, что методы config были вызваны
        assert app.monthly_label.config.called
        assert app.loan_sum_label.config.called
        assert app.interest_label.config.called

    def test_calculate_loan_invalid_loan_amount(self, app):
        """Проверяет на наличие ошибок, если введена неправильная сумма кредита"""
        app.loan_var.get.return_value = "-100"
        app.loan_time_var.get.return_value = "12"
        app.annual_interest_var.get.return_value = "10"
        
        with patch('tkinter.messagebox.showerror') as mock_error:
            app.calculate_loan()
            mock_error.assert_called()

class TestConvert:
    def test_convert_success(self, app):
        """Проверяет успешность конвертации"""
        app.monthly_label.cget.return_value = "Ежемесячный платёж: 10000.00 RUB"
        app.target_var.get.return_value = "USD"
        
        with patch('db.get_saved_rate', return_value=75.5):
            app.convert()
            assert app.result_label.config.called

    def test_convert_none_rate(self, app):
        """Проверяет конвертацию, когда курс является None"""
        app.monthly_label.cget.return_value = "Ежемесячный платёж: 10000.00 RUB"
        app.target_var.get.return_value = "USD"
        
        with patch('db.get_saved_rate', return_value=0.0):
            with patch('tkinter.messagebox.showwarning') as mock_warning:
                app.convert()
                mock_warning.assert_called()

    def test_convert_exception(self, app):
        """Проверяет обработку исключений"""
        app.monthly_label.cget.return_value = "Invalid text"
        
        with patch('tkinter.messagebox.showerror') as mock_error:
            app.convert()
            mock_error.assert_called()

class TestUpdateDB:
    def test_update_db_success(self, app):
        """Проверяет успешность обновления БД"""
        mock_rates = {
            'Valute': {
                '1': {'Code': 'USD', 'Value': 75.5, 'ID': '1'}
            }
        }
        
        with patch('api.fetch_rates', return_value=mock_rates):
            with patch('db.save_rate') as mock_save:
                with patch('tkinter.messagebox.showinfo') as mock_info:
                    app.update_db()
                    assert mock_save.called
                    assert mock_info.called

    def test_update_db_empty_rates(self, app):
        """Проверяет обновление БД пустым списком курсов"""
        with patch('api.fetch_rates', return_value={}):
            with patch('tkinter.messagebox.showerror') as mock_error:
                app.update_db()
                mock_error.assert_called()
