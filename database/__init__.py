from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from settings import logger, DB

Session = None
engine = None


def init_db():
    global Session, engine
    if DB["engine"] == "sqlite":
        engine = create_engine('{engine}:{file}'.format(**DB), connect_args={'check_same_thread': False})
    else:
        eng = '{engine}://{username}:{password}@{host}/{database}'.format(**DB)
        engine = create_engine(eng)

    Session = sessionmaker(bind=engine)


init_db()
