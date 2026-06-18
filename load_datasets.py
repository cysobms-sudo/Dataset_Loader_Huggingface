# -*- coding: utf-8 -*-
"""
Created on Tue Jun 16 12:50:25 2026

@author: Alireza
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import threading
import webbrowser
import json
import os
from datetime import datetime
import pandas as pd
import requests

class DatasetLoaderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("بارگذارنده دیتاست هاگینگ فیس - نسخه حرفه‌ای")
        self.root.geometry("1400x900")
        self.root.configure(bg='#2b2b2b')
        
        self.loading_process = None
        self.cancel_flag = False
        self.current_dataset = None
        self.history_file = "dataset_history.json"
        self.settings_file = "app_settings.json"
        self.dark_mode = True
        self.sample_data = []
        
        # تنظیمات پیش‌فرض
        self.settings = {
            "theme": "dark",
            "default_split": "train",
            "default_rows": 10,
            "font_size": 13,
            "show_tooltips": True
        }
        
        # استایل
        self.font_btn = ('Segoe UI', 11, 'bold')
        self.font_title = ('Segoe UI', 20, 'bold')
        self.font_text = ('Segoe UI', 11)
        self.font_info_title = ('Segoe UI', 14, 'bold')
        self.font_info_body = ('Segoe UI', 12)
        
        self.load_settings()
        self.load_history()
        self.create_widgets()
        self.apply_theme()
    
    def load_settings(self):
        if os.path.exists(self.settings_file):
            try:
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    saved_settings = json.load(f)
                    self.settings.update(saved_settings)
            except:
                pass
        self.dark_mode = self.settings["theme"] == "dark"
    
    def save_settings(self):
        try:
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, ensure_ascii=False, indent=2)
        except:
            pass
    
    def load_history(self):
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    self.history = json.load(f)
            except:
                self.history = []
        else:
            self.history = []
    
    def save_to_history(self, dataset_name):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        entry = {"name": dataset_name, "time": timestamp}
        self.history = [h for h in self.history if h["name"] != dataset_name]
        self.history.insert(0, entry)
        self.history = self.history[:10]
        with open(self.history_file, 'w', encoding='utf-8') as f:
            json.dump(self.history, f, ensure_ascii=False, indent=2)
        self.update_history_display()
    
    def update_history_display(self):
        self.history_listbox.delete(0, tk.END)
        for item in self.history:
            self.history_listbox.insert(tk.END, f"📁 {item['name']} ({item['time']})")
    
    def paste_from_clipboard(self):
        try:
            clipboard_text = self.root.clipboard_get()
            if clipboard_text:
                self.dataset_entry.delete(0, tk.END)
                self.dataset_entry.insert(0, clipboard_text.strip())
                self.status_bar.config(text=f"✅ متن چسبانده شد: {clipboard_text[:50]}...")
        except Exception as e:
            messagebox.showerror("خطا", f"خطا: {str(e)}")
    
    def open_settings(self):
        settings_window = tk.Toplevel(self.root)
        settings_window.title("تنظیمات")
        settings_window.geometry("500x500")
        settings_window.configure(bg='#2b2b2b')
        settings_window.transient(self.root)
        settings_window.grab_set()
        
        title = tk.Label(settings_window, text="⚙️ تنظیمات", 
                        font=self.font_title, bg='#2b2b2b', fg='#FFD700')
        title.pack(pady=20)
        
        settings_frame = tk.Frame(settings_window, bg='#2b2b2b')
        settings_frame.pack(fill='both', expand=True, padx=30, pady=10)
        
        # تم
        theme_frame = tk.LabelFrame(settings_frame, text="ظاهر", 
                                    font=self.font_text, bg='#2b2b2b', fg='white')
        theme_frame.pack(fill='x', pady=10)
        self.theme_var = tk.StringVar(value=self.settings["theme"])
        tk.Radiobutton(theme_frame, text="🌙 حالت شب", variable=self.theme_var, 
                      value="dark", font=self.font_text, bg='#2b2b2b', fg='white',
                      selectcolor='#2b2b2b').pack(anchor='w', padx=20, pady=5)
        tk.Radiobutton(theme_frame, text="☀️ حالت روز", variable=self.theme_var, 
                      value="light", font=self.font_text, bg='#2b2b2b', fg='white',
                      selectcolor='#2b2b2b').pack(anchor='w', padx=20, pady=5)
        
        # تنظیمات پیش‌فرض
        default_frame = tk.LabelFrame(settings_frame, text="پیش‌فرض", 
                                      font=self.font_text, bg='#2b2b2b', fg='white')
        default_frame.pack(fill='x', pady=10)
        
        split_frame = tk.Frame(default_frame, bg='#2b2b2b')
        split_frame.pack(fill='x', padx=20, pady=5)
        tk.Label(split_frame, text="Split:", font=self.font_text, 
                bg='#2b2b2b', fg='white', width=15, anchor='w').pack(side='left')
        self.default_split_var = tk.StringVar(value=self.settings["default_split"])
        split_combo = ttk.Combobox(split_frame, textvariable=self.default_split_var,
                                   values=["train", "test", "validation"], state="readonly", width=15)
        split_combo.pack(side='right')
        
        rows_frame = tk.Frame(default_frame, bg='#2b2b2b')
        rows_frame.pack(fill='x', padx=20, pady=5)
        tk.Label(rows_frame, text="تعداد ردیف:", font=self.font_text, 
                bg='#2b2b2b', fg='white', width=15, anchor='w').pack(side='left')
        self.default_rows_var = tk.StringVar(value=str(self.settings["default_rows"]))
        rows_spinbox = tk.Spinbox(rows_frame, from_=1, to=50, textvariable=self.default_rows_var,
                                  font=self.font_text, width=15)
        rows_spinbox.pack(side='right')
        
        # فونت
        font_frame = tk.LabelFrame(settings_frame, text="فونت", 
                                   font=self.font_text, bg='#2b2b2b', fg='white')
        font_frame.pack(fill='x', pady=10)
        font_size_frame = tk.Frame(font_frame, bg='#2b2b2b')
        font_size_frame.pack(fill='x', padx=20, pady=5)
        tk.Label(font_size_frame, text="اندازه:", font=self.font_text, 
                bg='#2b2b2b', fg='white', width=15, anchor='w').pack(side='left')
        self.font_size_var = tk.StringVar(value=str(self.settings["font_size"]))
        font_size_spinbox = tk.Spinbox(font_size_frame, from_=10, to=20, textvariable=self.font_size_var,
                                        font=self.font_text, width=15)
        font_size_spinbox.pack(side='right')
        
        def save_and_close():
            self.settings["theme"] = self.theme_var.get()
            self.settings["default_split"] = self.default_split_var.get()
            self.settings["default_rows"] = int(self.default_rows_var.get())
            self.settings["font_size"] = int(self.font_size_var.get())
            self.save_settings()
            self.dark_mode = self.settings["theme"] == "dark"
            self.apply_theme()
            self.font_info_body = ('Segoe UI', self.settings["font_size"])
            self.info_text.configure(font=self.font_info_body)
            settings_window.destroy()
            self.status_bar.config(text="✅ تنظیمات ذخیره شد")
        
        btn_frame = tk.Frame(settings_frame, bg='#2b2b2b')
        btn_frame.pack(pady=20)
        tk.Button(btn_frame, text="💾 ذخیره", command=save_and_close,
                 font=self.font_btn, bg='#4CAF50', fg='white', width=12).pack(side='left', padx=5)
        tk.Button(btn_frame, text="❌ انصراف", command=settings_window.destroy,
                 font=self.font_btn, bg='#f44336', fg='white', width=12).pack(side='left', padx=5)
    
    def create_widgets(self):
        # فریم بالایی
        top_frame = tk.Frame(self.root, bg='#2b2b2b')
        top_frame.pack(fill='x', padx=20, pady=10)
        
        title = tk.Label(top_frame, text="📊 بارگذارنده دیتاست از هاگینگ فیس", 
                         font=self.font_title, bg='#2b2b2b', fg='#FFD700')
        title.pack(side='left')
        
        self.settings_btn = tk.Button(top_frame, text="⚙️ تنظیمات", font=self.font_btn, 
                                      bg='#607D8B', fg='white', command=self.open_settings)
        self.settings_btn.pack(side='right', padx=5)
        
        self.theme_btn = tk.Button(top_frame, text="🌙", font=('Segoe UI', 14), 
                                   bg='#2b2b2b', fg='white', command=self.toggle_theme_simple)
        self.theme_btn.pack(side='right', padx=5)
        
        # فریم اصلی
        main_frame = tk.Frame(self.root, bg='#2b2b2b')
        main_frame.pack(fill='both', expand=True, padx=20, pady=10)
        
        # ========== ستون چپ ==========
        left_frame = tk.Frame(main_frame, bg='#2b2b2b', width=350)
        left_frame.pack(side='left', fill='both', expand=False, padx=(0, 15))
        left_frame.pack_propagate(False)
        
        control_frame = tk.LabelFrame(left_frame, text="🎮 کنترل بارگذاری", 
                                      font=self.font_info_title, bg='#2b2b2b', fg='#FFD700')
        control_frame.pack(fill='both', expand=True)
        
        control_inner = tk.Frame(control_frame, bg='#2b2b2b')
        control_inner.pack(fill='both', expand=True, padx=15, pady=15)
        
        self.hf_btn = tk.Button(control_inner, text="🚀 رفتن به Hugging Face", 
                                font=self.font_btn, bg='#4CAF50', fg='white',
                                command=self.open_huggingface, height=2)
        self.hf_btn.pack(fill='x', pady=5)
        
        tk.Label(control_inner, text="نام دیتاست:", font=self.font_text, 
                bg='#2b2b2b', fg='white').pack(anchor='w', pady=(10,5))
        
        entry_frame = tk.Frame(control_inner, bg='#2b2b2b')
        entry_frame.pack(fill='x', pady=5)
        self.dataset_entry = tk.Entry(entry_frame, font=('Segoe UI', 12))
        self.dataset_entry.pack(side='left', fill='x', expand=True, padx=(0, 5))
        self.paste_btn = tk.Button(entry_frame, text="📋 Paste", 
                                   font=self.font_btn, bg='#00BCD4', fg='white',
                                   command=self.paste_from_clipboard, width=8)
        self.paste_btn.pack(side='right')
        
        btn_frame = tk.Frame(control_inner, bg='#2b2b2b')
        btn_frame.pack(fill='x', pady=10)
        self.load_btn = tk.Button(btn_frame, text="📥 بارگذاری", 
                                  font=self.font_btn, bg='#2196F3', fg='white',
                                  command=self.start_loading_dataset, height=2)
        self.load_btn.pack(side='left', fill='x', expand=True, padx=(0, 5))
        self.cancel_btn = tk.Button(btn_frame, text="❌ لغو", 
                                    font=self.font_btn, bg='#f44336', fg='white',
                                    command=self.cancel_loading, height=2, state='disabled')
        self.cancel_btn.pack(side='right', fill='x', expand=True, padx=(5, 0))
        
        self.progress = ttk.Progressbar(control_inner, mode='indeterminate')
        self.progress.pack(fill='x', pady=10)
        
        self.clear_all_btn = tk.Button(control_inner, text="🗑️ پاک کردن همه", 
                                       font=self.font_btn, bg='#607D8B', fg='white',
                                       command=self.clear_all, height=1)
        self.clear_all_btn.pack(fill='x', pady=5)
        
        history_label = tk.Label(control_inner, text="📜 تاریخچه:", 
                                font=self.font_text, bg='#2b2b2b', fg='white')
        history_label.pack(anchor='w', pady=(10,5))
        
        self.history_listbox = tk.Listbox(control_inner, height=10, font=self.font_text)
        self.history_listbox.pack(fill='both', expand=True, pady=5)
        self.history_listbox.bind('<Double-Button-1>', self.load_from_history)
        self.update_history_display()
        
        # ========== ستون راست ==========
        right_frame = tk.Frame(main_frame, bg='#2b2b2b')
        right_frame.pack(side='right', fill='both', expand=True)
        
        # ===== بخش اطلاعات دیتاست =====
        info_container = tk.Frame(right_frame, bg='#2b2b2b')
        info_container.pack(fill='both', expand=True, pady=(0, 10))
        
        info_label = tk.Label(info_container, text="📄 اطلاعات کامل دیتاست", 
                             font=self.font_info_title, bg='#2b2b2b', fg='#FFD700')
        info_label.pack(anchor='w', pady=(0, 5))
        
        self.info_text = scrolledtext.ScrolledText(info_container, 
                                                   font=self.font_info_body, 
                                                   wrap=tk.WORD,
                                                   bg='#1e1e1e', 
                                                   fg='#d4d4d4', 
                                                   insertbackground='white',
                                                   spacing1=5,
                                                   spacing2=3,
                                                   spacing3=5,
                                                   height=12)
        self.info_text.pack(fill='both', expand=True)
        
        # دکمه‌های ذخیره اطلاعات
        info_buttons = tk.Frame(info_container, bg='#2b2b2b')
        info_buttons.pack(fill='x', pady=(8, 0))
        
        self.save_info_btn = tk.Button(info_buttons, text="💾 ذخیره اطلاعات در فایل (TXT)", 
                                       font=self.font_btn, bg='#FF9800', fg='white',
                                       command=self.save_info_to_file)
        self.save_info_btn.pack(side='left', fill='x', expand=True, padx=(0, 5))
        
        self.copy_info_btn = tk.Button(info_buttons, text="📋 کپی اطلاعات", 
                                       font=self.font_btn, bg='#9C27B0', fg='white',
                                       command=self.copy_info_to_clipboard)
        self.copy_info_btn.pack(side='right', fill='x', expand=True, padx=(5, 0))
        
        # ===== بخش نمونه داده =====
        data_container = tk.Frame(right_frame, bg='#2b2b2b')
        data_container.pack(fill='both', expand=True)
        
        # عنوان و نوار ابزار در یک خط
        header_frame = tk.Frame(data_container, bg='#2b2b2b')
        header_frame.pack(fill='x', pady=(0, 5))
        
        data_label = tk.Label(header_frame, text="📊 نمونه داده‌ها (چند ردیف اول)", 
                             font=self.font_info_title, bg='#2b2b2b', fg='#FFD700')
        data_label.pack(side='left')
        
        # نوار ابزار سمت راست
        toolbar = tk.Frame(header_frame, bg='#2b2b2b')
        toolbar.pack(side='right')
        
        tk.Label(toolbar, text="تعداد ردیف:", font=self.font_text, 
                bg='#2b2b2b', fg='white').pack(side='left', padx=5)
        self.sample_rows_var = tk.StringVar(value=str(self.settings["default_rows"]))
        rows_spin = tk.Spinbox(toolbar, from_=1, to=50, textvariable=self.sample_rows_var,
                               font=self.font_text, width=6)
        rows_spin.pack(side='left', padx=5)
        self.refresh_btn = tk.Button(toolbar, text="🔄 نمایش", 
                                     font=self.font_btn, bg='#2196F3', fg='white',
                                     command=self.refresh_sample_data)
        self.refresh_btn.pack(side='left', padx=5)
        
        # دکمه‌های ذخیره نمونه داده - درست در زیر عنوان و قبل از جدول
        data_buttons = tk.Frame(data_container, bg='#2b2b2b')
        data_buttons.pack(fill='x', pady=(5, 5))
        
        self.save_data_btn = tk.Button(data_buttons, text="💾 ذخیره نمونه داده در فایل (CSV)", 
                                       font=self.font_btn, bg='#FF9800', fg='white',
                                       command=self.save_sample_data_to_file)
        self.save_data_btn.pack(side='left', fill='x', expand=True, padx=(0, 5))
        
        self.copy_data_btn = tk.Button(data_buttons, text="📋 کپی نمونه داده", 
                                       font=self.font_btn, bg='#9C27B0', fg='white',
                                       command=self.copy_sample_data_to_clipboard)
        self.copy_data_btn.pack(side='left', fill='x', expand=True, padx=5)
        
        self.excel_btn = tk.Button(data_buttons, text="📊 خروجی Excel", 
                                   font=self.font_btn, bg='#4CAF50', fg='white',
                                   command=self.export_to_excel)
        self.excel_btn.pack(side='right', fill='x', expand=True, padx=(5, 0))
        
        # جدول داده
        tree_frame = tk.Frame(data_container, bg='#2b2b2b')
        tree_frame.pack(fill='both', expand=True, pady=5)
        
        scroll_y = tk.Scrollbar(tree_frame)
        scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        scroll_x = tk.Scrollbar(tree_frame, orient=tk.HORIZONTAL)
        scroll_x.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.tree = ttk.Treeview(tree_frame, yscrollcommand=scroll_y.set, 
                                  xscrollcommand=scroll_x.set, height=12)
        self.tree.pack(fill='both', expand=True)
        scroll_y.config(command=self.tree.yview)
        scroll_x.config(command=self.tree.xview)
        
        self.data_status = tk.Label(data_container, text="", font=self.font_text, 
                                    bg='#2b2b2b', fg='#cccccc')
        self.data_status.pack(pady=5)
        
        # نوار وضعیت
        self.status_bar = tk.Label(self.root, text="✅ آماده به کار", 
                                   bd=1, relief=tk.SUNKEN, anchor=tk.W,
                                   bg='#1e1e1e', fg='white', font=('Segoe UI', 10))
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def refresh_sample_data(self):
        if not self.sample_data:
            self.data_status.config(text="⚠️ ابتدا یک دیتاست را بارگذاری کنید", fg="#f44336")
            return
        try:
            num_rows = int(self.sample_rows_var.get())
            self.display_sample_data(num_rows)
            self.data_status.config(text=f"✅ {num_rows} ردیف نمایش داده شد", fg="#4CAF50")
        except Exception as e:
            self.data_status.config(text=f"❌ خطا: {str(e)}", fg="#f44336")
    
    def export_to_excel(self):
        if not self.sample_data:
            messagebox.showwarning("هشدار", "هیچ داده‌ای برای خروجی وجود ندارد!")
            return
        file_path = filedialog.asksaveasfilename(defaultextension=".xlsx", 
            filetypes=[("Excel files", "*.xlsx")], title="ذخیره به صورت Excel")
        if file_path:
            try:
                pd.DataFrame(self.sample_data).to_excel(file_path, index=False, engine='openpyxl')
                self.status_bar.config(text=f"📊 ذخیره شد")
                messagebox.showinfo("موفق", "فایل Excel ذخیره شد!")
            except Exception as e:
                messagebox.showerror("خطا", f"خطا: {str(e)}\nنصب: pip install openpyxl")
    
    def save_sample_data_to_file(self):
        if not self.sample_data:
            messagebox.showwarning("هشدار", "هیچ داده‌ای برای ذخیره وجود ندارد!")
            return
        file_path = filedialog.asksaveasfilename(defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")], title="ذخیره نمونه داده")
        if file_path:
            try:
                pd.DataFrame(self.sample_data).to_csv(file_path, index=False, encoding='utf-8-sig')
                self.status_bar.config(text=f"💾 ذخیره شد")
                messagebox.showinfo("موفق", "نمونه داده ذخیره شد!")
            except Exception as e:
                messagebox.showerror("خطا", f"خطا: {str(e)}")
    
    def copy_sample_data_to_clipboard(self):
        if not self.sample_data:
            messagebox.showwarning("هشدار", "هیچ داده‌ای برای کپی وجود ندارد!")
            return
        try:
            text = pd.DataFrame(self.sample_data).to_string()
            self.root.clipboard_clear()
            self.root.clipboard_append(text)
            self.status_bar.config(text="📋 نمونه داده کپی شد")
            messagebox.showinfo("موفق", "نمونه داده کپی شد!")
        except Exception as e:
            messagebox.showerror("خطا", f"خطا: {str(e)}")
    
    def clear_all(self):
        if messagebox.askyesno("تأیید", "همه اطلاعات پاک شود؟"):
            self.info_text.delete(1.0, tk.END)
            for item in self.tree.get_children():
                self.tree.delete(item)
            self.sample_data = []
            self.data_status.config(text="")
            self.status_bar.config(text="🗑️ همه اطلاعات پاک شد")
    
    def toggle_theme_simple(self):
        if self.dark_mode:
            self.settings["theme"] = "light"
        else:
            self.settings["theme"] = "dark"
        self.dark_mode = not self.dark_mode
        self.apply_theme()
        self.save_settings()
    
    def apply_theme(self):
        if self.dark_mode:
            bg_color = '#2b2b2b'
            fg_color = 'white'
            text_bg = '#1e1e1e'
            text_fg = '#d4d4d4'
            self.theme_btn.config(text="🌙")
        else:
            bg_color = '#f5f5f5'
            fg_color = 'black'
            text_bg = 'white'
            text_fg = 'black'
            self.theme_btn.config(text="☀️")
        
        self.root.configure(bg=bg_color)
        self.info_text.configure(bg=text_bg, fg=text_fg)
        self.status_bar.configure(bg=bg_color, fg=fg_color)
        self.history_listbox.configure(bg=text_bg, fg=text_fg)
        self.dataset_entry.configure(bg=text_bg, fg=text_fg)
    
    def open_huggingface(self):
        webbrowser.open("https://huggingface.co/datasets")
    
    def load_from_history(self, event):
        selection = self.history_listbox.curselection()
        if selection:
            item = self.history_listbox.get(selection[0])
            dataset_name = item.split(" (")[0].replace("📁 ", "")
            self.dataset_entry.delete(0, tk.END)
            self.dataset_entry.insert(0, dataset_name)
            self.start_loading_dataset()
    
    def save_info_to_file(self):
        if not self.info_text.get(1.0, tk.END).strip():
            messagebox.showwarning("هشدار", "هیچ اطلاعاتی برای ذخیره وجود ندارد!")
            return
        file_path = filedialog.asksaveasfilename(defaultextension=".txt",
            filetypes=[("Text files", "*.txt")], title="ذخیره اطلاعات دیتاست")
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(self.info_text.get(1.0, tk.END))
                self.status_bar.config(text=f"💾 ذخیره شد")
                messagebox.showinfo("موفق", "اطلاعات دیتاست ذخیره شد!")
            except Exception as e:
                messagebox.showerror("خطا", f"خطا: {str(e)}")
    
    def copy_info_to_clipboard(self):
        info = self.info_text.get(1.0, tk.END).strip()
        if info:
            self.root.clipboard_clear()
            self.root.clipboard_append(info)
            self.status_bar.config(text="📋 اطلاعات کپی شد")
            messagebox.showinfo("موفق", "اطلاعات کپی شد!")
        else:
            messagebox.showwarning("هشدار", "هیچ اطلاعاتی وجود ندارد!")
    
    def start_loading_dataset(self):
        dataset_name = self.dataset_entry.get().strip()
        if not dataset_name:
            messagebox.showerror("خطا", "لطفاً نام دیتاست را وارد کنید")
            return
        
        split = self.settings["default_split"]
        
        self.load_btn.config(state='disabled')
        self.cancel_btn.config(state='normal')
        self.progress.start(10)
        self.info_text.delete(1.0, tk.END)
        
        self.info_text.insert(tk.END, "⏳ در حال بارگذاری دیتاست...\n\n", "title")
        self.info_text.insert(tk.END, f"نام: {dataset_name}\n", "subtitle")
        self.info_text.insert(tk.END, f"Split: {split}\n\n", "subtitle")
        
        self.cancel_flag = False
        self.loading_process = threading.Thread(target=self.load_dataset, args=(dataset_name, split))
        self.loading_process.daemon = True
        self.loading_process.start()
    
    def cancel_loading(self):
        self.cancel_flag = True
        self.status_bar.config(text="❌ لغو شد")
        self.info_text.insert(tk.END, "\n⚠️ عملیات لغو شد.\n", "error")
        self.progress.stop()
        self.load_btn.config(state='normal')
        self.cancel_btn.config(state='disabled')
    
    def get_sample_data(self, dataset_name, split, num_rows=10):
        sample_data = []
        try:
            from datasets import load_dataset
            self.update_info("📊 دریافت نمونه داده...", "highlight")
            dataset = load_dataset(dataset_name, split=split, streaming=True)
            for i, sample in enumerate(dataset):
                if i >= num_rows:
                    break
                processed = {}
                for k, v in sample.items():
                    if isinstance(v, (list, dict)):
                        processed[k] = str(v)[:100] + "..." if len(str(v)) > 100 else str(v)
                    else:
                        processed[k] = v
                sample_data.append(processed)
            return sample_data
        except Exception as e:
            self.update_info(f"⚠️ خطا: {str(e)[:100]}", "error")
            return []
    
    def update_info(self, message, tag=None):
        def _update():
            if tag == "title":
                self.info_text.insert(tk.END, message + "\n", "title")
            elif tag == "subtitle":
                self.info_text.insert(tk.END, message + "\n", "subtitle")
            elif tag == "highlight":
                self.info_text.insert(tk.END, message + "\n", "highlight")
            elif tag == "error":
                self.info_text.insert(tk.END, message + "\n", "error")
            else:
                self.info_text.insert(tk.END, message + "\n")
            self.info_text.see(tk.END)
        self.root.after(0, _update)
    
    def load_dataset(self, dataset_name, split):
        try:
            self.update_info("🔍 جستجو در Hugging Face...", "highlight")
            if self.cancel_flag: return
            
            response = requests.get(f"https://huggingface.co/api/datasets/{dataset_name}", timeout=10)
            if self.cancel_flag: return
            
            if response.status_code != 200:
                self.update_info(f"❌ دیتاست '{dataset_name}' یافت نشد!", "error")
                return
            
            dataset_info = response.json()
            self.save_to_history(dataset_name)
            
            num_rows = self.settings["default_rows"]
            self.sample_data = self.get_sample_data(dataset_name, split, num_rows)
            
            self.root.after(0, lambda: self.display_sample_data(num_rows))
            self.root.after(0, lambda: self.data_status.config(text=f"✅ {len(self.sample_data)} ردیف دریافت شد", fg="#4CAF50"))
            
            info_str = f"""
{'='*70}
✅ اطلاعات دیتاست
{'='*70}

📌 نام: {dataset_info.get('id', 'نامشخص')}
🏢 نویسنده: {dataset_info.get('author', 'نامشخص')}

📝 توضیحات:
"""
            desc = dataset_info.get('description', 'ندارد')
            for i in range(0, len(desc), 80):
                info_str += f"   {desc[i:i+80]}\n"
            
            info_str += f"""
📈 آمار:
   • دانلودها: {dataset_info.get('downloads', 0):,}
   • لایک‌ها: {dataset_info.get('likes', 0)}
   • بازدیدها: {dataset_info.get('views', 0):,}

🏷️ تگ‌ها: {', '.join(dataset_info.get('tags', ['بدون تگ'])[:10])}

📋 Split: {split}
📊 ردیف‌ها: {len(self.sample_data)}

{'='*70}
💡 کاربرد: {self.get_application(dataset_name)}
{'='*70}
🔗 لینک: https://huggingface.co/datasets/{dataset_name}
"""
            if not self.cancel_flag:
                self.update_info(info_str)
                self.status_bar.config(text=f"✅ {dataset_name} بارگذاری شد")
                messagebox.showinfo("موفق", f"دیتاست '{dataset_name}' بارگذاری شد!")
        except Exception as e:
            if not self.cancel_flag:
                self.update_info(f"❌ خطا: {str(e)}", "error")
        finally:
            self.root.after(0, self.loading_finished)
    
    def get_application(self, name):
        name_lower = name.lower()
        if 'imdb' in name_lower:
            return "تحلیل احساسات، پردازش زبان طبیعی"
        elif 'squad' in name_lower:
            return "پرسش و پاسخ، درک مطلب"
        elif 'mnist' in name_lower:
            return "تشخیص دست خط، طبقه‌بندی تصاویر"
        else:
            return "یادگیری ماشین، تحلیل داده، تحقیق"
    
    def display_sample_data(self, num_rows=10):
        for item in self.tree.get_children():
            self.tree.delete(item)
        if not self.sample_data:
            return
        cols = list(self.sample_data[0].keys())
        self.tree["columns"] = cols
        self.tree["show"] = "headings"
        for col in cols:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=140, minwidth=100)
        for row in self.sample_data[:num_rows]:
            values = [str(row.get(c, ""))[:80] for c in cols]
            self.tree.insert("", "end", values=values)
    
    def loading_finished(self):
        self.progress.stop()
        self.load_btn.config(state='normal')
        self.cancel_btn.config(state='disabled')

if __name__ == "__main__":
    root = tk.Tk()
    app = DatasetLoaderApp(root)
    
    # تنظیم تگ‌ها بعد از ایجاد ویجت
    app.info_text.tag_config("title", font=('Segoe UI', app.settings["font_size"]+3, 'bold'), 
                              foreground="#FFD700", spacing3=10)
    app.info_text.tag_config("subtitle", font=('Segoe UI', app.settings["font_size"]+1, 'bold'), 
                              foreground="#4CAF50", spacing3=8)
    app.info_text.tag_config("highlight", foreground="#2196F3", 
                              font=('Segoe UI', app.settings["font_size"], 'bold'))
    app.info_text.tag_config("error", foreground="#f44336", 
                              font=('Segoe UI', app.settings["font_size"], 'bold'))
    
    root.mainloop()