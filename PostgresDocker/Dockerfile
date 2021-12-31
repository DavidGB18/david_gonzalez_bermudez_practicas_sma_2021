FROM postgres
ENV POSTGRES_USER sma
ENV POSTGRES_PASSWORD sma
ENV POSTGRES_DB chatbot_postgres_db
COPY initialize.sql /docker-entrypoint-initdb.d/
RUN chmod -R 775 /docker-entrypoint-initdb.d