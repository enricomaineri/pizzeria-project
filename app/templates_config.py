from fastapi.templating import Jinja2Templates

# Istanza condivisa: tutti i moduli API importano da qui
# invece di creare ogni volta Jinja2Templates(directory="app/templates").
templates = Jinja2Templates(directory="app/templates")
