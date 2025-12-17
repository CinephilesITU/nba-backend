# 🌐 NBA Backend - Google Cloud Deployment Config

## 🚀 PRODUCTION URL
**https://nba-backend-391303839683.europe-west1.run.app**

## Proje Bilgileri
- **GCP Project ID:** dark-runway-417405
- **GCP Project Number:** 391303839683
- **Region:** europe-west1

## Cloud SQL (MySQL)
- **Instance Name:** nba-mysql
- **IP Address:** 34.22.203.23
- **Port:** 3306
- **Database:** nba_db
- **User:** root
- **Password:** NbaBackend2024!

## Cloud Run
- **Service Name:** nba-backend
- **Container Image:** gcr.io/dark-runway-417405/nba-backend
- **Port:** 8080

## Bağlantı Bilgileri (app.py için)
```python
MYSQLHOST = "34.22.203.23"
MYSQLPORT = 3306
MYSQLUSER = "root"
MYSQL_ROOT_PASSWORD = "NbaBackend2024!"
MYSQL_DATABASE = "nba_db"
```

## Yararlı Komutlar

### Veritabanına Bağlan
```bash
mysql -h 34.22.203.23 -u root -pNbaBackend2024! nba_db
```

### Verileri Import Et
```bash
mysql -h 34.22.203.23 -u root -pNbaBackend2024! nba_db < init.sql
```

### Container Rebuild
```bash
gcloud builds submit --tag gcr.io/dark-runway-417405/nba-backend
```

### Cloud Run Deploy
```bash
gcloud run deploy nba-backend \
  --image gcr.io/dark-runway-417405/nba-backend \
  --platform managed \
  --region europe-west1 \
  --allow-unauthenticated \
  --set-env-vars "USE_CLOUD_DB=true,MYSQLHOST=34.22.203.23,MYSQLPORT=3306,MYSQLUSER=root,MYSQL_ROOT_PASSWORD=NbaBackend2024!,MYSQL_DATABASE=nba_db"
```
