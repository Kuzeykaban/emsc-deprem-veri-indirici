# EMSC Deprem Veri İndirici

Bu proje, EMSC (Avrupa-Akdeniz Sismoloji Merkezi) API'sinden deprem verilerini indirmek için kullanılan bir araçtır. Kullanıcılar, belirli bir bölge ve zaman aralığı için deprem verilerini CSV formatında indirebilirler.

Proje iki farklı kullanım seçeneği sunar:
1. Komut satırı arayüzü (`emsc_earthquake_data.py`)
2. Grafik kullanıcı arayüzü (`emsc_earthquake_gui.py`)

## Özellikler

- Belirli bir coğrafi bölge için deprem verilerini indirme (enlem/boylam koordinatları ile)
- Belirli bir zaman aralığı için deprem verilerini filtreleme
- Minimum ve maksimum deprem büyüklüğüne göre filtreleme
- Verileri CSV formatında kaydetme
- Kullanıcı dostu grafik arayüzü
- Hazır bölge seçenekleri (Türkiye, İstanbul, İzmir, Ankara, Dünya)
- Hazır zaman aralığı seçenekleri (Son 24 saat, Son 7 gün, vb.)

## Gereksinimler

Bu projeyi çalıştırmak için aşağıdaki Python paketlerine ihtiyacınız vardır:

- Python 3.6 veya üzeri
- requests
- pandas
- python-dateutil
- tkinter (GUI için)

## Kurulum

1. Bu depoyu klonlayın veya indirin:
```
git clone https://github.com/Kuzeykaban/emsc-deprem-veri-indirici.git
```
veya sağ kısımdaki releases bölümünden indirin

2. Gerekli paketleri yükleyin:
```
pip install -r requirements.txt
```

## Kullanım

### Komut Satırı Arayüzü

Komut satırı arayüzünü kullanmak için:

```bash
python emsc_earthquake_data.py --min-lat 36.0 --max-lat 42.0 --min-lon 26.0 --max-lon 45.0 --start-date "2023-01-01" --end-date "2023-01-31" --output "turkiye_ocak_2023.csv"
```

#### Parametreler:

- `--min-lat`: Minimum enlem değeri (zorunlu)
- `--max-lat`: Maksimum enlem değeri (zorunlu)
- `--min-lon`: Minimum boylam değeri (zorunlu)
- `--max-lon`: Maksimum boylam değeri (zorunlu)
- `--start-date`: Başlangıç tarihi, YYYY-MM-DD formatında (zorunlu)
- `--end-date`: Bitiş tarihi, YYYY-MM-DD formatında (zorunlu)
- `--min-magnitude`: Minimum deprem büyüklüğü (isteğe bağlı, varsayılan: 0.0)
- `--max-magnitude`: Maksimum deprem büyüklüğü (isteğe bağlı, varsayılan: 10.0)
- `--output`: Çıktı CSV dosyasının adı (isteğe bağlı, varsayılan: "emsc_earthquakes.csv")

### Grafik Kullanıcı Arayüzü

Grafik arayüzü kullanmak için:

```bash
python emsc_earthquake_gui.py
```

GUI uygulaması, aşağıdaki özellikleri sunar:

1. Bölge koordinatlarını (enlem/boylam) manuel olarak giriş
2. Hazır bölge seçenekleri (Türkiye, İstanbul, İzmir, Ankara, Dünya)
3. Başlangıç ve bitiş tarihlerini manuel olarak giriş
4. Hazır zaman aralığı seçenekleri (Son 24 saat, Son 7 gün, Son 30 gün, vb.)
5. Minimum ve maksimum deprem büyüklüğü filtreleme
6. Çıktı dosyasını seçme
7. İlerleme göstergesi ve durum bildirimleri

## Örnek Kullanım Senaryoları

### Senaryo 1: Türkiye'deki Son 7 Günün Depremleri

Komut satırı:
```bash
python emsc_earthquake_data.py --min-lat 36.0 --max-lat 42.0 --min-lon 26.0 --max-lon 45.0 --start-date "$(date -d '7 days ago' '+%Y-%m-%d')" --end-date "$(date '+%Y-%m-%d')" --output "turkiye_son_7_gun.csv"
```

### Senaryo 2: İstanbul'daki 5.0 ve Üzeri Büyüklükteki Depremler (2020-2023)

Komut satırı:
```bash
python emsc_earthquake_data.py --min-lat 40.8 --max-lat 41.3 --min-lon 28.5 --max-lon 29.5 --start-date "2020-01-01" --end-date "2023-12-31" --min-magnitude 5.0 --output "istanbul_buyuk_depremler.csv"
```

## Çıktı Formatı

İndirilen CSV dosyası aşağıdaki sütunları içerir:

- `id`: Deprem kimliği
- `time`: Deprem zamanı (UTC)
- `latitude`: Enlem
- `longitude`: Boylam
- `depth`: Derinlik (km)
- `magnitude`: Büyüklük
- `magnitude_type`: Büyüklük tipi (örn. ML, MW)
- `region`: Bölge adı
- `source`: Veri kaynağı

## Notlar

- EMSC API'si, çok büyük zaman aralıkları için sınırlamalar getirebilir. Bir yıldan uzun süreli sorgularda uyarı alabilirsiniz.
- Coğrafi bölge ne kadar büyükse, o kadar çok veri indirilebilir ve işlem o kadar uzun sürebilir.

## Lisans

Bu proje MIT lisansı altında lisanslanmıştır. Daha fazla bilgi için `LICENSE` dosyasına bakın.

## İletişim

Sorularınız veya önerileriniz için lütfen bir issue açın veya e-posta gönderin.
