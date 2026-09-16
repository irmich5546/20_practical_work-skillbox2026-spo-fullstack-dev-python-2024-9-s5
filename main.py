import tkinter as tk
from tkinter import ttk, messagebox
import db
import api

class CurrencyConverterApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Конвертер валют")
        self.geometry("600x700")
        
        # Инициализация переменных
        self.loan_var = tk.StringVar()
        self.loan_time_var = tk.StringVar()
        self.annual_interest_var = tk.StringVar()
        self.base_var = tk.StringVar(value="RUB")
        self.target_var = tk.StringVar()
        
        self.create_widgets()
        db.init_db()
    
    def create_widgets(self):
        # Раздел выбора суммы кредита
        ttk.Label(self, text="Сумма кредита:").pack(pady=5)
        ttk.Entry(self, textvariable=self.loan_var).pack()
        
        # Раздел выбора срока кредита
        ttk.Label(self, text="Срок кредита (мес):").pack(pady=5)
        ttk.Entry(self, textvariable=self.loan_time_var).pack()
        
        # Раздел выбора процентной ставки
        ttk.Label(self, text="Процентная ставка (%):").pack(pady=5)
        ttk.Entry(self, textvariable=self.annual_interest_var).pack()
        
        # Кнопка расчёта кредита
        ttk.Button(self, text="Рассчитать", command=self.calculate_loan).pack(pady=10)
        
        # Вывод результата кредита
        self.monthly_label = ttk.Label(self, text="Ежемесячный платёж: 0 RUB")
        self.monthly_label.pack()
        
        self.loan_sum_label = ttk.Label(self, text="Сумма всех платежей: 0 RUB")
        self.loan_sum_label.pack()
        
        self.interest_label = ttk.Label(self, text="Начисленные проценты: 0 RUB")
        self.interest_label.pack()
        
        # Начальная валюта
        ttk.Label(self, text="Базовая валюта:").pack(pady=10)
        ttk.Label(self, textvariable=self.base_var).pack()
        
        # Выбор искомой валюты
        ttk.Label(self, text="Целевая валюта:").pack(pady=5)
        currencies = ["USD", "EUR", "CNY", "GBP", "JPY"]
        self.target_entry = ttk.Combobox(self, textvariable=self.target_var, values=currencies)
        self.target_entry.pack()
        self.target_entry.set("USD")
        
        # Кнопка конвертации
        ttk.Button(self, text="Конвертировать", command=self.convert).pack(pady=10)
        
        # Вывод результата
        self.result_label = ttk.Label(self, text="")
        self.result_label.pack()
        
        # Кнопка обновления курса валют
        ttk.Button(self, text="Обновить курсы", command=self.update_db).pack(pady=10)
        
        # Логгер
        ttk.Label(self, text="Лог:").pack()
        self.log_text = tk.Text(self, height=10, width=50)
        self.log_text.pack(pady=5)
    
    def log(self, message: str):
        """Выводит лог действий в специальную панель"""
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
    
    def is_loan_invalid(self, value: float, message: str) -> bool:
        """Проверяет, что сумма, количество месяцев или процентная ставка больше 0"""
        if value <= 0:
            messagebox.showerror("Ошибка", message)
            return True
        return False
    
    def calculate_loan(self):
        """Рассчитывает ежемесячный платёж, сумму всех платежей и начисленные проценты"""
        try:
            loan_amount = float(self.loan_var.get())
            loan_time = float(self.loan_time_var.get())
            annual_interest = float(self.annual_interest_var.get())
            
            if (self.is_loan_invalid(loan_amount, "Сумма кредита должна быть больше 0") or
                self.is_loan_invalid(loan_time, "Срок кредита должен быть больше 0") or
                self.is_loan_invalid(annual_interest, "Процентная ставка должна быть больше 0")):
                return
            
            # Расчёт ежемесячного платежа (аннуитетный)
            monthly_interest = annual_interest / 100 / 12
            if monthly_interest == 0:
                monthly_payment = loan_amount / loan_time
            else:
                monthly_payment = loan_amount * (monthly_interest * (1 + monthly_interest) ** loan_time) / \
                                  ((1 + monthly_interest) ** loan_time - 1)
            
            total_payment = monthly_payment * loan_time
            total_interest = total_payment - loan_amount
            
            self.monthly_label.config(text=f"Ежемесячный платёж: {monthly_payment:.2f} RUB")
            self.loan_sum_label.config(text=f"Сумма всех платежей: {total_payment:.2f} RUB")
            self.interest_label.config(text=f"Начисленные проценты: {total_interest:.2f} RUB")
            
            self.log(f"Кредит рассчитан: сумма={loan_amount}, срок={loan_time} мес, ставка={annual_interest}%")
            
        except ValueError:
            messagebox.showerror("Ошибка", "Введите корректные числовые значения")
    
    def convert(self):
        """Конвертирует RUB в выбранную валюту"""
        try:
            monthly_payment_text = self.monthly_label.cget("text")
            # Извлекаем сумму из текста
            amount_rub = float(monthly_payment_text.split(": ")[1].split()[0])
            
            target_currency = self.target_var.get()
            rate = db.get_saved_rate(target_currency)
            
            if rate == 0.0:
                self.log(f"Курс для {target_currency} не найден. Обновите курсы.")
                messagebox.showwarning("Внимание", "Курс валюты не найден. Нажмите 'Обновить курсы'")
                return
            
            converted_amount = amount_rub / rate
            self.result_label.config(text=f"{amount_rub:.2f} RUB = {converted_amount:.2f} {target_currency}")
            self.log(f"Конвертация: {amount_rub:.2f} RUB -> {converted_amount:.2f} {target_currency} (курс: {rate})")
            
        except (ValueError, IndexError) as e:
            messagebox.showerror("Ошибка", "Сначала рассчитайте кредит")
    
    def update_db(self):
        """Обновляет БД на актуальные данные"""
        self.log("Обновление курсов валют...")
        rates_data = api.fetch_rates()
        
        if not rates_data:
            self.log("Ошибка получения данных API")
            messagebox.showerror("Ошибка", "Не удалось получить курсы валют")
            return
        
        try:
            # Получаем курсы из API
            valutes = rates_data.get("Valute", {})
            
            for currency_id, currency_data in valutes.items():
                currency_code = currency_data["Code"]
                currency_rate = currency_data["Value"]
                
                # Сохраняем в БД
                db.save_rate(id=int(currency_data["ID"]), 
                           target_currency=currency_code, 
                           rate=currency_rate)
                
                self.log(f"Обновлён курс {currency_code}: {currency_rate}")
            
            # Также сохраняем базовый курс RUB (1.0)
            db.save_rate(id=1, target_currency="RUB", rate=1.0)
            
            messagebox.showinfo("Успех", "Курсы валют обновлены")
            self.log("Курсы валют успешно обновлены")
            
        except Exception as e:
            self.log(f"Ошибка при сохранении курсов: {e}")
            messagebox.showerror("Ошибка", f"Ошибка при обновлении курсов: {e}")

if __name__ == "__main__":
    app = CurrencyConverterApp()
    app.mainloop()