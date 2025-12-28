# Микроблоги (Twitter)






##  Архитектура



Проект представляет собой распределенную платформу микроблогов с использованием NoSQL технологий:



- *\*FastAPI\*\* - REST API сервер (Python)

- *\*MongoDB\*\* - основное хранилище данных

- *\*Elasticsearch\*\* - полнотекстовый поиск

- *\*Hazelcast\*\* - распределенный кэш



## Быстрый запуск



### 1. Запуск инфраструктуры

```bash
Инструкция по запуску:

1. cd microblog-platform/infrastructure
2. docker-compose up -d
3. cd ../backend
4. pip install -r requirements.txt
5. python run.py

