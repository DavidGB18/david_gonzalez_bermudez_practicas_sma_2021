# SistemasMultiagentes
## Usage
### Initialize BBDD
```
cd PostgresDocker
docker build -t chatbot_postgres_db ./
docker run -d --name chatbot_postgres -p 5432:5432 chatbot_postgres_db
docker start chatbot_postgres
```

### Initialize chatbot
```
cd ..
docker build -t python-image .
docker run -it --rm --name python3 python-image
```
