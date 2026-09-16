import pytest
import sqlite3
import os
import tempfile
from datetime import datetime
from unittest.mock import patch, MagicMock
import db

@pytest.fixture
def temp_db():
    """Create a temporary database for testing"""
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
    temp_file.close()
    
    original_db_name = db.DB_NAME
    
    with patch.object(db, 'DB_NAME', temp_file.name):
        db.init_db()
        yield temp_file.name
    
    try:
        os.unlink(temp_file.name)
    except (PermissionError, FileNotFoundError):
        pass

@pytest.fixture
def sample_data():
    """Sample data for testing"""
    return {
        'id': 1,
        'currency': 'USD',
        'rate': 1.0
    }

class TestInitDB:
    def test_init_db_creates_table(self, temp_db):
        """Проверяет создание таблицы"""
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='rates'")
        result = cursor.fetchone()
        conn.close()
        assert result is not None
        assert result[0] == 'rates'

class TestSaveRate:
    def test_save_rate_new_record(self, temp_db):
        """Проверяет добавление новой записи"""
        db.save_rate(1, 'USD', 75.5)
        result = db.get_saved_rate('USD')
        assert result == 75.5

    def test_save_rate_update_existing(self, temp_db):
        """Проверяет обновление существующего поля"""
        db.save_rate(1, 'USD', 75.5)
        db.save_rate(1, 'USD', 80.0)
        result = db.get_saved_rate('USD')
        assert result == 80.0

    def test_save_rate_date_format(self, temp_db):
        """Проверяет формат даты"""
        db.save_rate(1, 'USD', 75.5)
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute("SELECT fetched_at FROM rates WHERE id=1")
        date_str = cursor.fetchone()[0]
        conn.close()
        # Проверяем, что дата в ISO формате
        datetime.fromisoformat(date_str)

    def test_save_rate_multiple_currencies(self, temp_db):
        """Проверяет разный набор валют"""
        db.save_rate(1, 'USD', 75.5)
        db.save_rate(2, 'EUR', 90.0)
        db.save_rate(3, 'CNY', 11.5)
        assert db.get_saved_rate('USD') == 75.5
        assert db.get_saved_rate('EUR') == 90.0
        assert db.get_saved_rate('CNY') == 11.5

    def test_save_rate_edge_cases(self, temp_db):
        """Проверяет разные диапазоны значений"""
        db.save_rate(1, 'USD', 0.001)
        assert db.get_saved_rate('USD') == 0.001
        
        db.save_rate(2, 'EUR', 999999.99)
        assert db.get_saved_rate('EUR') == 999999.99

    def test_save_rate_database_connection_error(self, temp_db):
        """Проверяет разрыв соединения с БД"""
        with patch('sqlite3.connect') as mock_connect:
            mock_connect.side_effect = sqlite3.Error("Connection error")
            with pytest.raises(sqlite3.Error):
                db.save_rate(1, 'USD', 75.5)

    def test_save_rate_commit_error(self, temp_db):
        """Проверяет ошибку при коммите данных в БД"""
        conn = sqlite3.connect(temp_db)
        with patch.object(conn, 'commit') as mock_commit:
            mock_commit.side_effect = sqlite3.Error("Commit error")
            with pytest.raises(sqlite3.Error):
                db.save_rate(1, 'USD', 75.5)
        conn.close()

    def test_save_rate_parameter_types(self, temp_db):
        """Проверяет разные типы данных параметров"""
        db.save_rate(1, 'USD', 75.5)
        db.save_rate(2, 'EUR', 90)
        assert isinstance(db.get_saved_rate('USD'), float)

    def test_save_rate_sql_injection_protection(self, temp_db):
        """Проверяет защиту на SQL-инъекции"""
        malicious_input = "'; DROP TABLE rates; --"
        db.save_rate(1, malicious_input, 75.5)
        result = db.get_saved_rate(malicious_input)
        assert result == 75.5
        # Проверяем, что таблица не удалена
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='rates'")
        assert cursor.fetchone() is not None
        conn.close()

class TestGetSavedRate:
    def test_get_saved_rate_success(self, temp_db):
        """Проверяет успешность получения данных из БД"""
        db.save_rate(1, 'USD', 75.5)
        result = db.get_saved_rate('USD')
        assert result == 75.5

    def test_get_saved_rate_default_currency(self, temp_db):
        """Проверяет получение курса стандартной валюты"""
        db.save_rate(1, 'RUB', 1.0)
        result = db.get_saved_rate('RUB')
        assert result == 1.0

    def test_get_saved_rate_nonexistent_currency(self, temp_db):
        """Проверяет получение несуществующей валюты"""
        result = db.get_saved_rate('XYZ')
        assert result == 0.0

    def test_get_saved_rate_empty_database(self, temp_db):
        """Проверяет получение данных из пустой БД"""
        result = db.get_saved_rate('USD')
        assert result == 0.0

    def test_get_saved_rate_multiple_currencies(self, temp_db):
        """Проверяет получение множества валют"""
        db.save_rate(1, 'USD', 75.5)
        db.save_rate(2, 'EUR', 90.0)
        db.save_rate(3, 'CNY', 11.5)
        assert db.get_saved_rate('USD') == 75.5
        assert db.get_saved_rate('EUR') == 90.0
        assert db.get_saved_rate('CNY') == 11.5

    def test_get_saved_rate_case_sensitivity(self, temp_db):
        """Проверяет чувствительность написания параметров"""
        db.save_rate(1, 'USD', 75.5)
        result_upper = db.get_saved_rate('USD')
        result_lower = db.get_saved_rate('usd')
        assert result_upper == 75.5
        assert result_lower == 0.0

    def test_get_saved_rate_sql_injection_protection(self, temp_db):
        """Проверяет защиту на SQL-инъекции"""
        malicious_input = "'; DROP TABLE rates; --"
        result = db.get_saved_rate(malicious_input)
        assert result == 0.0
        # Проверяем, что таблица не удалена
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='rates'")
        assert cursor.fetchone() is not None
        conn.close()

    def test_get_saved_rate_database_connection_error(self, temp_db):
        """Проверяет разрыв соединения с БД"""
        with patch('sqlite3.connect') as mock_connect:
            mock_connect.side_effect = sqlite3.Error("Connection error")
            with pytest.raises(sqlite3.Error):
                db.get_saved_rate('USD')
