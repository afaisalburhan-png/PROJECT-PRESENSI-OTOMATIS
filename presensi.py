
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, date, timedelta
import csv
import os
import math

GAJI_POKOK = 80000
TARIF_JAM = 10000
JAM_MASUK = 9 * 3600
JAM_PULANG = 17 * 3600
FILE_CSV = "rekap_presensi.csv"

KARYAWAN = {
    "Kartu A": {"uid": "01020304", "nama": "Andi"},
    "Kartu B": {"uid": "11223344", "nama": "Budi"},
    "Kartu C": {"uid": "55667788", "nama": "Citra"},
}

data_harian = {}
hari_aktif = date.today()
waktu_simulasi = 8 * 3600 + 50 * 60


def format_waktu(detik):
    jam = detik // 3600
    menit = (detik % 3600) // 60
    detik = detik % 60
    return f"{jam:02d}:{menit:02d}:{detik:02d}"


def format_rupiah(nilai):
    return "Rp" + f"{nilai:,}".replace(",", ".")


def hitung_potongan(masuk):
    terlambat = masuk - JAM_MASUK

    if terlambat <= 0:
        return 0

    blok_jam = math.ceil(terlambat / 3600)
    return min(blok_jam * TARIF_JAM, GAJI_POKOK)


def hitung_lembur(pulang):
    if pulang <= JAM_PULANG:
        return 0

    return (pulang - JAM_PULANG) // 3600


def simpan_csv(nama, uid, masuk, pulang,
               potongan, jam_lembur, total):
    file_baru = not os.path.exists(FILE_CSV)

    with open(FILE_CSV, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)

        if file_baru:
            writer.writerow([
                "Tanggal", "Nama", "UID", "Jam Masuk",
                "Jam Pulang", "Potongan", "Jam Lembur",
                "Total Gaji"
            ])

        writer.writerow([
            hari_aktif.isoformat(),
            nama,
            uid,
            format_waktu(masuk),
            format_waktu(pulang),
            potongan,
            jam_lembur,
            total
        ])


def perbarui_tampilan():
    jam_label.config(
        text=f"{format_waktu(waktu_simulasi)}  |  {hari_aktif}"
    )


def atur_waktu():
    global waktu_simulasi

    try:
        jam = datetime.strptime(
            input_jam.get().strip(), "%H:%M:%S"
        )
        waktu_simulasi = (
            jam.hour * 3600 + jam.minute * 60 + jam.second
        )
        perbarui_tampilan()
        status_label.config(text="Jam simulasi berhasil diubah.")
    except ValueError:
        messagebox.showerror(
            "Format salah",
            "Masukkan jam dengan format HH:MM:SS\n"
            "Contoh: 09:00:01"
        )


def tap_kartu(nama_kartu):
    global data_harian

    k = KARYAWAN[nama_kartu]
    uid = k["uid"]
    nama = k["nama"]

    if uid not in data_harian:
        data_harian[uid] = {
            "nama": nama,
            "masuk": None,
            "pulang": None,
        }

    data = data_harian[uid]

    # Tap pertama menjadi presensi masuk
    if data["masuk"] is None:
        if waktu_simulasi >= JAM_PULANG:
            status_label.config(
                text=f"{nama}: presensi masuk ditolak, "
                     "jam kerja sudah berakhir."
            )
            return

        data["masuk"] = waktu_simulasi
        potongan = hitung_potongan(waktu_simulasi)

        status_label.config(
            text=f"{nama} berhasil tap masuk pukul "
                 f"{format_waktu(waktu_simulasi)}. "
                 f"Potongan: {format_rupiah(potongan)}"
        )

    # Kartu sudah masuk dan belum pulang
    elif data["pulang"] is None:
        if waktu_simulasi < JAM_PULANG:
            status_label.config(
                text=f"{nama}: tap pulang ditolak. "
                     "Tap pulang hanya boleh mulai pukul 17:00."
            )
            return

        data["pulang"] = waktu_simulasi
        selesaikan_presensi(uid)

    else:
        status_label.config(
            text=f"{nama} sudah menyelesaikan presensi hari ini."
        )

    perbarui_tabel()


def selesaikan_presensi(uid, otomatis=False):
    data = data_harian[uid]
    masuk = data["masuk"]
    pulang = data["pulang"]
    potongan = hitung_potongan(masuk)
    jam_lembur = hitung_lembur(pulang)
    upah_lembur = jam_lembur * TARIF_JAM
    total = GAJI_POKOK - potongan + upah_lembur

    simpan_csv(
        data["nama"], uid, masuk, pulang,
        potongan, jam_lembur, total
    )

    tambahan = (
        " Pulang otomatis pukul 17:00."
        if otomatis else ""
    )

    status_label.config(
        text=f"{data['nama']} selesai presensi. "
             f"Total gaji: {format_rupiah(total)}.{tambahan}"
    )

    messagebox.showinfo(
        "Rincian Gaji",
        f"Nama: {data['nama']}\n"
        f"Jam masuk: {format_waktu(masuk)}\n"
        f"Jam pulang: {format_waktu(pulang)}\n"
        f"Gaji pokok: {format_rupiah(GAJI_POKOK)}\n"
        f"Potongan: {format_rupiah(potongan)}\n"
        f"Lembur: {jam_lembur} jam penuh\n"
        f"Upah lembur: {format_rupiah(upah_lembur)}\n"
        f"TOTAL GAJI: {format_rupiah(total)}"
    )


def perbarui_tabel():
    for item in tabel.get_children():
        tabel.delete(item)

    for uid, data in data_harian.items():
        masuk = (
            format_waktu(data["masuk"])
            if data["masuk"] is not None else "-"
        )
        pulang = (
            format_waktu(data["pulang"])
            if data["pulang"] is not None else "-"
        )

        if data["pulang"] is not None:
            total = (
                GAJI_POKOK
                - hitung_potongan(data["masuk"])
                + hitung_lembur(data["pulang"]) * TARIF_JAM
            )
            gaji = format_rupiah(total)
        else:
            gaji = "Belum selesai"

        tabel.insert(
            "", "end",
            values=(data["nama"], masuk, pulang, gaji)
        )


def tutup_hari():
    global data_harian, hari_aktif, waktu_simulasi

    for uid, data in list(data_harian.items()):
        if data["masuk"] is not None and data["pulang"] is None:
            data["pulang"] = JAM_PULANG
            selesaikan_presensi(uid, otomatis=True)

    data_harian = {}
    hari_aktif += timedelta(days=1)
    waktu_simulasi = 0

    perbarui_tampilan()
    perbarui_tabel()
    status_label.config(text="Hari baru dimulai pukul 00:00:00.")


root = tk.Tk()
root.title("Simulasi Presensi Karyawan")
root.geometry("800x600")
root.minsize(700, 500)

judul = tk.Label(
    root,
    text="MESIN PRESENSI KARYAWAN",
    font=("Arial", 20, "bold")
)
judul.pack(pady=(15, 5))

tk.Label(
    root,
    text="SIMULASI KARTU RFID • PYTHON",
    font=("Arial", 10)
).pack()

jam_label = tk.Label(
    root, text="", font=("Arial", 18, "bold")
)
jam_label.pack(pady=12)

frame_jam = ttk.Frame(root)
frame_jam.pack(pady=3)

ttk.Label(frame_jam, text="Atur waktu (HH:MM:SS):").pack(
    side="left", padx=5
)

input_jam = ttk.Entry(frame_jam, width=12)
input_jam.insert(0, "08:50:00")
input_jam.pack(side="left", padx=5)

ttk.Button(
    frame_jam, text="Atur Jam", command=atur_waktu
).pack(side="left", padx=5)

tk.Label(
    root,
    text="Pilih kartu virtual untuk melakukan tap:",
    font=("Arial", 11, "bold")
).pack(pady=(15, 5))

frame_kartu = ttk.Frame(root)
frame_kartu.pack(pady=5)

for kartu, info in KARYAWAN.items():
    ttk.Button(
        frame_kartu,
        text=f"💳 {kartu}\n{info['nama']}\nTAP KARTU",
        command=lambda nama=kartu: tap_kartu(nama),
        width=18
    ).pack(side="left", padx=8, ipady=12)

status_label = tk.Label(
    root,
    text="Sistem siap. Silakan pilih kartu.",
    wraplength=700,
    font=("Arial", 10)
)
status_label.pack(pady=12)

tk.Label(
    root,
    text="REKAP PRESENSI HARI INI",
    font=("Arial", 12, "bold")
).pack(pady=(5, 5))

kolom = ("Nama", "Jam Masuk", "Jam Pulang", "Total Gaji")
tabel = ttk.Treeview(
    root, columns=kolom, show="headings", height=8
)

for nama_kolom in kolom:
    tabel.heading(nama_kolom, text=nama_kolom)
    tabel.column(nama_kolom, anchor="center", width=170)

tabel.pack(fill="both", expand=True, padx=15, pady=(0, 10))

ttk.Button(
    root, text="Tutup Hari / Simulasikan Tengah Malam",
    command=tutup_hari
).pack(pady=(0, 12))

perbarui_tampilan()
root.mainloop()