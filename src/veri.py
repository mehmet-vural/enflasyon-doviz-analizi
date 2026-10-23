"""Enflasyon ve döviz verisini açık kaynaklardan çeker, veri/ klasörüne kaydeder.

Kaynaklar (ikisi de ücretsiz, API anahtarı gerekmez):
- Dünya Bankası: yıllık TÜFE enflasyonu (FP.CPI.TOTL.ZG)
- Frankfurter (Avrupa Merkez Bankası referans kurları): günlük USD/TRY, EUR/TRY
"""

from pathlib import Path

import pandas as pd
import requests

VERI_KLASORU = Path(__file__).resolve().parent.parent / "veri"
ULKELER = {"TUR": "Türkiye", "USA": "ABD", "EMU": "Euro Bölgesi"}


def enflasyon_cek(baslangic: int = 2005, bitis: int = 2025) -> pd.DataFrame:
    """Yıllık TÜFE enflasyonu (%), satırlar yıl, sütunlar ülke."""
    url = (
        "https://api.worldbank.org/v2/country/"
        f"{';'.join(ULKELER)}/indicator/FP.CPI.TOTL.ZG"
        f"?format=json&date={baslangic}:{bitis}&per_page=500"
    )
    kayitlar = requests.get(url, timeout=30).json()[1]
    df = pd.DataFrame(
        {
            "yil": int(k["date"]),
            "ulke": ULKELER[k["countryiso3code"]],
            "enflasyon": k["value"],
        }
        for k in kayitlar
    )
    return df.pivot(index="yil", columns="ulke", values="enflasyon").sort_index()


def kur_cek(baslangic: str = "2005-01-01", bitis: str = "2025-12-31") -> pd.DataFrame:
    """Günlük USD/TRY ve EUR/TRY kurları (ECB referans kuru)."""
    url = f"https://api.frankfurter.dev/v1/{baslangic}..{bitis}?from=USD&to=TRY,EUR"
    oranlar = requests.get(url, timeout=60).json()["rates"]
    df = pd.DataFrame(oranlar).T
    df.index = pd.to_datetime(df.index)
    df = df.sort_index()
    return pd.DataFrame(
        {"USD/TRY": df["TRY"], "EUR/TRY": df["TRY"] / df["EUR"]},
        index=df.index.rename("tarih"),
    )


def veriyi_yukle(yenile: bool = False) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Kayıtlı veriyi okur; yoksa (ya da yenile=True ise) internetten çekip kaydeder."""
    enf_dosya = VERI_KLASORU / "enflasyon_yillik.csv"
    kur_dosya = VERI_KLASORU / "kur_gunluk.csv"
    if yenile or not (enf_dosya.exists() and kur_dosya.exists()):
        VERI_KLASORU.mkdir(exist_ok=True)
        enflasyon_cek().round(3).to_csv(enf_dosya)
        kur_cek().round(4).to_csv(kur_dosya)
    enflasyon = pd.read_csv(enf_dosya, index_col="yil")
    kur = pd.read_csv(kur_dosya, index_col="tarih", parse_dates=True)
    return enflasyon, kur


if __name__ == "__main__":
    enf, kur = veriyi_yukle(yenile=True)
    print(enf.tail())
    print(kur.tail())
