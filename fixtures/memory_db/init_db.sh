set -euo pipefail

set -a
source .env
set +a

which python
python setup_db.py