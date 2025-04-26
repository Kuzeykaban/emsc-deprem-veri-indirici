#!/usr/bin/env python3
"""
EMSC Earthquake Data Downloader

This script downloads earthquake data from the EMSC (European-Mediterranean Seismological Centre) API
based on user-specified region and time interval, and saves it as a CSV file.
"""

import requests
import pandas as pd
import datetime
import argparse
import sys
import os
from dateutil import parser as date_parser

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Download earthquake data from EMSC API.')
    
    parser.add_argument('--min-lat', type=float, help='Minimum latitude of the region', required=True)
    parser.add_argument('--max-lat', type=float, help='Maximum latitude of the region', required=True)
    parser.add_argument('--min-lon', type=float, help='Minimum longitude of the region', required=True)
    parser.add_argument('--max-lon', type=float, help='Maximum longitude of the region', required=True)
    
    parser.add_argument('--start-date', type=str, help='Start date (YYYY-MM-DD or YYYY-MM-DD HH:MM:SS)', required=True)
    parser.add_argument('--end-date', type=str, help='End date (YYYY-MM-DD or YYYY-MM-DD HH:MM:SS)', required=True)
    
    parser.add_argument('--min-magnitude', type=float, help='Minimum earthquake magnitude', default=0.0)
    parser.add_argument('--max-magnitude', type=float, help='Maximum earthquake magnitude', default=10.0)
    
    parser.add_argument('--output', type=str, help='Output CSV file name', default='emsc_earthquakes.csv')
    
    return parser.parse_args()

def validate_dates(start_date_str, end_date_str):
    """Validate and parse date strings."""
    try:
        start_date = date_parser.parse(start_date_str)
        end_date = date_parser.parse(end_date_str)
        
        if end_date < start_date:
            print("Error: End date must be after start date.")
            sys.exit(1)
            
        # Check if the date range is not too large (EMSC API might have limitations)
        date_diff = (end_date - start_date).days
        if date_diff > 365:
            print("Warning: Date range is very large ({}). This might result in a large amount of data or API limitations.".format(date_diff))
            
        return start_date, end_date
    except Exception as e:
        print(f"Error parsing dates: {e}")
        sys.exit(1)

def format_date_for_api(date_obj):
    """Format datetime object for EMSC API.
    
    EMSC API expects dates in UTC timezone in ISO 8601 format.
    """
    # Ensure the datetime object is timezone-aware and in UTC
    if date_obj.tzinfo is None:
        # If the datetime object is naive (no timezone info), assume it's in local time
        # and convert to UTC
        local_tz = datetime.datetime.now().astimezone().tzinfo
        date_obj = date_obj.replace(tzinfo=local_tz).astimezone(datetime.timezone.utc)
    else:
        # If it already has timezone info, convert to UTC
        date_obj = date_obj.astimezone(datetime.timezone.utc)
    
    # Format in ISO 8601 format
    return date_obj.strftime("%Y-%m-%dT%H:%M:%SZ")

def get_earthquake_data(min_lat, max_lat, min_lon, max_lon, start_date, end_date, min_magnitude, max_magnitude):
    """
    Fetch earthquake data from EMSC API.
    
    The EMSC API endpoint for retrieving earthquake data is:
    https://www.seismicportal.eu/fdsnws/event/1/query
    """
    base_url = "https://www.seismicportal.eu/fdsnws/event/1/query"
    
    params = {
        'minlat': min_lat,
        'maxlat': max_lat,
        'minlon': min_lon,
        'maxlon': max_lon,
        'start': format_date_for_api(start_date),
        'end': format_date_for_api(end_date),
        'minmag': min_magnitude,
        'maxmag': max_magnitude,
        'format': 'json'
    }
    
    print(f"Fetching earthquake data from {start_date} to {end_date} for region: "
          f"Lat [{min_lat}, {max_lat}], Lon [{min_lon}, {max_lon}], "
          f"Magnitude [{min_magnitude}, {max_magnitude}]")
    
    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()  # Raise an exception for HTTP errors
        
        data = response.json()
        
        if 'features' not in data:
            print("No earthquake data found or unexpected API response format.")
            return None
            
        return data['features']
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from EMSC API: {e}")
        return None

def process_earthquake_data(earthquake_features):
    """Process earthquake data and convert to DataFrame."""
    if not earthquake_features:
        return None
        
    earthquakes = []
    
    for feature in earthquake_features:
        properties = feature.get('properties', {})
        geometry = feature.get('geometry', {})
        coordinates = geometry.get('coordinates', [0, 0, 0]) if geometry else [0, 0, 0]
        
        # API'den gelen zaman değeri
        time_str = properties.get('time', '')
        
        # Zaman değerini doğru şekilde işle
        try:
            if time_str:
                # ISO 8601 formatındaki tarihi ayrıştır
                time_obj = date_parser.parse(time_str)
                
                # Yerel zaman dilimine dönüştür
                if time_obj.tzinfo is not None:
                    local_tz = datetime.datetime.now().astimezone().tzinfo
                    time_obj = time_obj.astimezone(local_tz)
                    
                # Okunabilir formatta tarih dizesi oluştur
                formatted_time = time_obj.strftime("%Y-%m-%d %H:%M:%S")
            else:
                formatted_time = ""
        except Exception as e:
            print(f"Tarih ayrıştırma hatası: {e} - Orijinal değer: {time_str}")
            formatted_time = time_str
        
        earthquake = {
            'id': properties.get('source_id', ''),
            'time': formatted_time,  # Formatlanmış zaman değeri
            'original_time': time_str,  # Orijinal zaman değeri (hata ayıklama için)
            'latitude': coordinates[1],
            'longitude': coordinates[0],
            'depth': coordinates[2],
            'magnitude': properties.get('mag', 0),
            'magnitude_type': properties.get('magtype', ''),
            'region': properties.get('flynn_region', ''),
            'source': properties.get('source_id', '').split(':')[0] if properties.get('source_id', '') else ''
        }
        
        earthquakes.append(earthquake)
    
    return pd.DataFrame(earthquakes)

def save_to_csv(df, output_file):
    """Save DataFrame to CSV file."""
    try:
        df.to_csv(output_file, index=False)
        print(f"Successfully saved {len(df)} earthquake records to {output_file}")
        return True
    except Exception as e:
        print(f"Error saving to CSV: {e}")
        return False

def main():
    """Main function to run the script."""
    # Argüman sayısını kontrol et
    if len(sys.argv) == 1:
        # Hiç argüman verilmemişse, kullanıcıya seçenek sun
        print("EMSC Deprem Veri İndirici")
        print("==========================")
        print("Komut satırı argümanları sağlanmadı.")
        print("Seçenekler:")
        print("1. Grafik kullanıcı arayüzünü başlat")
        print("2. Komut satırı yardımını göster")
        print("3. Çıkış")
        
        try:
            choice = input("Seçiminiz (1-3): ")
            if choice == "1":
                try:
                    # GUI uygulamasını başlat
                    print("Grafik kullanıcı arayüzü başlatılıyor...")
                    import importlib.util
                    
                    # emsc_earthquake_gui.py dosyasının varlığını kontrol et
                    gui_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "emsc_earthquake_gui.py")
                    if os.path.exists(gui_path):
                        spec = importlib.util.spec_from_file_location("emsc_earthquake_gui", gui_path)
                        gui_module = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(gui_module)
                        gui_module.main()
                    else:
                        print("Hata: emsc_earthquake_gui.py dosyası bulunamadı.")
                        print("Lütfen emsc_earthquake_gui.py dosyasının bu script ile aynı dizinde olduğundan emin olun.")
                except Exception as e:
                    print(f"GUI başlatılırken bir hata oluştu: {e}")
                    print("Lütfen gerekli bağımlılıkların yüklü olduğundan emin olun (tkinter, pandas, requests, dateutil).")
            elif choice == "2":
                # Yardım mesajını göster
                print("\nKullanım:")
                print("python emsc_earthquake_data.py --min-lat 36.0 --max-lat 42.0 --min-lon 26.0 --max-lon 45.0 --start-date \"2023-01-01\" --end-date \"2023-01-31\" --output \"depremler.csv\"\n")
                print("Zorunlu parametreler:")
                print("  --min-lat MIN_LAT     Minimum enlem değeri")
                print("  --max-lat MAX_LAT     Maksimum enlem değeri")
                print("  --min-lon MIN_LON     Minimum boylam değeri")
                print("  --max-lon MAX_LON     Maksimum boylam değeri")
                print("  --start-date START    Başlangıç tarihi (YYYY-MM-DD)")
                print("  --end-date END        Bitiş tarihi (YYYY-MM-DD)")
                print("\nİsteğe bağlı parametreler:")
                print("  --min-magnitude MIN   Minimum deprem büyüklüğü (varsayılan: 0.0)")
                print("  --max-magnitude MAX   Maksimum deprem büyüklüğü (varsayılan: 10.0)")
                print("  --output OUTPUT       Çıktı CSV dosyası (varsayılan: emsc_earthquakes.csv)")
            else:
                print("Çıkılıyor...")
        except KeyboardInterrupt:
            print("\nİşlem kullanıcı tarafından iptal edildi.")
        
        return
    
    # Normal komut satırı işlemi
    args = parse_arguments()
    
    try:
        start_date, end_date = validate_dates(args.start_date, args.end_date)
        
        earthquake_features = get_earthquake_data(
            args.min_lat, args.max_lat, 
            args.min_lon, args.max_lon,
            start_date, end_date,
            args.min_magnitude, args.max_magnitude
        )
        
        if not earthquake_features:
            print("Belirtilen parametreler için deprem verisi bulunamadı.")
            sys.exit(1)
        
        df = process_earthquake_data(earthquake_features)
        
        if df is None or df.empty:
            print("Deprem verilerini işlerken bir hata oluştu.")
            sys.exit(1)
        
        print(f"{len(df)} deprem kaydı alındı.")
        
        success = save_to_csv(df, args.output)
        
        if not success:
            print("Deprem verilerini CSV dosyasına kaydederken bir hata oluştu.")
            sys.exit(1)
        
        print(f"Deprem verileri başarıyla {args.output} dosyasına kaydedildi.")
    except Exception as e:
        print(f"Bir hata oluştu: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
