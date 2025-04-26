#!/usr/bin/env python3
"""
EMSC Deprem Veri İndirici - Grafik Kullanıcı Arayüzü

Bu script, EMSC (Avrupa-Akdeniz Sismoloji Merkezi) API'sinden deprem verilerini
kullanıcının belirttiği bölge ve zaman aralığına göre indirir ve CSV dosyası olarak kaydeder.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import pandas as pd
import datetime
import sys
import os
from dateutil import parser as date_parser
import threading

# emsc_earthquake_data.py'den fonksiyonları içe aktarıyoruz
from emsc_earthquake_data import (
    validate_dates, 
    format_date_for_api, 
    get_earthquake_data, 
    process_earthquake_data, 
    save_to_csv
)

class EMSCEarthquakeGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("EMSC Deprem Veri İndirici")
        self.root.geometry("700x600")
        self.root.resizable(True, True)
        
        # Ana çerçeve
        main_frame = ttk.Frame(root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Başlık
        title_label = ttk.Label(main_frame, text="EMSC Deprem Veri İndirici", font=("Arial", 16, "bold"))
        title_label.pack(pady=10)
        
        # Bölge Koordinatları Çerçevesi
        region_frame = ttk.LabelFrame(main_frame, text="Bölge Koordinatları", padding="10")
        region_frame.pack(fill=tk.X, pady=5)
        
        # Enlem (Latitude) girdileri
        lat_frame = ttk.Frame(region_frame)
        lat_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(lat_frame, text="Minimum Enlem:").grid(row=0, column=0, sticky=tk.W, padx=5)
        self.min_lat_var = tk.StringVar(value="36.0")  # Türkiye'nin güney sınırı yaklaşık
        ttk.Entry(lat_frame, textvariable=self.min_lat_var, width=10).grid(row=0, column=1, padx=5)
        
        ttk.Label(lat_frame, text="Maksimum Enlem:").grid(row=0, column=2, sticky=tk.W, padx=5)
        self.max_lat_var = tk.StringVar(value="42.0")  # Türkiye'nin kuzey sınırı yaklaşık
        ttk.Entry(lat_frame, textvariable=self.max_lat_var, width=10).grid(row=0, column=3, padx=5)
        
        # Boylam (Longitude) girdileri
        lon_frame = ttk.Frame(region_frame)
        lon_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(lon_frame, text="Minimum Boylam:").grid(row=0, column=0, sticky=tk.W, padx=5)
        self.min_lon_var = tk.StringVar(value="26.0")  # Türkiye'nin batı sınırı yaklaşık
        ttk.Entry(lon_frame, textvariable=self.min_lon_var, width=10).grid(row=0, column=1, padx=5)
        
        ttk.Label(lon_frame, text="Maksimum Boylam:").grid(row=0, column=2, sticky=tk.W, padx=5)
        self.max_lon_var = tk.StringVar(value="45.0")  # Türkiye'nin doğu sınırı yaklaşık
        ttk.Entry(lon_frame, textvariable=self.max_lon_var, width=10).grid(row=0, column=3, padx=5)
        
        # Hazır bölge seçenekleri
        preset_frame = ttk.Frame(region_frame)
        preset_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(preset_frame, text="Hazır Bölge:").grid(row=0, column=0, sticky=tk.W, padx=5)
        
        self.region_presets = {
            "Türkiye": {"min_lat": 36.0, "max_lat": 42.0, "min_lon": 26.0, "max_lon": 45.0},
            "İstanbul": {"min_lat": 40.8, "max_lat": 41.3, "min_lon": 28.5, "max_lon": 29.5},
            "İzmir": {"min_lat": 38.0, "max_lat": 38.7, "min_lon": 26.5, "max_lon": 27.5},
            "Ankara": {"min_lat": 39.5, "max_lat": 40.2, "min_lon": 32.5, "max_lon": 33.5},
            "Dünya": {"min_lat": -90.0, "max_lat": 90.0, "min_lon": -180.0, "max_lon": 180.0}
        }
        
        self.region_var = tk.StringVar()
        region_combo = ttk.Combobox(preset_frame, textvariable=self.region_var, values=list(self.region_presets.keys()), width=15)
        region_combo.grid(row=0, column=1, padx=5)
        region_combo.bind("<<ComboboxSelected>>", self.on_region_selected)
        
        # Zaman Aralığı Çerçevesi
        time_frame = ttk.LabelFrame(main_frame, text="Zaman Aralığı", padding="10")
        time_frame.pack(fill=tk.X, pady=5)
        
        # Başlangıç tarihi
        start_date_frame = ttk.Frame(time_frame)
        start_date_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(start_date_frame, text="Başlangıç Tarihi (YYYY-MM-DD):").grid(row=0, column=0, sticky=tk.W, padx=5)
        
        # Bir hafta öncesini varsayılan olarak ayarla
        one_week_ago = (datetime.datetime.now() - datetime.timedelta(days=7)).strftime("%Y-%m-%d")
        self.start_date_var = tk.StringVar(value=one_week_ago)
        ttk.Entry(start_date_frame, textvariable=self.start_date_var, width=15).grid(row=0, column=1, padx=5)
        
        # Bitiş tarihi
        end_date_frame = ttk.Frame(time_frame)
        end_date_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(end_date_frame, text="Bitiş Tarihi (YYYY-MM-DD):").grid(row=0, column=0, sticky=tk.W, padx=5)
        
        # Bugünü varsayılan olarak ayarla
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        self.end_date_var = tk.StringVar(value=today)
        ttk.Entry(end_date_frame, textvariable=self.end_date_var, width=15).grid(row=0, column=1, padx=5)
        
        # Hazır zaman aralığı seçenekleri
        time_preset_frame = ttk.Frame(time_frame)
        time_preset_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(time_preset_frame, text="Hazır Zaman Aralığı:").grid(row=0, column=0, sticky=tk.W, padx=5)
        
        self.time_presets = {
            "Son 24 Saat": {"days": 1},
            "Son 7 Gün": {"days": 7},
            "Son 30 Gün": {"days": 30},
            "Son 90 Gün": {"days": 90},
            "Son 365 Gün": {"days": 365}
        }
        
        self.time_var = tk.StringVar()
        time_combo = ttk.Combobox(time_preset_frame, textvariable=self.time_var, values=list(self.time_presets.keys()), width=15)
        time_combo.grid(row=0, column=1, padx=5)
        time_combo.bind("<<ComboboxSelected>>", self.on_time_selected)
        
        # Büyüklük (Magnitude) Çerçevesi
        magnitude_frame = ttk.LabelFrame(main_frame, text="Deprem Büyüklüğü", padding="10")
        magnitude_frame.pack(fill=tk.X, pady=5)
        
        # Minimum büyüklük
        min_mag_frame = ttk.Frame(magnitude_frame)
        min_mag_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(min_mag_frame, text="Minimum Büyüklük:").grid(row=0, column=0, sticky=tk.W, padx=5)
        self.min_mag_var = tk.StringVar(value="0.0")
        ttk.Entry(min_mag_frame, textvariable=self.min_mag_var, width=10).grid(row=0, column=1, padx=5)
        
        # Maksimum büyüklük
        max_mag_frame = ttk.Frame(magnitude_frame)
        max_mag_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(max_mag_frame, text="Maksimum Büyüklük:").grid(row=0, column=0, sticky=tk.W, padx=5)
        self.max_mag_var = tk.StringVar(value="10.0")
        ttk.Entry(max_mag_frame, textvariable=self.max_mag_var, width=10).grid(row=0, column=1, padx=5)
        
        # Çıktı Dosyası Çerçevesi
        output_frame = ttk.LabelFrame(main_frame, text="Çıktı Dosyası", padding="10")
        output_frame.pack(fill=tk.X, pady=5)
        
        # Çıktı dosya adı
        output_file_frame = ttk.Frame(output_frame)
        output_file_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(output_file_frame, text="Çıktı Dosya Adı:").grid(row=0, column=0, sticky=tk.W, padx=5)
        self.output_var = tk.StringVar(value="emsc_earthquakes.csv")
        output_entry = ttk.Entry(output_file_frame, textvariable=self.output_var, width=30)
        output_entry.grid(row=0, column=1, padx=5)
        
        ttk.Button(output_file_frame, text="Gözat...", command=self.browse_output_file).grid(row=0, column=2, padx=5)
        
        # Durum çubuğu
        self.status_var = tk.StringVar(value="Hazır")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X, pady=5)
        
        # İlerleme çubuğu
        self.progress = ttk.Progressbar(main_frame, orient=tk.HORIZONTAL, length=100, mode='indeterminate')
        self.progress.pack(side=tk.BOTTOM, fill=tk.X, pady=5)
        
        # İndir butonu - Daha büyük ve belirgin
        download_frame = ttk.Frame(main_frame)
        download_frame.pack(fill=tk.X, pady=15)
        
        download_button = ttk.Button(
            download_frame, 
            text="DEPREM VERİLERİNİ İNDİR", 
            command=self.download_earthquakes,
            style="Download.TButton"
        )
        download_button.pack(ipadx=20, ipady=10, fill=tk.X)
        
        # Özel buton stili
        style = ttk.Style()
        style.configure("Download.TButton", font=("Arial", 12, "bold"))
    
    def on_region_selected(self, event):
        """Hazır bölge seçildiğinde koordinatları güncelle."""
        selected_region = self.region_var.get()
        if selected_region in self.region_presets:
            region = self.region_presets[selected_region]
            self.min_lat_var.set(str(region["min_lat"]))
            self.max_lat_var.set(str(region["max_lat"]))
            self.min_lon_var.set(str(region["min_lon"]))
            self.max_lon_var.set(str(region["max_lon"]))
    
    def on_time_selected(self, event):
        """Hazır zaman aralığı seçildiğinde tarihleri güncelle."""
        selected_time = self.time_var.get()
        if selected_time in self.time_presets:
            days = self.time_presets[selected_time]["days"]
            # Şu anki zamanı yerel zaman diliminde al
            end_date = datetime.datetime.now().replace(microsecond=0)
            start_date = end_date - datetime.timedelta(days=days)
            
            # Tarihleri YYYY-MM-DD formatında ayarla
            self.start_date_var.set(start_date.strftime("%Y-%m-%d"))
            self.end_date_var.set(end_date.strftime("%Y-%m-%d"))
    
    def browse_output_file(self):
        """Çıktı dosyası için dosya tarayıcısını aç."""
        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV Dosyaları", "*.csv"), ("Tüm Dosyalar", "*.*")],
            title="Deprem Verilerini Kaydet"
        )
        if filename:
            self.output_var.set(filename)
    
    def validate_inputs(self):
        """Kullanıcı girdilerini doğrula."""
        try:
            min_lat = float(self.min_lat_var.get())
            max_lat = float(self.max_lat_var.get())
            min_lon = float(self.min_lon_var.get())
            max_lon = float(self.max_lon_var.get())
            
            if min_lat < -90 or max_lat > 90 or min_lat >= max_lat:
                messagebox.showerror("Hata", "Geçersiz enlem değerleri. Enlem -90 ile 90 arasında olmalı ve minimum değer maksimum değerden küçük olmalıdır.")
                return False
            
            if min_lon < -180 or max_lon > 180 or min_lon >= max_lon:
                messagebox.showerror("Hata", "Geçersiz boylam değerleri. Boylam -180 ile 180 arasında olmalı ve minimum değer maksimum değerden küçük olmalıdır.")
                return False
            
            min_mag = float(self.min_mag_var.get())
            max_mag = float(self.max_mag_var.get())
            
            if min_mag < 0 or max_mag > 10 or min_mag >= max_mag:
                messagebox.showerror("Hata", "Geçersiz büyüklük değerleri. Büyüklük 0 ile 10 arasında olmalı ve minimum değer maksimum değerden küçük olmalıdır.")
                return False
            
            # Tarihleri doğrula
            start_date_str = self.start_date_var.get()
            end_date_str = self.end_date_var.get()
            
            try:
                validate_dates(start_date_str, end_date_str)
            except Exception as e:
                messagebox.showerror("Hata", f"Tarih doğrulama hatası: {e}")
                return False
            
            # Çıktı dosyasını doğrula
            output_file = self.output_var.get()
            if not output_file:
                messagebox.showerror("Hata", "Lütfen bir çıktı dosya adı belirtin.")
                return False
            
            return True
        except ValueError as e:
            messagebox.showerror("Hata", f"Giriş doğrulama hatası: {e}")
            return False
    
    def download_earthquakes(self):
        """Deprem verilerini indir."""
        if not self.validate_inputs():
            return
        
        # İlerleme çubuğunu başlat
        self.progress.start()
        self.status_var.set("Deprem verileri indiriliyor...")
        self.root.update()
        
        # İndirme işlemini ayrı bir iş parçacığında başlat
        threading.Thread(target=self._download_thread, daemon=True).start()
    
    def _download_thread(self):
        """Deprem verilerini indirme iş parçacığı."""
        try:
            min_lat = float(self.min_lat_var.get())
            max_lat = float(self.max_lat_var.get())
            min_lon = float(self.min_lon_var.get())
            max_lon = float(self.max_lon_var.get())
            min_mag = float(self.min_mag_var.get())
            max_mag = float(self.max_mag_var.get())
            
            start_date_str = self.start_date_var.get()
            end_date_str = self.end_date_var.get()
            output_file = self.output_var.get()
            
            start_date, end_date = validate_dates(start_date_str, end_date_str)
            
            # Deprem verilerini al
            earthquake_features = get_earthquake_data(
                min_lat, max_lat, 
                min_lon, max_lon,
                start_date, end_date,
                min_mag, max_mag
            )
            
            if not earthquake_features:
                self.root.after(0, lambda: messagebox.showinfo("Bilgi", "Belirtilen parametreler için deprem verisi bulunamadı."))
                self.root.after(0, lambda: self.status_var.set("Hazır"))
                self.root.after(0, self.progress.stop)
                return
            
            # Verileri işle
            df = process_earthquake_data(earthquake_features)
            
            if df is None or df.empty:
                self.root.after(0, lambda: messagebox.showerror("Hata", "Deprem verilerini işlerken bir hata oluştu."))
                self.root.after(0, lambda: self.status_var.set("Hazır"))
                self.root.after(0, self.progress.stop)
                return
            
            # CSV olarak kaydet
            success = save_to_csv(df, output_file)
            
            if success:
                self.root.after(0, lambda: messagebox.showinfo("Başarılı", f"{len(df)} deprem kaydı başarıyla {output_file} dosyasına kaydedildi."))
                self.root.after(0, lambda: self.status_var.set(f"{len(df)} deprem kaydı indirildi."))
            else:
                self.root.after(0, lambda: messagebox.showerror("Hata", "Deprem verilerini CSV dosyasına kaydederken bir hata oluştu."))
                self.root.after(0, lambda: self.status_var.set("Hata oluştu."))
            
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Hata", f"Deprem verilerini indirirken bir hata oluştu: {e}"))
            self.root.after(0, lambda: self.status_var.set("Hata oluştu."))
        finally:
            self.root.after(0, self.progress.stop)

def main():
    """Ana fonksiyon."""
    root = tk.Tk()
    app = EMSCEarthquakeGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
