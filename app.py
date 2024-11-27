import re 
import unicodedata
import tkinter as tk
import requests
import sqlite3
from tkinter import messagebox
from tkinter.scrolledtext import ScrolledText


# 初始化資料庫
def setup_database():
    conn = sqlite3.connect('contacts.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS contacts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            title TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE
        )
        ''')
    conn.commit()
    conn.close()
    return 

# 存入資料資料庫(根據email檢查是否有重複)
def save_to_database(teacher_name, unique_teacher_position, unique_emails):
    conn = sqlite3.connect('contacts.db')
    cursor = conn.cursor()

    for (name, title, email) in zip(teacher_name, unique_teacher_position, unique_emails):
        cursor.execute('SELECT COUNT(*) FROM contacts WHERE email = ?', (email,))
        if cursor.fetchone()[0] > 0:
            continue

        cursor.execute('''
            INSERT INTO contacts (name, title, email)
            VALUES (?, ?, ?)
        ''', (name, title, email))
        
    conn.commit()
    conn.close()

# 從資料庫抓取資料
def fetch_data_from_database():
    conn = sqlite3.connect('contacts.db')
    cursor = conn.cursor()
    cursor.execute('SELECT name, title, email FROM contacts')
    data = cursor.fetchall()
    conn.close()
    return data

# 取得老師名稱、職稱、電子郵件
def parse_contacts(response):
    response_text = response.text

    # 姓名
    teacher_name_pattern = re.compile(r'<div class="member_name"><a href="[^"]+">([^<]+)</a>')
    teacher_name = teacher_name_pattern.findall(response_text)

    # 職稱
    teacher_position_pattern = re.compile(r'<i class="fas fa-briefcase"></i>\s*.*?</div>\s*<div class="member_info_content">(.*?)</div>')
    teacher_position = teacher_position_pattern.findall(response_text)
    unique_teacher_position = teacher_position

    # 電子郵件
    email_pattern = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}+\.[a-z|A-Z]+')
    emails = email_pattern.findall(response_text)
    unique_emails = list(set(emails))

    return teacher_name, unique_teacher_position, unique_emails

# 處理url錯誤並儲存、顯示資料
def fetch_url(url, display_text):
        try:
            response = requests.get(url)
            if response.status_code == 404:
                messagebox.showerror("網路錯誤", "無法取得網頁：404")

            teacher_name, unique_teacher_position, unique_emails = parse_contacts(response)

            # 儲存資料
            save_to_database(teacher_name, unique_teacher_position, unique_emails)
            
            # 獲取資料
            data = fetch_data_from_database()
            display_text.insert(tk.END, f"{pad_to_width('姓名', 10)}{pad_to_width('職稱', 30)}{pad_to_width('Email', 30)}\n")
            display_text.insert(tk.END, "-" * 80 + "\n")
            for row in data:
                display_text.insert(tk.END, f"{pad_to_width(row[0], 10)}{pad_to_width(row[1], 30)}{pad_to_width(row[2], 30)}\n")

        except Exception as error:
            messagebox.showerror('網路錯誤', f"無法連接網站: {error}")

# 獲得字串並計算中英文總占用空間
def get_display_width(text):
    width = 0
    for char in text:
        if unicodedata.east_asian_width(char) in 'WF':
            width += 2
        else:
            width += 1
    return width

# 補齊空格以達到指定寬度
def pad_to_width(text, width):
    current_width = get_display_width(text)
    padding = width - current_width
    return text + ' ' * max(0, padding)


# 主程式
setup_database()

windows = tk.Tk()
windows.title("爬蟲")
windows.geometry('640x480')
windows.resizable(1, 1)

# 設定 grid 配置
windows.grid_rowconfigure(0, weight=0)
windows.grid_rowconfigure(1, weight=1)
windows.grid_rowconfigure(2, weight=3)
windows.grid_columnconfigure(0, weight=1)
windows.grid_columnconfigure(1, weight=4)
windows.grid_columnconfigure(2, weight=0)

url_label = tk.Label(windows, text="URL:", font=("Arial", 12))
url_label.grid(row=0, column=0, padx=10, pady=10, sticky="w")

url_entry = tk.Entry(windows, font=("Arial", 12), width=50)
url_entry.grid(row=0, column=1, padx=10, pady=10, sticky="ew")

fetch_button = tk.Button(windows, text="抓取", font=("Arial", 12), command=lambda: fetch_url(url_entry.get(), display_text))
fetch_button.grid(row=0, column=2, padx=10, pady=10, sticky="ew")

display_text = ScrolledText(windows, font=("Courier New", 10), width=70, height=15)
display_text.grid(row=2, column=0, columnspan=3, padx=10, pady=10, sticky="nsew")

windows.mainloop()
