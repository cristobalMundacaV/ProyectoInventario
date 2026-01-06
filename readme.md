git clone https://github.com/cristobalMundacaV/ProyectoInventario.git
cd ProyectoInventario
python -m venv venv
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver