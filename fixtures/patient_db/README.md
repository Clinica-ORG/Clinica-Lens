# External Database
Since the DB creation and CRUD are not in the scope of the project, I simulate an existing database containing existing data (production scenario), to which the application interacts with.
My choice is `Supabase`, a cloud postgres DB with generous free plan.

To initialize, create an env using the `requirements.txt`, modify the `.env` with the DB URL.
The predefined data is set in `data/` in `json` format.

Finally, run the command to init the DB and add data into the tables:
```bash
bash init_db.sh
```

