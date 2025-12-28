#!/usr/bin/env python3
"""
Запускной скрипт микроблог платформы
"""
import subprocess
import sys
import time
import os

def check_docker():
    """Проверяет, запущены ли Docker контейнеры"""
    print("🔍 Проверка Docker контейнеров...")
    
    try:
        result = subprocess.run(
            ["docker", "ps", "--format", "table {{.Names}}\t{{.Status}}"],
            capture_output=True,
            text=True
        )
        
        containers = result.stdout.strip().split('\n')[1:]  # Пропускаем заголовок
        required_containers = ["mongodb", "elasticsearch", "hazelcast", "hazelcast-mancenter"]
        
        running_containers = []
        for container in containers:
            if container:
                name = container.split()[0]
                running_containers.append(name)
        
        missing = [c for c in required_containers if c not in running_containers]
        
        if missing:
            print(f"⚠️  Отсутствуют контейнеры: {missing}")
            print("   Запустите: docker-compose up -d в папке infrastructure/")
            return False
        else:
            print("✅ Все контейнеры запущены")
            return True
    
    except FileNotFoundError:
        print("❌ Docker не установлен или не в PATH")
        return False

def check_python_deps():
    """Проверяет Python зависимости"""
    print("\n🔍 Проверка Python зависимостей...")
    
    try:
        import fastapi
        import pymongo
        import elasticsearch
        import hazelcast
        import pydantic
        
        print("✅ Все зависимости установлены")
        return True
    except ImportError as e:
        print(f"❌ Отсутствует зависимость: {e}")
        print("   Установите: pip install -r requirements.txt")
        return False

def wait_for_services():
    """Ожидает готовности сервисов"""
    print("\n⏳ Ожидание готовности сервисов...")
    
    services = [
        ("MongoDB", "mongodb://localhost:27017"),
        ("Elasticsearch", "http://localhost:9200"),
        ("Hazelcast", "localhost:5701")
    ]
    
    for service_name, url in services:
        print(f"  ⏳ {service_name}...", end="", flush=True)
        
        max_attempts = 10
        for attempt in range(max_attempts):
            try:
                if service_name == "MongoDB":
                    import pymongo
                    client = pymongo.MongoClient(url, serverSelectionTimeoutMS=2000)
                    client.server_info()
                elif service_name == "Elasticsearch":
                    import requests
                    response = requests.get(url, timeout=2)
                    if response.status_code == 200:
                        pass
                elif service_name == "Hazelcast":
                    # Hazelcast проверяется при запуске приложения
                    pass
                
                print(" ✅")
                break
            except Exception:
                if attempt < max_attempts - 1:
                    time.sleep(1)
                else:
                    print(" ❌")
                    print(f"     Не удалось подключиться к {service_name}")
                    return False
    
    return True

def main():
    """Основная функция запуска"""
    print("=" * 60)
    print("🚀 ЗАПУСК МИКРОБЛОГ ПЛАТФОРМЫ")
    print("=" * 60)
    
    # Проверяем Docker
    if not check_docker():
        sys.exit(1)
    
    # Проверяем зависимости Python
    if not check_python_deps():
        sys.exit(1)
    
    # Ждем готовности сервисов
    if not wait_for_services():
        print("⚠️  Некоторые сервисы не готовы, продолжаем...")
    
    # Запускаем приложение
    print("\n🚀 Запуск FastAPI сервера...")
    print("=" * 60)
    
    os.system("uvicorn app.main:app --reload --host 0.0.0.0 --port 8000")

if __name__ == "__main__":
    main()