# создать пустую (начальную) миграцию БД
alembic revision -m "Empty init"
# применить миграцию БД
alembic upgrade head
# добавить миграцию БД
alembic revision --autogenerate -m "Added Doctor model"
# применить миграцию БД
alembic upgrade head
