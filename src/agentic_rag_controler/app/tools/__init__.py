from .db import get_db_tools

# TOols for Database
db_tools = get_db_tools()

# list all tools
list_tools = db_tools

TOOLS_BY_NAME = {t.name: t for t in list_tools}
