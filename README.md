# SistemasMultiagentes
## Usage
### 1.- Initialize BBDD
```
cd PostgresDocker
docker build -t chatbot_postgres_db ./
docker run -d --name chatbot_postgres -p 5432:5432 chatbot_postgres_db
docker start chatbot_postgres
```

### 2.- Initialize chatbot
```
cd ..
docker build -t python-image .
docker run -it --rm --name python3 python-image
```

### Mount bind
Instead of executing that:
```
docker run -it --rm --name python3 python-image
```
If you want to see created files on your host execute the following command.
```
docker run --mount type=bind,source=<host_directory_path>,target=/SistemasMultiagentes -it --rm --name python3 python-image
```
Example:
```
docker run --mount type=bind,source="C:\Users\david\Documents\Año 4\Cuatrimestre 1\Sistemas multiagentes/david_gonzalez_bermudez_practicas_sma_2021",target=/SistemasMultiagentes -it --rm --name python3 python-image
```