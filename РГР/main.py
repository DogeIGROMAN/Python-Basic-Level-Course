#Імпорт функції Main
from license_audit.cli import main

#Якщо запуск відбувається з цього скрипта,то викликається функція main з виводом коду завершення
if __name__ == "__main__":
    raise SystemExit(main())

#Через термінал запускаємо проєкт з сирими даними: python main.py --input data/raw_records.txt