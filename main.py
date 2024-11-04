from config import API_TOKEN
import telebot
import re
from datetime import datetime
import json
import os
import uuid

# Inisialisasi bot dengan API_TOKEN yang diimpor dari file config
bot = telebot.TeleBot(token=API_TOKEN)

# Variabel global untuk menyimpan data sementara pengguna selama proses interaksi
user_data = {}

# Handler untuk command '/start', memberikan pesan selamat datang kepada pengguna
@bot.message_handler(commands=['start'])
def start_message(message):
    bot.send_message(message.chat.id, 'Selamat datang! \nTerima kasih telah menggunakan layanan kami. Siap mencatat aktivitasmu hari ini?\n\nKlik /activitylog untuk memulai!')

# Handler untuk command '/activitylog', memulai proses pencatatan aktivitas
@bot.message_handler(commands=['activitylog'])
def choose_activity_type(message):
    user_data.clear()
    markup = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True)
    markup.add('Dengan Pelanggan', 'Tanpa Pelanggan')
    bot.send_message(message.chat.id, 'Silakan pilih tipe aktivitas:', reply_markup=markup)
    bot.register_next_step_handler(message, process_activity_choice)

# Proses pilihan tipe aktivitas yang dipilih pengguna
def process_activity_choice(message):
    activity_type = message.text
    user_data['activity_type'] = activity_type
    # Jika aktivitas tanpa pelanggan, hapus project_id (jika ada)
    if activity_type == 'Tanpa Pelanggan':
        if 'project_id' in user_data:
            del user_data['project_id']
    
    # Jika aktivitas dengan pelanggan, lanjutkan proses ke input data pelanggan
    if activity_type == 'Dengan Pelanggan':
        # Lanjut ke input aktivitas dengan pelanggan
        ask_customer_contact(message)

    # Jika aktivitas tanpa pelanggan, lanjutkan proses ke input aktivitas internal
    elif activity_type == 'Tanpa Pelanggan':
        ask_internal_activity_type(message)
    else:
        bot.send_message(message.chat.id, 'Pilihan tidak valid! Silakan pilih "Dengan Pelanggan" atau "Tanpa Pelanggan".')
        bot.register_next_step_handler(message, process_activity_choice)
        
# Meminta kontak pelanggan jika aktivitas melibatkan pelanggan
def ask_customer_contact(message):
    bot.send_message(message.chat.id, 'Silakan masukkan kontak pelanggan (Nama/NIK):')
    bot.register_next_step_handler(message, process_customer_contact)

# Proses penyimpanan kontak pelanggan
def process_customer_contact(message):
    user_data['customer_contact'] = message.text
    ask_customer_feedback(message)

# Meminta feedback pelanggan (opsional)
def ask_customer_feedback(message):
    markup = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True)
    markup.add("Ya", "Tidak")
    bot.send_message(message.chat.id, "Apakah Anda ingin memberikan suara pelanggan? (Ya/Tidak) ", reply_markup=markup)
    bot.register_next_step_handler(message, process_customer_feedback)

# Proses penyimpanan feedback pelanggan
def process_customer_feedback(message):
    if message.text.lower() == 'ya':
        bot.send_message(message.chat.id, 'Silakan masukkan suara pelanggan:')
        bot.register_next_step_handler(message, process_feedback)
    else:
        user_data['customer_feedback'] = 'N/A'
        ask_customer_name(message) 

# Proses penyimpanan feedback dari pelanggan
def process_feedback(message):
    user_data['customer_feedback'] = message.text
    # ask_attachment(message)
    ask_customer_name(message) 

# Meminta input nama pelanggan
def ask_customer_name(message):
    bot.send_message(message.chat.id, 'Masukkan nama pelanggan:')
    bot.register_next_step_handler(message, process_customer_name)

# Proses penyimpanan nama pelanggan
def process_customer_name(message):
    user_data['customer_name'] = message.text
    markup = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True)
    markup.add("Tanpa Proyek", "Dengan Proyek")
    bot.send_message(message.chat.id, "Apakah aktivitas ini terkait proyek?", reply_markup=markup)
    bot.register_next_step_handler(message, process_project_type)

# Memproses pilihan apakah aktivitas terkait proyek atau tidak
def process_project_type(message):
    if message.text == "Tanpa Proyek":
        if 'project_id' in user_data:
            del user_data['project_id']  # Hapus project_id jika tidak ada proyek
        process_activity_no_project(message)
    elif message.text == "Dengan Proyek":
        ask_project_id(message)

# Proses untuk aktivitas tanpa proyek
def process_activity_no_project(message):
    activity_options = ["Kunjungan", "Rapat", "Survey", "Submit Penawaran", "Negosiasi", 
                        "Follow-up", "Administrasi", "Rekonsiliasi", "Dealing Kontrak", 
                        "Penanganan Gangguan", "Penanganan Invoice", "Lainnya"]
    markup = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True)
    for option in activity_options:
        markup.add(option)
    bot.send_message(message.chat.id, "Pilih tipe aktivitas:", reply_markup=markup)
    bot.register_next_step_handler(message, process_activity_type_no_project)

# Proses penyimpanan tipe aktivitas tanpa proyek
def process_activity_type_no_project(message):
    activity_type = message.text
    if activity_type == "Lainnya":
        bot.send_message(message.chat.id, "Silakan masukkan nama aktivitas secara manual:")
        bot.register_next_step_handler(message, process_manual_activity_no_project)
    else:
        user_data['activity_type'] = activity_type
        ask_date_start(message)

# Proses input aktivitas manual untuk tipe tanpa proyek
def process_manual_activity_no_project(message):
    user_data['activity_type'] = message.text
    ask_date_start(message)

# Proses input ID proyek
def ask_project_id(message):
    bot.send_message(message.chat.id, "Masukkan ID Proyek:")
    bot.register_next_step_handler(message, process_project_id)

# Proses penyimpanan ID proyek
def process_project_id(message):
    user_data['project_id'] = message.text
    process_activity_with_project(message)

# Proses untuk aktivitas dengan proyek
def process_activity_with_project(message):
    activity_options = ["Kunjungan", "Rapat", "Survey", "Submit Penawaran", "Negosiasi", 
                        "Follow-up", "Administrasi", "Rekonsiliasi", "Dealing Kontrak", 
                        "Penanganan Gangguan", "Penanganan Invoice", "Lainnya"]
    markup = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True)
    for option in activity_options:
        markup.add(option)
    bot.send_message(message.chat.id, "Pilih tipe aktivitas:", reply_markup=markup)
    bot.register_next_step_handler(message, process_activity_type_with_project)

# Proses penyimpanan tipe aktivitas dengan proyek
def process_activity_type_with_project(message):
    activity_type = message.text
    if activity_type == "Lainnya":
        bot.send_message(message.chat.id, "Silakan masukkan nama aktivitas secara manual:")
        bot.register_next_step_handler(message, process_manual_activity_with_project)
    else:
        user_data['activity_type'] = activity_type
        ask_date_start(message)

# Proses input aktivitas manual untuk tipe dengan proyek
def process_manual_activity_with_project(message):
    user_data['activity_type'] = message.text
    ask_date_start(message)

# Meminta input tipe aktivitas internal
def ask_internal_activity_type(message):
    activity_options = ["Koordinasi Internal", "Coaching dengan atasan", "Administrasi", "Pelatihan", "Pendekatan Pelanggan Baru", "Lainnya"]
    markup = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True)
    for option in activity_options:
        markup.add(option)
    bot.send_message(message.chat.id, "Pilih tipe aktivitas:", reply_markup=markup)
    bot.register_next_step_handler(message, process_activity_type_internal)

# Proses penyimpanan tipe aktivitas internal
def process_activity_type_internal(message):
    activity_type = message.text
    if activity_type == "Lainnya":
        bot.send_message(message.chat.id, "Silakan masukkan nama aktivitas secara manual:")
        bot.register_next_step_handler(message, process_manual_activity_internal)
    else:
        user_data['activity_type'] = activity_type
        ask_date_start(message)

# Proses input aktivitas manual untuk tipe internal
def process_manual_activity_internal(message):
    user_data['activity_type'] = message.text
    ask_date_start(message)


from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime

# Data bulan dalam bahasa Indonesia
MONTHS = [
    "Januari", "Februari", "Maret", "April", "Mei", "Juni",
    "Juli", "Agustus", "September", "Oktober", "November", "Desember"
]

# Meminta input tanggal mulai kegiatan
def ask_date_start(message):
    days = range(1, 32)  # Tanggal dari 1 hingga 31
    markup = InlineKeyboardMarkup(row_width=8)  # Atur jumlah kolom per baris menjadi 8
    buttons = [InlineKeyboardButton(str(day), callback_data=f"start_day_{day:02d}") for day in days]
    markup.add(*buttons)
    bot.send_message(message.chat.id, 'Pilih tanggal mulai kegiatan:', reply_markup=markup)

# Proses callback tanggal mulai
@bot.callback_query_handler(func=lambda call: call.data.startswith("start_day_"))
def process_start_day(call):
    day = call.data.split("_")[2]
    user_data['start_day'] = day
    ask_start_month(call.message)

# Meminta input bulan mulai kegiatan dengan nama bulan
def ask_start_month(message):
    markup = InlineKeyboardMarkup(row_width=3)  # Atur jumlah kolom per baris menjadi 3
    buttons = [InlineKeyboardButton(month, callback_data=f"start_month_{i:02d}") for i, month in enumerate(MONTHS, start=1)]
    markup.add(*buttons)
    bot.send_message(message.chat.id, 'Pilih bulan mulai kegiatan:', reply_markup=markup)

# Proses callback bulan mulai
@bot.callback_query_handler(func=lambda call: call.data.startswith("start_month_"))
def process_start_month(call):
    month = call.data.split("_")[2]
    user_data['start_month'] = month
    ask_start_year(call.message)

# Meminta input tahun mulai kegiatan
def ask_start_year(message):
    current_year = datetime.now().year
    years = range(current_year, current_year + 6)  # Rentang tahun
    markup = InlineKeyboardMarkup(row_width=3)  # Langsung atur jumlah kolom per baris
    buttons = [InlineKeyboardButton(str(year), callback_data=f"start_year_{year}") for year in years]
    markup.add(*buttons)
    bot.send_message(message.chat.id, 'Pilih tahun mulai kegiatan:', reply_markup=markup)

# Proses callback tahun mulai
@bot.callback_query_handler(func=lambda call: call.data.startswith("start_year_"))
def process_start_year(call):
    year = call.data.split("_")[2]
    user_data['start_year'] = year
    ask_start_time(call.message)

# Meminta input jam mulai kegiatan
def ask_start_time(message):
    hours = range(0, 24)  # Jam dari 0 hingga 23
    markup = InlineKeyboardMarkup(row_width=8)  # Atur jumlah kolom per baris menjadi 8
    buttons = [InlineKeyboardButton(f"{hour:02d}", callback_data=f"start_hour_{hour:02d}") for hour in hours]
    markup.add(*buttons)
    bot.send_message(message.chat.id, 'Pilih jam mulai kegiatan:', reply_markup=markup)

# Proses callback jam mulai
@bot.callback_query_handler(func=lambda call: call.data.startswith("start_hour_"))
def process_start_hour(call):
    hour = call.data.split("_")[2]
    user_data['start_hour'] = hour
    ask_start_minute(call.message)

# Meminta input menit mulai kegiatan dengan 10 kolom per baris
def ask_start_minute(message):
    minutes = range(0, 60, 5)  # Rentang menit tiap 5 menit (0, 5, 10, ..., 55)
    markup = InlineKeyboardMarkup(row_width=8)  # Atur jumlah kolom per baris menjadi 8
    buttons = [InlineKeyboardButton(f"{minute:02d}", callback_data=f"start_minute_{minute:02d}") for minute in minutes]
    markup.add(*buttons)
    bot.send_message(message.chat.id, 'Pilih menit mulai kegiatan:', reply_markup=markup)

# Proses callback menit mulai
@bot.callback_query_handler(func=lambda call: call.data.startswith("start_minute_"))
def process_start_minute(call):
    minute = call.data.split("_")[2]
    user_data['start_minute'] = minute
    confirm_start_datetime(call.message)

# Konfirmasi tanggal dan waktu mulai
def confirm_start_datetime(message):
    start_date = f"{user_data['start_day']}-{user_data['start_month']}-{user_data['start_year']}"
    start_time = f"{user_data['start_hour']}:{user_data['start_minute']}"
    user_data['start_date'] = start_date
    user_data['start_time'] = start_time
    bot.send_message(message.chat.id, f"Mulai kegiatan: {start_date} pada {start_time}")
    ask_end_date(message)  # Lanjut ke input tanggal berakhir

# Meminta input tanggal berakhir kegiatan dengan 8 kolom per baris
def ask_end_date(message):
    days = range(1, 32)  # Tanggal dari 1 hingga 31
    markup = InlineKeyboardMarkup(row_width=8)  # Atur jumlah kolom per baris menjadi 8
    buttons = [InlineKeyboardButton(str(day), callback_data=f"end_day_{day:02d}") for day in days]
    markup.add(*buttons)
    bot.send_message(message.chat.id, 'Pilih tanggal berakhir kegiatan:', reply_markup=markup)

# Proses callback tanggal berakhir
@bot.callback_query_handler(func=lambda call: call.data.startswith("end_day_"))
def process_end_day(call):
    day = call.data.split("_")[2]
    user_data['end_day'] = day
    ask_end_month(call.message)

# Meminta input bulan berakhir kegiatan dengan nama bulan
def ask_end_month(message):
    markup = InlineKeyboardMarkup(row_width=3)  # Atur jumlah kolom per baris menjadi 3
    buttons = [InlineKeyboardButton(month, callback_data=f"end_month_{i:02d}") for i, month in enumerate(MONTHS, start=1)]
    markup.add(*buttons)
    bot.send_message(message.chat.id, 'Pilih bulan berakhir kegiatan:', reply_markup=markup)

# Proses callback bulan berakhir
@bot.callback_query_handler(func=lambda call: call.data.startswith("end_month_"))
def process_end_month(call):
    month = call.data.split("_")[2]
    user_data['end_month'] = month
    ask_end_year(call.message)

# Meminta input tahun berakhir kegiatan
def ask_end_year(message):
    current_year = datetime.now().year
    years = range(current_year, current_year + 6)  # Rentang tahun
    markup = InlineKeyboardMarkup(row_width=3)  # Langsung atur jumlah kolom per baris
    buttons = [InlineKeyboardButton(str(year), callback_data=f"end_year_{year}") for year in years]
    markup.add(*buttons)
    bot.send_message(message.chat.id, 'Pilih tahun berakhir kegiatan:', reply_markup=markup)

# Proses callback tahun berakhir
@bot.callback_query_handler(func=lambda call: call.data.startswith("end_year_"))
def process_end_year(call):
    year = call.data.split("_")[2]
    user_data['end_year'] = year
    ask_end_time(call.message)

# Meminta input jam berakhir
def ask_end_time(message):
    hours = range(0, 24)  # Jam dari 0 hingga 23
    markup = InlineKeyboardMarkup(row_width=8)  # Atur jumlah kolom per baris menjadi 10
    buttons = [InlineKeyboardButton(f"{hour:02d}", callback_data=f"end_hour_{hour:02d}") for hour in hours]
    markup.add(*buttons)
    bot.send_message(message.chat.id, 'Pilih jam berakhir kegiatan:', reply_markup=markup)

# Proses callback jam berakhir
@bot.callback_query_handler(func=lambda call: call.data.startswith("end_hour_"))
def process_end_hour(call):
    hour = call.data.split("_")[2]
    user_data['end_hour'] = hour
    ask_end_minute(call.message)

# Meminta input menit berakhir kegiatan dengan 8 kolom per baris
def ask_end_minute(message):
    minutes = range(0, 60, 5)  # Rentang menit tiap 5 menit (0, 5, 10, ..., 55)
    markup = InlineKeyboardMarkup(row_width=8)  # Atur jumlah kolom per baris menjadi 8
    buttons = [InlineKeyboardButton(f"{minute:02d}", callback_data=f"end_minute_{minute:02d}") for minute in minutes]
    markup.add(*buttons)
    bot.send_message(message.chat.id, 'Pilih menit berakhir kegiatan:', reply_markup=markup)

# Proses callback menit berakhir
@bot.callback_query_handler(func=lambda call: call.data.startswith("end_minute_"))
def process_end_minute(call):
    minute = call.data.split("_")[2]
    user_data['end_minute'] = minute
    confirm_end_datetime(call.message)

# Konfirmasi tanggal dan waktu berakhir
def confirm_end_datetime(message):
    end_date = f"{user_data['end_day']}-{user_data['end_month']}-{user_data['end_year']}"
    end_time = f"{user_data['end_hour']}:{user_data['end_minute']}"
    user_data['end_date'] = end_date
    user_data['end_time'] = end_time
    bot.send_message(message.chat.id, f"Berakhir kegiatan: {end_date} pada {end_time}")
    ask_notes(message)

# meminta inputan catatan
def ask_notes(message):
    bot.send_message(message.chat.id, 'Silakan masukkan catatan tambahan:')
    bot.register_next_step_handler(message, process_notes)

# proses penyimpanan catatan
def process_notes(message):
    user_data['notes'] = message.text
    ask_attachment(message)

# meminta inputan lampiran   
def ask_attachment(message):
    markup = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True)
    markup.add("Ya", "Tidak")
    bot.send_message(message.chat.id, "Apakah Anda ingin melampirkan file? (Ya/Tidak)", reply_markup=markup)
    bot.register_next_step_handler(message, process_attachment)

# proses lampiran
def process_attachment(message):
    if message.text.lower() == 'ya':
        bot.send_message(message.chat.id, 'Silakan kirim file lampiran Anda:')
        bot.register_next_step_handler(message, process_file_attachment)
    else:
        confirm_and_save(message)

# proses penyimpanan file 
def process_file_attachment(message):
    if message.document:  # Jika ada lampiran dokumen
        file_info = bot.get_file(message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        # Membuat folder "uploads" jika belum ada
        folder_path = 'uploads'
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
        
        # Generate nama file unik dan simpan file
        file_extension = os.path.splitext(file_info.file_path)[1]
        file_name = str(uuid.uuid4()) + file_extension
        file_path = os.path.join(folder_path, file_name)
        
        with open(file_path, 'wb') as new_file:
            new_file.write(downloaded_file)

        user_data['attachment'] = file_path  # Simpan path file lokal
        bot.send_message(message.chat.id, 'File berhasil diterima dan disimpan!')
        confirm_and_save(message)
    
    elif message.photo:  # Jika ada gambar
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        # Membuat folder "uploads" jika belum ada
        folder_path = 'uploads'
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
        
        # Generate nama file unik dan simpan file gambar
        file_name = str(uuid.uuid4()) + ".jpg"
        file_path = os.path.join(folder_path, file_name)
        
        with open(file_path, 'wb') as new_file:
            new_file.write(downloaded_file)
        
        user_data['attachment'] = file_path  # Simpan path gambar lokal
        bot.send_message(message.chat.id, 'Gambar berhasil diterima dan disimpan!')
        confirm_and_save(message)
    
    else:
        bot.send_message(message.chat.id, 'Mohon kirim file lampiran yang valid.')
        bot.register_next_step_handler(message, process_file_attachment)

# proses konfirmasi
def confirm_and_save(message):
    user_id = message.from_user.id  # Ambil ID pengguna
    username = message.from_user.username or "tidak ada"  # Ambil username, jika ada

    # Tampilkan ringkasan kepada pengguna
    summary = (
        f"***Ringkasan Aktivitas***\n\n"
        f"Tipe Aktivitas: {user_data['activity_type']}\n"
        f"Nama Pelanggan: {user_data.get('customer_name', 'N/A')}\n"
        f"ID Proyek: {user_data.get('project_id', 'N/A')}\n"
        f"Tanggal Mulai: {user_data['start_date']} {user_data['start_time']} WIB \n"
        f"Tanggal Berakhir: {user_data['end_date']} {user_data['end_time']} WIB\n"
        f"Catatan: {user_data['notes']}\n"
        f"Kontak Pelanggan: {user_data.get('customer_contact', 'N/A')}\n"
        f"Suara Pelanggan: {user_data.get('customer_feedback', 'N/A')}\n"
        f"Lampiran: {user_data.get('attachment', 'N/A')}\n"
    )

    # Kirim ringkasan aktivitas terlebih dahulu
    bot.send_message(message.chat.id, summary)

    # Buat markup untuk tombol konfirmasi
    markup = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True)
    markup.add("Ya", "Tidak")
    
    # Tampilkan konfirmasi setelah ringkasan
    bot.send_message(message.chat.id, "Apakah Anda ingin menyimpan data ini? (Ya/Tidak)", reply_markup=markup)

    # Daftarkan handler untuk menangani respons selanjutnya
    bot.register_next_step_handler(message, lambda m: process_save_confirmation(m, user_id, username))

# proses konfirmasi penyimpanan catatan aktivitas
def process_save_confirmation(message, user_id, username):
    if message.text.lower() == 'ya':
        save_data_to_json(user_id, username)
    else:
        bot.send_message(user_id, 'Data aktivitas tidak disimpan. Terima kasih telah menggunakan layanan kami.')

# proses simpan data ke json
def save_data_to_json(user_id, username):
    # Pastikan direktori ada
    if not os.path.exists('data'):
        os.makedirs('data')

    # Siapkan data untuk disimpan
    activity_record = {
        'id': str(uuid.uuid4()),
        'user_id': user_id,
        'username': username,
        'activity_type': user_data['activity_type'],
        'customer_name': user_data.get('customer_name', 'N/A'),
        'project_id': user_data.get('project_id', 'N/A'),
        'start_date': user_data['start_date'],
        'start_time': user_data['start_time'],
        'end_date': user_data['end_date'],
        'end_time': user_data['end_time'],
        'notes': user_data['notes'],
        'kontak_pelanggan': user_data.get('customer_contact', 'N/A'),
        'suara_pelanggan': user_data.get('customer_feedback', 'N/A'),
        'attachment': user_data.get('attachment', 'N/A'),
    }

    # Nama file untuk menyimpan data
    filename = 'data/activity_log.json'

    # Coba membaca file JSON yang sudah ada
    if os.path.exists(filename):
        with open(filename, 'r') as json_file:
            try:
                # Membaca data yang ada dan mengubahnya menjadi list
                data = json.load(json_file)
            except json.JSONDecodeError:
                # Jika file kosong atau tidak valid, mulai dengan list kosong
                data = []
    else:
        # Jika file belum ada, mulai dengan list kosong
        data = []

    # Tambahkan activity record baru ke dalam data
    data.append(activity_record)

    # Simpan kembali data ke dalam file JSON
    with open(filename, 'w') as json_file:
        json.dump(data, json_file, indent=4)

    bot.send_message(user_id, 'Data aktivitas telah disimpan\nTerima kasih telah menggunakan layanan kami.')

# fungsi agar bot tetap berjalan secara terus-menerus.
bot.polling(none_stop=True)
