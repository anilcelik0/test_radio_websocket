- create virtualvenv
- docker-compose up --build
- open new bash
- docker-compose run django python manage.py shell  # open the django shell
- from radio.tasks import *
- run_radio_pipeline.delay()   # start 8001 port.
- listen_to_port.delay()    !!!! before that you must connected the websocket. for this you should go to http://localhost:8000/radio_websocket and click the start stream Button

It should be work

