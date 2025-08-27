# Core-System Installation Guide

## 📋 **فایل‌های کپی شده**

تمام فایل‌های Core-System به مسیر زیر کپی شده‌اند:
```
\\wsl.localhost\Ubuntu\home\ahad\proj\core\
```

## 🗂️ **ساختار کامل فایل‌ها**

```
core/
├── 📄 docker-compose.core.yml     # تنظیمات Docker Compose
├── 📄 .env.example               # نمونه متغیرهای محیط
├── 📄 .gitignore                 # فایل‌های نادیده گرفته شده Git
├── 📄 README.md                  # راهنمای کامل سیستم
├── 📄 Makefile                   # دستورات توسعه
├── 📄 deploy.sh                  # اسکریپت استقرار خودکار
├── 📄 INSTALLATION.md            # راهنمای نصب (این فایل)
├── 📁 config/
│   ├── 📄 policy.yaml           # سیاست‌های سیستم
│   └── 📄 schema.yaml           # تعریف ساختار داده‌ها
├── 📁 scripts/
│   └── 📄 validate_deployment.py # اعتبارسنجی استقرار
└── 📁 api/
    ├── 📄 Dockerfile            # تنظیمات کانتینر
    ├── 📄 requirements.txt      # وابستگی‌های Python
    ├── 📄 prestart.sh           # اسکریپت راه‌اندازی
    ├── 📄 alembic.ini           # تنظیمات Migration
    ├── 📄 healthcheck.py        # بررسی سلامت سیستم
    ├── 📄 pytest.ini            # تنظیمات تست
    ├── 📁 app/
    │   ├── 📄 __init__.py
    │   ├── 📄 main.py           # اپلیکیشن اصلی FastAPI
    │   ├── 📄 deps.py           # وابستگی‌ها و MinIO
    │   ├── 📁 core/
    │   │   ├── 📄 __init__.py
    │   │   └── 📄 settings.py   # تنظیمات سیستم
    │   ├── 📁 db/
    │   │   ├── 📄 __init__.py
    │   │   ├── 📄 base.py       # پایگاه داده
    │   │   ├── 📄 session.py    # جلسات DB
    │   │   └── 📁 migrations/
    │   │       ├── 📄 env.py
    │   │       ├── 📄 script.py.mako
    │   │       └── 📁 versions/
    │   │           └── 📄 0001_initial_migration.py
    │   ├── 📁 models/
    │   │   ├── 📄 __init__.py
    │   │   ├── 📄 official.py   # مدل اسناد قانونی
    │   │   ├── 📄 qa.py         # مدل پرسش و پاسخ
    │   │   ├── 📄 user.py       # مدل کاربر
    │   │   └── 📄 sync.py       # مدل همگام‌سازی
    │   ├── 📁 routers/
    │   │   ├── 📄 __init__.py
    │   │   ├── 📄 health.py     # API سلامت سیستم
    │   │   ├── 📄 stats.py      # API آمار
    │   │   └── 📄 sync.py       # API همگام‌سازی
    │   └── 📁 utils/
    │       ├── 📄 __init__.py
    │       └── 📄 minio_helper.py # کمکی MinIO
    └── 📁 tests/
        ├── 📄 __init__.py
        ├── 📄 test_health.py    # تست سلامت سیستم
        ├── 📄 test_stats.py     # تست آمار
        ├── 📄 test_sync.py      # تست همگام‌سازی
        └── 📄 test_integration.py # تست یکپارچگی
```

## 🚀 **نصب و راه‌اندازی**

### 1. **بررسی فایل‌ها**
```bash
cd /home/ahad/proj/core
ls -la
```

### 2. **ایجاد شبکه Docker**
```bash
docker network create advisor_net
```

### 3. **تنظیم متغیرهای محیط**
```bash
cp .env.example .env
nano .env  # ویرایش تنظیمات
```

### 4. **استقرار خودکار**
```bash
chmod +x deploy.sh
./deploy.sh
```

### 5. **استقرار دستی**
```bash
# ساخت و اجرای سرویس‌ها
docker compose -f docker-compose.core.yml up -d --build

# بررسی وضعیت
docker compose -f docker-compose.core.yml ps
```

## 🔗 **آدرس‌های دسترسی**

پس از راه‌اندازی موفق:

- **🌐 API اصلی**: http://localhost:8000
- **📚 مستندات API**: http://localhost:8000/docs
- **💚 بررسی سلامت**: http://localhost:8000/health
- **📊 آمار سیستم**: http://localhost:8000/stats
- **🗄️ مدیریت پایگاه داده**: http://localhost:8082
- **📦 کنسول MinIO**: http://localhost:9001

## ⚙️ **دستورات مفید**

```bash
# مشاهده لاگ‌ها
docker compose -f docker-compose.core.yml logs -f

# توقف سرویس‌ها
docker compose -f docker-compose.core.yml down

# اجرای تست‌ها
docker exec -it core_api pytest

# دسترسی به پایگاه داده
docker exec -it core_db psql -U postgres -d coredb

# دسترسی به کانتینر API
docker exec -it core_api /bin/bash
```

## 🔧 **عیب‌یابی**

### مشکلات رایج:

1. **Docker در حال اجرا نیست**
   ```bash
   sudo systemctl start docker
   ```

2. **پورت‌ها اشغال هستند**
   ```bash
   sudo netstat -tulpn | grep :8000
   sudo kill -9 <PID>
   ```

3. **مشکل دسترسی به فایل‌ها**
   ```bash
   sudo chown -R $USER:$USER /home/ahad/proj/core
   chmod +x deploy.sh
   ```

## ✅ **تأیید نصب**

برای تأیید نصب موفق:

```bash
# اجرای اسکریپت اعتبارسنجی
python3 scripts/validate_deployment.py

# یا بررسی دستی
curl http://localhost:8000/health
```

## 📞 **پشتیبانی**

در صورت بروز مشکل:
1. بررسی لاگ‌های Docker
2. مطالعه فایل README.md
3. اجرای اسکریپت validate_deployment.py
