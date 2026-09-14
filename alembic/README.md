Generic single-database configuration.
# After each DB change
```bash
alembic revision --autogenerate -m "Message"
```
# Apply change
```bash
alembic upgrade head
```
